#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
SNMP passive sensor.
'''
from datetime import datetime
import socket

from whmonit.client.sensors import AdvancedSensorBase


class Sensor(AdvancedSensorBase):
    '''
    SNMP passive sensor.

    Uses pysnmp library to handle TRAP and INFORM messages.
    '''

    name = 'snmp_passive'
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'interface_ip': {
                'type': 'string',
                'default': '0.0.0.0'
            },
            'port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
                'default': 162
            },
            'devices': {
                'type': 'array',
                'items': {'oneOf': [
                    # For SNMPv1 or SNMPv2c.
                    {
                        'type': 'object',
                        'properties': {
                            'version': {
                                'type': 'string',
                                'enum': ['v1', 'v2c']
                            },
                            'index': {
                                'type': 'string',
                                'default': 'my_area',
                                'description': 'community index'
                            },
                            'name': {
                                'type': 'string',
                                'default': 'public',
                                'description': 'community name'
                            }
                        },
                        'required': ['version'],
                        'additionalProperties': False
                    },
                    # For SNMPv3.
                    {
                        'type': 'object',
                        'properties': {
                            'version': {'type': 'string', 'enum': ['v3']},
                            'authentication': {
                                'type': 'string',
                                'enum': ['MD5', 'SHA']
                            },
                            'auth_key': {'type': 'string'},
                            'encryption': {
                                'type': 'string',
                                'enum': [
                                    'DES',
                                    '3DES',
                                    'AES128',
                                    'AES192',
                                    'AES256'
                                ]
                            },
                            'encrypt_key': {'type': 'string'},
                            'device_id': {
                                'type': 'string',
                                'pattern': '^([0-9a-f]+|[0-9A-F]+)$',
                                'description': 'Needed to handle TRAP messages'
                            }
                        },
                        'required': ['version'],
                        'dependencies': {
                            'auth_key': ['authentication'],
                            'authentication': ['auth_key'],
                            'encrypt_key': ['encryption'],
                            'encryption': ['encrypt_key']
                        },
                        'additionalProperties': False
                    }
                ]},
                'minItems': 1,
                'uniqueItems': True
            }
        },
        'required': ['devices'],
        'additionalProperties': False
    }
    streams = {
        'sender': {
            'type': str,
            'description': "Device's address."
        },
        'context_engine_id': {
            'type': str,
            'description': "Device's context engine ID."
        },
        'context_name': {
            'type': str,
            'description': "Device's context name."
        },
        'variable_name': {
            'type': str,
            'description': "Changed variable's name."
        },
        'variable_value': {
            'type': str,
            'description': "New variable's value."
        }
    }

    def do_run(self):
        '''
        Run sensor.
        '''
        # Too many branches.
        # pylint: disable=R0912

        from pysnmp.error import PySnmpError
        from pysnmp.entity import engine, config
        from pysnmp.carrier.asynsock.dgram import udp, udp6
        from pysnmp.entity.rfc3413 import ntfrcv
        from pysnmp.proto.api import v2c

        # Create SNMP engine with autogenernated engineID and pre-bound
        # to socket transport dispatcher.
        snmp_engine = engine.SnmpEngine()

        # Transport setup.
        try:
            socket.inet_pton(socket.AF_INET, self.config['interface_ip'])
            # UDP over IPv4.
            config.addSocketTransport(
                snmp_engine,
                udp.domainName,
                udp.UdpTransport().openServerMode(
                    (self.config['interface_ip'], self.config['port'])
                )
            )
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, self.config['interface_ip'])
                # UDP over IPv6.
                config.addSocketTransport(
                    snmp_engine,
                    udp6.domainName,
                    udp6.Udp6Transport().openServerMode(
                        (self.config['interface_ip'], self.config['port'])
                    )
                )
            except socket.error:
                self.log('given interface_ip is neither IPv4 nor IPv6 address')
                return
        snmpv3_protocols = {
            'MD5': config.usmHMACMD5AuthProtocol,
            'SHA': config.usmHMACSHAAuthProtocol,
            'DES': config.usmDESPrivProtocol,
            '3DES': config.usm3DESEDEPrivProtocol,
            'AES128': config.usmAesCfb128Protocol,
            'AES192': config.usmAesCfb192Protocol,
            'AES256': config.usmAesCfb256Protocol
        }

        def snmpv3_setup_args(version, authentication=None, encryption=None,
                              auth_key=None, encrypt_key=None, device_id=None):
            '''
            Helper function, parses args.
            '''
            # R0913: Too many arguments
            # pylint: disable=R0913
            del version
            del device_id
            args = [snmp_engine, 'usr-{}-{}'.format(
                authentication.lower() if authentication else 'none',
                encryption.lower() if encryption else 'none'
            )]
            if authentication:
                # Expression not assigned
                # pylint: disable=W0106
                args.append(snmpv3_protocols[authentication]),
                args.append(auth_key)
            if encryption:
                # Expression not assigned
                # pylint: disable=W0106
                args.append(snmpv3_protocols[encryption]),
                args.append(encrypt_key)
            return args
        # Setup devices.
        for device in self.config['devices']:
            if device['version'] == 'v3':
                # SNMPv3 setup.
                if 'device_id' in device:
                    config.addV3User(
                        *snmpv3_setup_args(**device),
                        contextEngineId=v2c.OctetString(hexValue=device['device_id'])
                    )
                else:
                    config.addV3User(*snmpv3_setup_args(**device))
            else:
                # SNMPv1/2c setup.
                # SecurityName <-> CommunityName mapping.
                config.addV1System(
                    snmp_engine,
                    device['index'],
                    device['name']
                )

        def cb_fun(snmp_engine, state_reference, context_engine_id,
                   context_name, var_binds, cb_ctx):
            # Too many arguments
            # pylint: disable=R0913
            '''
            Callback function for receiving notifications.
            '''
            _, transport_address = snmp_engine.msgAndPduDsp.getTransportInfo(
                state_reference
            )
            for name, val in var_binds:
                self.send_results(datetime.utcnow(), (
                    ('sender', transport_address),
                    ('context_engine_id', context_engine_id.prettyPrint()),
                    ('context_name', context_name.prettyPrint()),
                    ('variable_name', name.prettyPrint()),
                    ('variable_value', val.prettyPrint())
                ))

        # Register SNMP Application at the SNMP engine.
        ntfrcv.NotificationReceiver(snmp_engine, cb_fun)

        # This job would never finish.
        snmp_engine.transportDispatcher.jobStarted(1)

        # Run I/O dispatcher which would receive queries and send confirmations.
        try:
            snmp_engine.transportDispatcher.runDispatcher()
        except PySnmpError as err:
            snmp_engine.transportDispatcher.closeDispatcher()
            self.send_results(datetime.utcnow(), (('error', err.message),))
            return

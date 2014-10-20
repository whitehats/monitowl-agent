#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Active SNMP sensor.
'''

from timeit import timeit

from whmonit.client.sensors import TaskSensorBase
from whmonit.common.csvline import write


class Sensor(TaskSensorBase):
    '''
    SNMP active class.

    Uses pysnmp library to get states of objects of given OID.
    '''

    name = 'snmp_active'
    streams = {
        'response_time': {
            'type': float,
            'description': 'Time from sending GET command to getting response.'
        },
        'error_message': {
            'type': str,
            'description': 'Error message recieved from device via SNMP.'
        },
        'response': {
            'type': str,
            'description': 'Response to GET in format: csv(OID, response).'
        }
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
                'default': 161
            },
            'device': {'oneOf': [
                {
                    'type': 'object',
                    'properties': {
                        'version': {'type': 'string', 'enum': ['v1', 'v2c']},
                        'index': {
                            'type': 'string',
                            'default': 'my_area',
                            'description': 'Community index'
                        },
                        'name': {
                            'type': 'string',
                            'default': 'public',
                            'description': 'Community name'
                        }
                    },
                    'required': ['version']
                },
                {
                    'type': 'object',
                    'properties': {
                        'version': {'type': 'string', 'enum': ['v3']},
                        'username': {'type': 'string'},
                        'authkey': {'type': 'string'},
                        'privkey': {'type': 'string'},
                    },
                    'required': ['version', 'username', 'authkey', 'privkey']
                }
            ]},
            'OIDs': {
                'type': 'array',
                'items': {'oneOf': [
                    {'type': 'string', 'pattern': '^[0-9]+(\\.[0-9]+)*$'},
                    {'type': 'array', 'items': [
                        {'type': 'string', 'description': 'MIB name'},
                        {'type': 'string', 'description': 'MIB symbol'},
                        {'type': 'integer', 'description': 'Instance id'}
                    ]}
                ]},
                'minItems': 1,
                'uniqueItems': True
            }
        },
        'required': ['host', 'device', 'OIDs'],
        'additionalProperties': False
    }

    def do_run(self):
        '''Returns GET respons from SNMP device'''
        # R0914 Too many local variables
        # pylint: disable=R0914

        from pysnmp.entity.rfc3413.oneliner import cmdgen
        from pysnmp.smi.error import SmiError

        device = self.config['device']
        if device['version'] == 'v1':
            args = [device[key] for key in ['index', 'name']].append(0)
            data = cmdgen.CommunityData(*args)
        elif device['version'] == 'v2c':
            args = [device[key] for key in ['index', 'name']]
            data = cmdgen.CommunityData(*args)
        else:
            args = [device[key] for key in ['username', 'authkey', 'privkey']]
            data = cmdgen.UsmUserData(*args)
        try:
            cmd_gen = cmdgen.CommandGenerator()
            ret_vals = {}

            def send_get_request():
                ''' cmd_gen.getCmd wrapper for timeit usage '''
                ret_vals['getCmd'] = cmd_gen.getCmd(
                    data,
                    cmdgen.UdpTransportTarget(
                        (self.config['host'], self.config['port'])
                    ),
                    *[
                        x if x.__class__ is str else ((x[0], x[1]), x[2])
                        for x in self.config['OIDs']
                    ]
                )
            time_elapsed = timeit(send_get_request, number=1)
            err_indication, err_status, err_index, var_binds = ret_vals['getCmd']
            if err_indication:
                return (
                    ('response_time', time_elapsed),
                    (
                        'error_message', 'engine-level error: {}'.format(
                            err_indication
                        )
                    )
                )
            else:
                if err_status:
                    return (
                        ('response_time', time_elapsed),
                        ('error_message', 'PDU-level error: {} at {}'.format(
                            err_status.prettyPrint(),
                            err_index and var_binds[int(err_index) - 1] or '?'
                        ))
                    )
                else:
                    return (
                        [
                            ('response', write([name.prettyPrint(), val.prettyPrint()]))
                            for name, val in var_binds
                        ]
                        +
                        [('response_time', time_elapsed)]
                    )
        except SmiError as err:
            self.log('Invalid MIB name or symbol. {}'.format(err))

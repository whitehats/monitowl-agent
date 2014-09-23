#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check port sensor.
'''
import socket

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''
    Check port sensor class.

    Note that returned error codes and/or messages might be platform dependent.
    '''

    name = 'check_port'
    streams = {
        'is_open': bool,
        'error_code': float,
        'error_text': str,
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'hostname': {'type': 'string'},
            'port': {'type': 'integer', 'minimum': 1, 'maximum': 65535},
            'protocol': {'type': 'string', 'enum': ['tcp', 'udp']}
        },
        'required': ['hostname', 'port', 'protocol'],
        'additionalProperties': False
    }

    types = {
        'tcp': socket.SOCK_STREAM,
        'udp': socket.SOCK_DGRAM,
    }

    def do_run(self):
        '''
        Returns whether given hostname:port is open.
        Additionally, it fills the 'error' streams with details on failure.
        '''
        typ = Sensor.types.get(self.config['protocol'])
        sock = socket.socket(socket.AF_INET, typ)

        try:
            sock.connect((self.config['hostname'], self.config['port']))
            sock.shutdown(socket.SHUT_RDWR)
            return (('is_open', True),)
        except socket.error as err:
            return (
                ('is_open', False),
                ('error_code', float(err.errno)),
                ('error_text', err.strerror),
            )

#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check port sensor.
'''
import socket
from voluptuous import Required, Range, All, Lower, Any

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """
    Check port sensor class.

    Note that returned error codes and/or messages might be platform dependent.
    """

    name = 'check_port'
    streams = {
        'is_open': bool,
        'error_code': float,
        'error_text': str,
    }
    config_schema = {
        Required('hostname'): basestring,
        Required('port'): All(int, Range(1, 65535)),
        Required('protocol'): All(Lower, Any('tcp', 'udp')),
    }

    types = {
        'tcp': socket.SOCK_STREAM,
        'udp': socket.SOCK_DGRAM,
    }

    def do_run(self):
        """
        Returns whether given hostname:port is open.
        Additionally, it fills the 'error' streams with details on failure.
        """
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

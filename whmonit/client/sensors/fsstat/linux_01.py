#!/usr/bin/env python
# -*- coding: utf-8 -*-
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''netstat sensor class.'''
    # W0232: Class has no __init__ method
    # R0201: Method could be a function
    # R0903: Too few public methods
    # pylint: disable=W0232,R0201,R0903

    name = 'fsstat'
    streams = {
        'total': float,
        'used': float,
        'free': float,
        'percent': float,
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {'mountpoint': {'type': 'string'}},
        'required': ['mountpoint'],
        'additionalProperties': False
    }

    def do_run(self):
        '''Executes itself.'''
        import psutil

        data = psutil.disk_usage(self.config['mountpoint'])

        return (('total', float(data.total)),
                ('used', float(data.used)),
                ('free', float(data.free)),
                ('percent', float(data.percent)))


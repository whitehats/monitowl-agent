#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
network ping sensor.
'''

from ping import do_one as ping

from whmonit.client.sensors import TaskSensorBase
from whmonit.common.units import unit_reg


class Sensor(TaskSensorBase):
    '''Generic 'ping' sensor.'''
    # W0232: Class has no __init__ method
    # R0201: Method could be a function
    # R0903: Too few public methods
    # pylint: disable=W0232,R0201,R0903

    name = 'ping'
    streams = {
        'default': {
            'type': float,
            'description':
                'Time from sending message to destination host '
                'to receiving acknowledgment.',
            'unit': str(unit_reg.millisec)
        }
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {'host': {'type': 'string'}},
        'required': ['host'],
        'additionalProperties': False
    }

    def do_run(self):
        '''Returns time to ping a host.'''

        try:
            delay = float(ping(self.config['host'], 5))
        except:  # TODO: should be time TimeOut and some other errors
            return ()

        return (("default", delay), )

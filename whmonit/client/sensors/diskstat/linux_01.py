#!/usr/bin/env python
# -*- coding: utf-8 -*-
from whmonit.client.sensors import TaskSensorBase
from whmonit.common.units import unit_reg


class Sensor(TaskSensorBase):
    '''netstat sensor class.'''
    # W0232: Class has no __init__ method
    # R0201: Method could be a function
    # R0903: Too few public methods
    # pylint: disable=W0232,R0201,R0903

    name = 'diskstat'
    streams = {
        'read_bytes': {
            'type': float,
            'description': 'Number of bytes read.',
            'unit': str(unit_reg.byte)
        },
        'write_bytes': {
            'type': float,
            'description': 'Number of bytes written.',
            'unit': str(unit_reg.byte)
        },
        'read_count': {
            'type': float,
            'description': 'Number of reads.'
        },
        'write_count': {
            'type': float,
            'description': 'Number of writes.'
        },
        'read_time': {
            'type': float,
            'description': 'Time spent reading from disk (in milliseconds).',
            'unit': str(unit_reg.millisec)
        },
        'write_time': {
            'type': float,
            'description': 'Time spent writing to disk (in milliseconds).',
            'unit': str(unit_reg.millisec)
        }
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {'device': {'type': 'string'}},
        'additionalProperties': False
    }

    def do_run(self):
        '''Executes itself.'''
        import psutil

        # if there is no device provided, count all data
        if 'device' in self.config:
            data = psutil.disk_io_counters(perdisk=True)[self.config['device']]
        else:
            data = psutil.disk_io_counters()

        return (('read_bytes', float(data.read_bytes)),
                ('write_bytes', float(data.write_bytes)),
                ('read_count', float(data.read_count)),
                ('write_count', float(data.write_count)),
                ('read_time', float(data.read_time)),
                ('write_time', float(data.write_time)))


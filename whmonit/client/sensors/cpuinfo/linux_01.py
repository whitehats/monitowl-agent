#!/usr/bin/env python
'''Cpuinfo sensor.'''
import platform
import psutil

from whmonit.client.sensors.base import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Read processor information from /proc/cpuinfo.'''
    name = 'cpuinfo'
    streams = {
        'name': {
            'type': str,
            'description': 'Processor name.'
        },
        'cpu_count': {
            'type': float,
            'description': 'Number of CPUs.'
        },
        'cpu_percent': {
            'type': float,
            'description': 'Percent of CPU usage.',
        },
        'cpu_times': {
            'type': float,
            'description': 'CPU times.'
        }
    }

    def do_run(self):
        '''Returns 'cpuinfo' contents as a string.'''
        return (
            ('name', str(platform.processor())),
            ('cpu_count', float(psutil.cpu_count())),
            ('cpu_percent', float(psutil.cpu_percent())),
            ('cpu_times', float(psutil.cpu_times()))
        )

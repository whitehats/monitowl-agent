#!/usr/bin/env python
'''Cpuinfo sensor.'''
import platform
import psutil
from whmonit.client.sensors.base import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Read processor information from /proc/cpuinfo.'''
    name = 'cpuinfo'
    streams = {
        'name': str,
        'cpu_count': float,
        'cpu_percent': float,
        'cpu_times': float
    }

    def do_run(self):
        '''Returns 'cpuinfo' contents as a string.'''
        return (
            ('name', str(platform.processor())),
            ('cpu_count', float(psutil.cpu_count())),
            ('cpu_percent', float(psutil.cpu_percent())),
            ('cpu_times', float(psutil.cpu_times()))
        )

#!/usr/bin/env python
'''Cpuinfo sensor.'''
from whmonit.client.sensors.base import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Read processor information from /proc/cpuinfo.'''
    name = 'cpuinfo'
    streams = {'default': str}

    def do_run(self):
        '''Returns 'cpuinfo' contents as a string.'''
        with open('/proc/cpuinfo') as f_input:
            output = f_input.read()
        return (('default', output),)

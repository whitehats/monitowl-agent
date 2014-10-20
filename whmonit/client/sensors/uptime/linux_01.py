#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Uptime sensor.
'''
import psutil
import time

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Generic 'uptime' sensor.'''
    # W0232: Class has no __init__ method
    # R0201: Method could be a function
    # R0903: Too few public methods
    # pylint: disable=W0232,R0201,R0903

    name = 'uptime'
    streams = {
        'default': {
            'type': float,
            'description': 'System uptime.'
        }
    }

    def do_run(self):
        '''Returns system uptime.'''
        contents = time.time() - psutil.boot_time()
        return (("default", float(contents)),)

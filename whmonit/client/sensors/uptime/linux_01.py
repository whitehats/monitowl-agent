#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Uptime sensor.
'''
import time

from whmonit.client.sensors import TaskSensorBase
from whmonit.common.units import unit_reg


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
            'description': 'System uptime.',
            'unit': str(unit_reg.second),
        }
    }

    def do_run(self):
        '''Returns system uptime.'''
        import psutil

        contents = time.time() - psutil.boot_time()
        return (("default", float(contents)),)

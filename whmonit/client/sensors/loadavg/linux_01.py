#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
system load sensor.
'''
import os
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Generic system load sensor.'''
    # W0232: Class has no __init__ method
    # R0201: Method could be a function
    # R0903: Too few public methods
    # pylint: disable=W0232,R0201,R0903

    name = 'loadavg'
    streams = {'default': float}

    def do_run(self):
        return (("default", float(os.getloadavg()[0])),)

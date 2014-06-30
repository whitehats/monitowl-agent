#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Logread sensor.
'''
import subprocess
from nanotime import nanotime
from voluptuous import Required

from .. import AdvancedSensorBase


class Sensor(AdvancedSensorBase):
    """
    Long-running logread sensor.
    """
    # W0232: Class has no __init__ method
    # E1101: Instance of 'Sensor' has no 'config'/'send_results' member
    # R0903: Too few public methods
    # pylint: disable=W0232,E1101,R0903

    name = 'logread'
    config_schema = {Required('filename'): basestring}
    streams = {'default': str}

    def do_run(self):
        """
        Run sensor.
        """

        #TODO: save the current position and when sensor has been restarted rewind the file to the old position
        f = subprocess.Popen(['tail', '-F', self.config['filename']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            self.send_results(nanotime.now().datetime(), (("default", f.stdout.readline()),))

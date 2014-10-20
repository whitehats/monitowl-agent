#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Logread sensor.
'''
import subprocess
from nanotime import nanotime

from whmonit.client.sensors.base import AdvancedSensorBase


class Sensor(AdvancedSensorBase):
    '''
    Long-running logread sensor.
    '''

    name = 'logread'
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {'filename': {'type': 'string'}},
        'required': ['filename'],
        'additionalProperties': False
    }
    streams = {
        'default': {
            'type': str,
            'description': 'Logs from the file.'
        }
    }

    def do_run(self):
        '''
        Run sensor.
        '''
        self.storage['line_no'] = self.storage.get('line_no') or 0
        filename = self.config['filename']
        f = subprocess.Popen(
            ('tail', '-F', '-n', '+{}'.format(self.storage['line_no']), filename),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        while True:
            self.send_results(
                nanotime.now().datetime(), (("default", f.stdout.readline()),)
            )
            self.storage['line_no'] += 1

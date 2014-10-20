#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Processes sensor.
'''
import os
from whmonit.client.sensors import TaskSensorBase

#http://linux.die.net/man/5/proc


class Sensor(TaskSensorBase):
    '''Generic class for processes sensor.'''
    # W0232: Class has no __init__ method
    # E1101: Instance of 'Sensor' has no 'log' member
    # R0903: Too few public methods
    # pylint: disable=W0232,E1101,R0903

    name = 'processes'
    streams = {
        'default': {
            'type': str,
            'description': 'List of running processes.'
        }
    }
    fields = ('pid', 'comm', 'state', 'ppid', 'pgrp', 'session', 'tty_nr',
              'tpgid', 'flags', 'minflt', 'cminflt', 'majflt', 'cmajflt',
              'utime', 'stime', 'cutime', 'cstime', 'priority', 'nice',
              'num_threads', 'itrealvalue', 'starttime', 'vsize', 'rss',
              'rsslim', 'startcode', 'endcode', 'startstack', 'kstkesp',
              'kstkeip', 'signal', 'blacked', 'sigignore', 'sigcatch',
              'wchan', 'nswap', 'cnswap', 'exit_signal', 'processor',
              'rt_priority', 'policy', 'delayacct_blkio_ticks', 'guest_time',
              'cguest_time')

    def do_run(self):
        '''Return list of running processes.'''
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        output = ';'.join(self.fields)
        output += '\n'

        for pid in pids:
            try:
                with open(os.path.join('/proc', pid, 'stat'), 'rb') as pidf:
                    vals = pidf.read().split()
                    output += ';'.join(vals)
                    output += '\n'
            except IOError:
                self.log("Cannot open stat file: /proc/%s/stat" % pid)

        return (("default", output),)

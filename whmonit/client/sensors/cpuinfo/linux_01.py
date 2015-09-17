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
        'time_user': {
            'type': float,
            'description': 'CPU Time User.'
        },
        'time_nice': {
            'type': float,
            'description': 'CPU Time Nice.'
        },
        'time_system': {
            'type': float,
            'description': 'CPU Time System.'
        },
        'time_idle': {
            'type': float,
            'description': 'CPU Time IDLE.'
        },
        'time_iowait': {
            'type': float,
            'description': 'CPU Time IO wait.'
        },
        'time_irq': {
            'type': float,
            'description': 'CPU Time IRQ.'
        },
        'time_softirq': {
            'type': float,
            'description': 'CPU Time Soft IRQ.'
        },
        'time_steal': {
            'type': float,
            'description': 'CPU Time Steal.'
        },
        'time_guest': {
            'type': float,
            'description': 'CPU Time Guest.'
        },
        'time_guest_nice': {
            'type': float,
            'description': 'CPU Time Guest Nice.'
        },
    }

    def do_run(self):
        '''Returns 'cpuinfo' contents as a string.'''
        times = psutil.cpu_times()
        return (
            ('name', str(platform.processor())),
            ('cpu_count', float(psutil.cpu_count())),
            ('cpu_percent', float(psutil.cpu_percent())),
            ('time_user', float(times.user)),
            ('time_nice', float(times.nice)),
            ('time_system', float(times.system)),
            ('time_idle', float(times.idle)),
            ('time_iowait', float(times.iowait)),
            ('time_irq', float(times.irq)),
            ('time_softirq', float(times.softirq)),
            ('time_steal', float(times.steal)),
            ('time_guest', float(times.guest)),
            ('time_guest_nice', float(times.guest_nice)),
        )

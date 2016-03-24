#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Processor and memory usage sensor.
'''

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Cpu and memory sensor class.'''

    name = 'sysstat'
    streams = {
        'proc_avg': {
            'type': float,
            'description': 'Processors usage percentage.',
            'unit': '%'
        },
        'vmem_perc': {
            'type': float,
            'description': 'Virtual memory usage percentage.',
            'unit': '%'
        },
        'smem_perc': {
            'type': float,
            'description': 'Swap memory usage percentage.',
            'unit': '%'
        }
    }

    def do_run(self):
        '''Executes itself.'''

        import psutil

        # Count processor usage in percent for each core and count average.
        cpu_perc_avg = 0
        cpu_perc = psutil.cpu_percent(interval=1, percpu=True)
        for core in range(psutil.cpu_count()):
            cpu_perc_avg += cpu_perc[core]
        cpu_perc_avg = cpu_perc_avg / psutil.cpu_count()

        # Virtual memory and Swap memory.
        vmem_perc = psutil.virtual_memory()[2]
        smem_perc = psutil.swap_memory()[3]

        return (('proc_avg', float(cpu_perc_avg)),
                ('vmem_perc', float(vmem_perc)),
                ('smem_perc', float(smem_perc)))

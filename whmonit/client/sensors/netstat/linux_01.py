#!/usr/bin/env python
# -*- coding: utf-8 -*-
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''netstat sensor class.'''
    # W0232: Class has no __init__ method
    # R0201: Method could be a function
    # R0903: Too few public methods
    # pylint: disable=W0232,R0201,R0903

    name = 'netstat'
    streams = {
        'bytes_sent': {
            'type': float,
            'description': 'Number of bytes sent.'
        },
        'bytes_recv': {
            'type': float,
            'description': 'Number of bytes received.'
        },
        'dropin': {
            'type': float,
            'description': 'Total number of incoming packets.'
        },
        'dropout': {
            'type': float,
            'description': 'Total number of outgoing packets.'
        },
        'packets_recv': {
            'type': float,
            'description': 'Number of packets received.'
        },
        'packets_sent': {
            'type': float,
            'description': 'Number of packets sent.'
        },
        'errin': {
            'type': float,
            'description': 'Total number of errors while receiving.'
        },
        'errout': {
            'type': float,
            'description': 'Total number of errors while sending.'
        }
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {'interface': {'type': 'string'}},
        'additionalProperties': False
    }

    def do_run(self):
        '''Executes itself.'''
        import psutil

        # if there is no interface provided, count all data
        if 'interface' in self.config:
            data = psutil.net_io_counters(pernic=True)[self.config['interface']]
        else:
            data = psutil.net_io_counters()

        return (('bytes_sent', float(data.bytes_sent)),
                ('bytes_recv', float(data.bytes_recv)),
                ('dropin', float(data.dropin)),
                ('dropout', float(data.dropout)),
                ('packets_recv', float(data.packets_recv)),
                ('packets_sent', float(data.packets_sent)),
                ('errin', float(data.errin)),
                ('errout', float(data.errout)))


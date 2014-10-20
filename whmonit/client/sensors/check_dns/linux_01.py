#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check DNS sensor.
'''
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''
    Check DNS sensor class.

    Use dns library to get response from dns service.
    '''
    name = 'check_dns'
    streams = {
        'name': {
            'type': str,
            'description': 'DNS name.'
        },
        'answer': {
            'type': str,
            'description': 'Answer from dns service.'
        }
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'DNS query'
            },
            'record_type': {
                'type': 'string',
                'description': 'DNS record type'
            },
            'timeout': {
                'type': 'number',
                'minimum': 0.5,
                'default': 0.5,
                'description': 'query execution timeout'
            }
        },
        'required': ['query', 'record_type'],
        'additionalProperties': False
    }

    def do_run(self):
        '''
        Return answer from dns service, or information that query is invalid.
        If record type is invalid raise SensorBaseError.
        '''
        from dns import resolver, exception

        sensor_resolver = resolver.Resolver()
        sensor_resolver.lifetime = self.config['timeout']

        try:
            answer = sensor_resolver.query(
                qname=self.config['query'],
                rdtype=self.config['record_type']
            )
        except exception.DNSException as ex:
            return (
                ('name', self.config['query']),
                ('error', str(ex))
            )
        return (
            ('name', str(answer.name)),
            ('answer', str(answer.rrset))
        )

#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check HTTP sensor.
'''
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''
    Check HTTP sensor class.

    Uses requests library to get response from given address.
    Arguments 'protocol', 'address' and 'port' are used to form a 'url'.
    All other arguments have the same meaning as described on
    http://docs.python-requests.org/en/latest/api/#requests.request.
    '''

    name = 'check_http'
    streams = {
        'status_code': {
            'type': float,
            'description': 'Status code of the HTTP connection.'
        },
        'status_text': {
            'type': str,
            'description': 'Status text.'
        },
        'response_time': {
            'type': float,
            'description': 'Response time.'
        }
    }

    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'address': {'type': 'string'},
            'protocol': {
                'type': 'string',
                'enum': ['http', 'https'],
                'default': 'http'
            },
            'method': {
                'type': 'string',
                'enum': ['get', 'post', 'patch', 'head', 'put', 'delete'],
                'default': 'get'
            },
            'port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
                'default': 80
            },
            'path': {'type': 'string', 'default': ''},
            'timeout': {
                'type': 'number',
                'minimum': 0,
            }
        },
        'required': ['address'],
        'additionalProperties': False
    }

    def do_run(self):
        '''Returns info about a given HTTP service.'''
        import requests
        from furl import furl

        url = furl().set(
            scheme=self.config['protocol'],
            host=self.config['address'],
            port=self.config['port'],
            path=self.config['path'],
        )
        method = self.config['method']

        # Optional arguments for requests.request. The `requests.request` API
        # interprets `None` as "use default value".
        args = {
            'timeout': self.config.get('timeout', None),
        }

        try:
            req = requests.request(method, url.url, **args)
            return (
                ('status_code', float(req.status_code)),
                ('status_text', req.reason),
                ('response_time', req.elapsed.total_seconds()),
            )
        except requests.exceptions.ConnectionError as err:
            return (
                ('status_code', float(err.args[0].reason.errno)),
                ('status_text', err.args[0].reason.strerror),
            )
        except requests.exceptions.Timeout as err:
            return (('status_text', 'Request timed out.'),)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check HTTP sensor.
'''
from voluptuous import Required, Optional, Any, All, Lower, Range
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """
    Check HTTP sensor class.

    Uses requests library to get response from given address.
    Arguments 'protocol', 'address' and 'port' are used to form a 'url'.
    All other arguments have the same meaning as described on
    http://docs.python-requests.org/en/latest/api/#requests.request.
    """

    name = 'check_http'
    streams = {
        'status_code': float,
        'status_text': str,
        'response_time': float,
    }
    config_schema = {
        Required('address'): basestring,
        Optional('protocol'): All(Lower, Any('http', 'https')),
        Optional('method'): All(Lower, Any(
            'get', 'post', 'patch', 'head', 'put', 'delete',
        )),
        Optional('port'): All(int, Range(1, 65535)),
        Optional('path'): basestring,
        Optional('headers'): dict,
        Optional('cookies'): dict,
        Optional('verify'): bool,
        Optional('auth'): tuple,
        Optional('cert'): tuple,
        Optional('timeout'): Range(min=0.),
    }

    def do_run(self):
        """Returns info about a given HTTP service."""
        import requests
        from furl import furl

        config = {
            'protocol': 'http',
            'method': 'get',
            'port': 80,
            'path': '',
            'timeout': None,
            'headers': None,
            'cookies': None,
            'verify': None,
            'auth': None,
            'cert': None,
        }
        config.update(self.config)

        url = furl().set(
            scheme=config['protocol'],
            host=config['address'],
            port=config['port'],
            path=config['path'],
        )
        method = config['method']
        args = dict(
            (key, config[key]) for key in
            ['headers', 'cookies', 'verify', 'auth', 'cert', 'timeout']
        )
        try:
            req = requests.request(method, url, **args)
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

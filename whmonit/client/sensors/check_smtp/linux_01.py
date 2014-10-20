#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check SMTP sensor.
'''
import smtplib
import socket
from timeit import timeit

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """
    Check SMTP sensor class.

    Uses smtplib library to establish connection to given SMTP server.
    """

    name = 'check_smtp'
    streams = {
        'could_connect': {
            'type': bool,
            'description': 'Could sensor connect to given smtp server.'
        },
        'could_login': {
            'type': bool,
            'description': 'Could sensor login with given login, password.'
        },
        'response_time': {
            'type': float,
            'description': 'Response time for HELO command to given smtp server.'
        }
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'port': {
                'type': 'number',
                'multipleOf': 1.,
                'minimum': 1,
                'maximum': 65535
            },
            'local_hostname': {
                'type': 'string',
                'description': 'FQDN of the local host in the HELO command'
            },
            'timeout': {
                'type': 'number',
                'minimum': 0,
                'default': 10,
                'description': 'Connection timeout (in seconds)'
            },
            'encryption': {
                'type': 'string',
                'enum': ['ssl', 'tls', 'none'],
                'default': 'none'
            },
            'login': {'type': 'string'},
            'password': {'type': 'string'},
            'key': {
                'type': 'string',
                'description': 'PEM formated private key'
            },
            'cert': {
                'type': 'string',
                'description': 'PEM formatted certificate chain'
            }
        },
        'dependencies': {
            'login': ['password'],
            'password': ['login'],
            'key': ['cert'],
            'cert': ['key']
        },
        'required': ['host'],
        'additionalProperties': False
    }

    def do_run(self):
        '''Returns whether it can connect to SMTP server.'''
        # R0912 Too many branches
        # pylint: disable=R0912

        could_connect = False
        could_login = False
        time_elapsed = 0
        if self.config['encryption'] != 'ssl' and 'port' not in self.config:
            self.config['port'] = 587
        smtp_args = {
            key: self.config[key]
            for key in ['host', 'port', 'local_hostname', 'timeout']
            if key in self.config
        }
        try:
            if self.config['encryption'] == 'ssl':
                smtp = smtplib.SMTP_SSL(**smtp_args)
            else:
                smtp = smtplib.SMTP(**smtp_args)
            if self.config['encryption'] == 'tls':
                if 'key' in self.config:
                    smtp.starttls(self.config['key'], self.config['cert'])
                else:
                    smtp.starttls()
            time_elapsed = timeit(smtp.helo, number=1)
            could_connect = True
            if 'login' in self.config:
                smtp.login(self.config['login'], self.config['password'])
                could_login = True
        except smtplib.SMTPConnectError:
            self.log(
                'Could not connect to `{}` on `{}`.'
                .format(self.config['host'], self.config['port'])
            )
        except socket.timeout:
            self.log(
                'Connection timed out after {}s'
                .format(self.config.get('timeout') or socket.getdefaulttimeout())
            )
        except smtplib.SMTPHeloError:
            self.log('The server didn’t reply properly to the HELO greeting.')
        except smtplib.SMTPAuthenticationError:
            self.log(
                'The server didn’t accept the username/password combination.'
            )
        except smtplib.SMTPException:
            self.log(
                'The server does not support the STARTTLS extension'
                'or no suitable authentication method was found.'
            )
        except RuntimeError:
            self.log(
                'SSL/TLS support is not available to your Python interpreter.'
            )
            raise
        finally:
            smtp.quit()

        return (
            ('could_connect', could_connect),
            ('could_login', could_login),
            ('response_time', time_elapsed)
        )

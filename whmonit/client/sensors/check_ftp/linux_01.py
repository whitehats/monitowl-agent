#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check ftp sensor.
'''
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''
    Check ftp sensor class.
    '''

    name = 'check_ftp'
    streams = {
        'status_text': {
            'type': str,
            'description': 'FTP connection status text.'
        },
        'connection_success': {
            'type': bool,
            'description': 'True if connection was successful, False otherwise.'
        }
    }

    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'user': {'type': 'string'},
            'password': {'type': 'string'}
        },
        'required': ['host', 'user', 'password'],
        'additionalProperties': False
    }

    def do_run(self):
        '''Returns connection status to ftp host'''
        import ftplib

        try:
            ftp = ftplib.FTP(host=self.config['host'])
        except ftplib.all_errors:
            return (
                ('status_text', 'connection failed'),
                ('connection_success', False)
            )
        try:
            ftp.login(user=self.config['user'], passwd=self.config['password'])
        except ftplib.all_errors:
            return (
                ('status_text', 'login failed'),
                ('connection_success', False)
            )
        finally:
            ftp.quit()
        return (
            ('status_text', 'connection success'),
            ('connection_success', True)
        )

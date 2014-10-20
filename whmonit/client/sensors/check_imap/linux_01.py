#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check IMAP sensor.
'''
import re
from timeit import timeit
from imaplib import IMAP4_SSL, IMAP4

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''Sensor class checking for IMAP connection.'''
    name = 'check_imap'
    streams = {
        'all_quota': {
            'type': float,
            'description': 'Disk space limit (quota).'
        },
        'used_quota': {
            'type': float,
            'description': 'Used disk space.'
        },
        'unseen_msg_count': {
            'type': float,
            'description': 'Number of unseen messages in INBOX.'
        },
        'msg_count': {
            'type': float,
            'description': 'Number of all messages in INBOX.'
        },
        'connect_time': {
            'type': float,
            'description': 'Time to connect and to get data from imap server.'
        },
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'host': {'type': 'string'},
            'port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
            },
            'key': {'type': 'string'},
            'cert': {'type': 'string'},
            'timeout': {
                'type': 'integer',
                'default': 60
            },
        },
        'required': ['username', 'password', 'host'],
        'dependencies': {
            'key': ['cert'],
            'cert': ['key']
        },
        'additionalProperties': False
    }

    pattern = re.compile(r'\d+')

    def do_run(self):
        '''
        Connects to IMAP server to specified host, with given username and password.
        '''
        from interruptingcow import timeout
        args = {
            key: self.config[key] for key in
            ['host', 'port', 'key', 'cert']
            if key in self.config
        }

        try:
            values = {}

            def func_to_time():
                '''
                Function to executed with timeit.
                '''
                with timeout(self.config['timeout']):
                    conn = IMAP4_SSL(**args)

                conn.login(
                    self.config['username'],
                    self.config['password']
                )

                values['all_msg_count'] = conn.select('inbox')[1][0]
                values['unseen_msg_count'] = Sensor.pattern.search(
                    conn.status('inbox', "(UNSEEN)")[1][0]).group()

                quota_str = conn.getquotaroot('inbox')
                # get quota or return unknow
                values['quota'] = Sensor.pattern.findall(str(quota_str)) or [0, 0]

                conn.logout()

            time = timeit(func_to_time, number=1)
            return (
                ('all_quota', float(values['quota'][0])),
                ('used_quota', float(values['quota'][1])),
                ('unseen_msg_count', float(values['unseen_msg_count'])),
                ('msg_count', float(values['all_msg_count'])),
                ('connect_time', time)
            )
        except IMAP4.error as err:
            self.log('IMAP error: {}'.format(str(err)))
        except RuntimeError as err:
            self.log('Request timeout ({}s).'.format(self.config['timeout']))
        except Exception as err:
            self.log('Error occured: {}'.format(str(err)))

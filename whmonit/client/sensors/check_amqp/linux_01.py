#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Sensor that connects to amqp server and checks queue.
'''
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """
    Sensor class that checks queue in amqp server using pika lib.
    """
    name = 'check_amqp'
    streams = {
        'queue_depth': float,
    }
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'port': {
                'type': 'integer',
                'default': 5672,
            },
            'vhost': {
                'type': 'string',
                'default': '/'
            },
            'user': {'type': 'string'},
            'password': {'type': 'string'},
            'queue_name': {'type': 'string'},
        },
        'required': ['host', 'user', 'password', 'queue_name'],
        'additionalProperties': False
    }

    def do_run(self):
        '''
        Connects to AMQP server and gets number of messages from given queue.
        '''
        import pika
        credentials = pika.credentials.PlainCredentials(
            self.config['user'],
            self.config['password']
        )
        params = pika.ConnectionParameters(
            host=self.config['host'],
            port=self.config['port'],
            virtual_host=self.config['vhost'],
            credentials=credentials,
        )

        try:
            conn = pika.BlockingConnection(parameters=params)
            channel = conn.channel()
            queue = channel.queue_declare(queue=self.config['queue_name'], passive=True)
            queue_depth = queue.method.message_count

            return (('queue_depth', float(queue_depth)),)
        except pika.exceptions.ProbableAuthenticationError as paerr:
            self.log(
                '{}: Incorrect user or password'.format(str(paerr))
            )
        except pika.exceptions.AMQPConnectionError as cerr:
            self.log(
                '{}: Unable to connect with {}'
                .format(str(cerr), self.config['host'])
            )
        except pika.exceptions.ChannelClosed as ccerr:
            self.log(
                '{}: Queue {} does not exist in vhost {}'
                .format(str(ccerr), self.config['queue_name'], self.config['vhost'])
            )


#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check connection with SQL database.
'''
import timeit

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''
    Check SQL sensor class.

    Sent results:
    * result: the rows returned by executing query separated by commas
    * timeit: time it took to execute query (it includes time spent on
              sending and receiving data from the server)

    As for returned error messages: there is a great number of SQL errors
    and they're never precise. What's more, different drivers may raise
    different errors in the same situations.
    Also, be careful using sqlite as for example connecting to non-existent
    database creates the file instead of causing error.

    This sensor returns either error while connecting (including timeout) or
    executing query.
    The errors generally might be:
    * DBAPI errors as returned by the database - they come in form
      (Type)message, OperationalError seems to be most common, for full list
      see http://legacy.python.org/dev/peps/pep-0249/#exceptions
    * StatementError - any kind of wrong statement (including DBAPI errors)
    * several others included in SQLAlchemyError like CompileError,
      ArgumentError, ResourceClosedError

    Drivers used: psycopg2, mysql-python, cx_oracle, pyodbc (mssql)

    Those drivers will usually require client to be installed on the machine in
    order to install them (oracle is non-free, mysql requires package
    libmysqlclient-dev). Message about lack of driver is sent through
    error stream.
    '''

    name = 'check_sql'
    streams = {
        'result': {
            'type': str,
            'description': 'Query result.',
        },
        'result_num': {
            'type': float,
            'description': 'Query result numeric.',
        },
        'query_time': {
            'type': float,
            'description': 'Time taken to execute the query.',
        },
    }

    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'scheme': {
                'type': 'string',
                'enum': ['postgresql', 'mysql', 'oracle', 'mssql', 'sqlite']
            },
            'host': {
                'type': 'string',
                'default': '',
                'description': 'Address to the server. Can be unix socket or '
                               'sqlite file. Defaults to unix domain socket.'
            },
            'port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
                'description': 'Port to the server. Defaults to driver default.'
            },
            'username': {
                'type': 'string',
                'description': 'Database username. '
                               'Not necessary for unix domain socket.'
            },
            'password': {
                'type': 'string',
                'description': 'Database password. '
                               'Not necessary for unix domain socket.'
            },
            'dbname': {
                'type': 'string',
                'description': 'Name of the database.'
            },
            'query': {
                'type': 'string',
                'description': 'SQL query to send to database.'
            }
        },
        'required': ['scheme', 'host', 'query'],
        'additionalProperties': False
    }

    def do_run(self):
        import sqlalchemy
        from sqlalchemy import exc
        from sqlalchemy.event import listen
        from furl import furl

        def start_query(conn, *dummy):
            ''' Save time the query starts. '''
            conn.info['wh_time'] = timeit.default_timer()

        def end_query(conn, *dummy):
            ''' Save time the query's finished. '''
            conn.info['wh_time'] = timeit.default_timer() - conn.info['wh_time']

        config = self.config.copy()
        del config['memory_limit']
        del config['frequency']
        del config['run_timeout']

        # Sqlite wants another '/'...
        if config['scheme'] == 'sqlite':
            config['host'] = "/{}".format(config['host'])

        query = config.pop('query')

        urlf = furl().set(**config)

        try:
            engine = sqlalchemy.create_engine(urlf.url)
        except ImportError as err:
            return ((
                'error',
                '{}. Sensor checking sql requires it. Please install it.'
                .format(err)
            ),)

        error_msg = (
            '(database {})\nError: {{}}\n Message from database: "{{}}"'
            .format(urlf.set(password='*****').url)
        )
        try:
            connection = engine.connect()
        except exc.TimeoutError:
            return (
                ('error', error_msg.format('Timeout getting connection', None)),
            )
        except exc.SQLAlchemyError as err:
            return (
                ('error', error_msg.format('Could not connect to database', err)),
            )

        listen(connection, 'before_cursor_execute', start_query)
        listen(connection, 'after_cursor_execute', end_query)
        try:
            result = connection.execute(query).fetchall()
        except exc.StatementError as err:
            return ((
                'error', error_msg.format(
                    'Error executing statement {}'.format(err.statement), err)
            ),)
        except exc.SQLAlchemyError as err:
            return ((
                'error', error_msg.format(
                    'Error executing statement, your query: {}'.format(
                        self.config['query']),
                    err.message)
            ),)
        finally:
            connection.close()

        try:
            if len(result) == 1 and len(result[0]) == 1:
                result = ('result_num', float(result[0][0]))
            else:
                raise ValueError
        except ValueError:
            result = ('result', str(result)[1:-1])

        return (result, ('query_time', connection.info['wh_time']))

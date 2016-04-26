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

    # TODO #1671: Better way for getting raw config
    config_raw = config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'dbtype': {
                'type': 'string',
                'enum': ['postgresql', 'mysql', 'oracle', 'mssql', 'sqlite']
            },
            'host': {
                'type': 'string',
                'default': '',
                'description': 'Server address. '
                               'Can be IP, hostname, socket or sqlite file.'
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
            'database': {
                'type': 'string',
                'description': 'Name of the database.'
            },
            'query': {
                'type': 'string',
                'description': 'SQL query to send to database.'
            }
        },
        'required': ['dbtype', 'host', 'query'],
        'additionalProperties': False
    }

    def do_run(self):
        # R0914: Too many local variables.
        # pylint: disable=R0914

        import sqlalchemy
        from sqlalchemy import exc
        from sqlalchemy.event import listen
        from sqlalchemy.engine.url import URL

        def start_query(conn, *dummy):
            ''' Save time the query starts. '''
            conn.info['wh_time'] = timeit.default_timer()

        def end_query(conn, *dummy):
            ''' Save time the query's finished. '''
            conn.info['wh_time'] = timeit.default_timer() - conn.info['wh_time']

        config = {
            k: v for k, v in self.config.iteritems()
            if k in self.config_raw['properties'].keys()
        }
        config['drivername'] = config.pop('dbtype')

        if config['drivername'] == 'sqlite':
            config['database'] = config.pop('host')

        query = config.pop('query')

        url = URL(**config)

        try:
            engine = sqlalchemy.create_engine(url)
        except ImportError as err:
            return ((
                'error',
                '{}. Sensor checking sql requires it. Please install it.'
                .format(err)
            ),)

        error_msg = (
            '(database {})\nError: {{}}\n Message from database: "{{}}"'
            .format(url.__to_string__())
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
            time = connection.info['wh_time']
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

        return (result, ('query_time', time))

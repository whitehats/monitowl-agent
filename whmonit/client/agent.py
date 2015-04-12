#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Agent - software that runs on client machine, runs sensors as scheduled, sends
    them raw to collector (over http).
'''
import sys
if sys.version_info.major != 2 or sys.version_info.minor < 7:
    print >> sys.stderr, 'You have to install python2.7 ' \
                         'or newer (in 2.x line)!'
    sys.exit(1)

import datetime
import hashlib
import importlib
import json
import multiprocessing
import os
import re
import signal
import ssl
import sqlite3
import time
import threading
from abc import ABCMeta, abstractmethod
from functools import partial
from itertools import izip
from multiprocessing.managers import SyncManager
from OpenSSL import crypto
from Crypto.Util import asn1

# Kenji: I'm taking dispense from our formatting guide, we need this here.
from whmonit.common.log import AgentErrorLogHandler, getLogger

import jsonschema
import psutil
import requests
import gzip
import StringIO
import yaml
from furl import furl
from interruptingcow import timeout

# C0103: Invalid constant name
# pylint: disable=C0103
if sys.platform in ['linux2', 'darwin']:
    from monotime import monotonic as timer
    from setproctitle import setproctitle
else:
    setproctitle = lambda x: x
    from time import time as timer
    getLogger('client.Agent').debug(
        "Your platform {} doesn't support monotonic clock,"
        " using normal clock. During time changes it may misbehave.".format(sys.platform)
    )

from whmonit.client.sensors.base import (
    TaskSensorBase, AdvancedSensorBase, InvalidDataError
)
from whmonit.common.serialization.json import JSONTypeRegistrySerializer
from whmonit.common.time import (
    milliseconds_to_datetime, MillisecondTimestampRangeError
)
from whmonit.common.types import (
    AgentRequestChunk, AgentRequest, ID, StreamName, SensorConfig,
)
from whmonit.common.types import PRIMITIVE_TYPE_REGISTRY as TYPE_REGISTRY
from whmonit.common.webclient import RequestManager, ComputationError


SENSOR_TIMEOUT_EXITCODE = 22


class TimeoutException(RuntimeError):
    '''
    Exception for sensor timeout.
    '''
    pass


class TerminatedException(Exception):
    '''
    Raised when sensor terminates ifself.
    '''
    pass


class ConnectionException(Exception):
    '''
    Raised when 5 attempts for getting data from server fail.
    '''
    pass


class StatusCodeException(Exception):
    '''
    Raised when getting status_code from server different than expected.
    '''
    pass


def make_request(ca_path, cert, params, function, url, data=None, hooks=None, headers=None):
    ''' Wrapper for requests calls '''
    # R0913: Too many arguments
    # pylint: disable=R0913
    if not headers:
        headers = {}
    if data:
        # Compress data before sending.
        out = StringIO.StringIO()
        with gzip.GzipFile(fileobj=out, mode="w") as fileh:
            fileh.write(data)
        data = out.getvalue()
        out.close()
        headers.update({'Content-Encoding': 'gzip', 'Accept-encoding': 'gzip'})

    return function(
        url,
        data=data,
        headers=headers,
        params=params,
        verify=ca_path,
        cert=cert,
        hooks=hooks
    )


def timeout_on_windows(func, time_out, pid):
    '''
    Checks timeout on windows and kill processes
    '''
    thread = threading.Thread(target=func)
    thread.start()
    thread.join(time_out)
    if thread.is_alive():
        os.system("taskkill /F /PID {} /T".format(pid))
        raise TimeoutException


def logger(name):
    ''' Wrapper logging.getLoger
    '''
    return getLogger('client.{}'.format(name))


def make_sqlite_conn(dbpath):
    '''
    Return connection to sqlite db with given path.
    '''
    sqliteconn = sqlite3.connect(
        dbpath,
        timeout=60,
        check_same_thread=False
    )
    return sqliteconn


class AgentInternal(multiprocessing.Process):
    '''
    Base class for agent internal processes (Shipper and Receiver).
    Groups common functionality.
    '''

    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(AgentInternal, self).__init__(*args, **kwargs)
        self.log = logger(self.__class__.__name__)
        self.process = None
        self.serializer = JSONTypeRegistrySerializer(TYPE_REGISTRY)
        self.ppid = None
        self.running = multiprocessing.Event()
        self.running.set()

    def __getstate__(self):
        to_pickle = dict(self.__dict__)
        del to_pickle['log']
        return to_pickle

    def __setstate__(self, to_pickle):
        self.__dict__.update(to_pickle)
        self.log = logger(self.__class__.__name__)

    def assert_parent_exists(self):
        '''
        Check if parent process has changed. Raise exception if it has.
        '''
        if self.ppid != self.process.ppid():
            raise Exception('Parent process changed')

    @abstractmethod
    def run(self):
        '''
        Run process to do its job.
        '''
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        setproctitle(self.name)
        self.process = psutil.Process(self.pid)
        self.ppid = self.process.ppid()

    def stop(self):
        '''
        Stops process execution in a gently manner.
        '''
        self.running.clear()


class StorageManager(object):
    '''
    Manager for per sensor persistent storage.

    Uses `multiprocessing.managers.SyncManager` to give sensors access
    to a dict-like structure, which automagically synchronizes with
    the main process.

    Values are stored in sqlite as stringified JSON documents.
    '''
    # TODO #1505: check if storage manager is pickable
    def __init__(self, dbpath):
        '''
        Initializes sync manager and logger.
        '''
        self.log = logger(self.__class__.__name__)
        self.storages = {}
        self.manager = SyncManager()
        self.manager.start(partial(signal.signal, signal.SIGINT, signal.SIG_IGN))

        self.ppid = None

        self.sqliteconn = make_sqlite_conn(dbpath)

    def get_storage(self, name):
        '''
        Retrieves storage for given name. If such storage doesn't exist,
        a new one, possibly with data got from sqlite, will be created.

        Note that name is not necessarily sensor's name. In fact,
        most of the time it will be sensor_name+hash(sensor_config).
        This way we can differentiate storages within one sensor type.
        '''
        self.log.debug('Storage requested for `{}`'.format(name))

        if name in self.storages:
            return self.storages[name]

        cursor = self.sqliteconn.cursor()
        cursor.execute("SELECT value FROM sensorstorage WHERE key=?", (name,))
        try:
            storage_data = json.loads(cursor.fetchone())
        # Catching too general exception
        # pylint: disable=W0703
        except Exception:
            storage_data = {}
        # Instance of 'SyncManager' has no 'dict' member
        # pylint: disable=E1101
        self.storages[name] = self.manager.dict(storage_data)
        return self.storages[name]

    def shutdown(self):
        '''
        Flushes all remaining storages into sqlite
        and shuts down manager.
        '''
        self.log.debug('Shutting down storage manager')

        cursor = self.sqliteconn.cursor()
        for sensor, store in self.storages.iteritems():
            cursor.execute(
                'INSERT OR REPLACE INTO sensorstorage'
                ' (key, value) VALUES (?,?)',
                (sensor, json.dumps(dict(store))),
            )
        self.sqliteconn.commit()
        self.sqliteconn.close()
        self.manager.shutdown()


class Sensor(multiprocessing.Process):
    '''
    Sensor process - for each scheduled sensor there is a separate process that
        runs sensor at given frequency. Results are passed to lstorage process
        via multiprocessing.Queue.
    '''
    # R0902: Too many instance attributes
    # pylint: disable=R0902

    proc_name = 'monitowl.sensor.{}'
    import_path = 'whmonit.client.sensors.{}.linux_01'
    class_name = 'Sensor'

    def __init__(self, queue, sensor, config, config_id, target, target_id, storage):
        '''
        Here we initialize Sensor class.
        '''
        # R0913: Too many arguments
        # pylint: disable=R0913
        super(Sensor, self).__init__(
            name=self.__class__.proc_name.format(sensor)
        )
        self.log = logger(self.__class__.__name__)
        self.queue = queue
        self.sensor = sensor
        self.config = config
        self.config_id = config_id
        self.target = target
        self.target_id = target_id
        self.process = None
        self.ppid = None
        self.config_queue = multiprocessing.Queue()
        self.do_config = multiprocessing.Event()
        self.sensor_class = getattr(importlib.import_module(
            self.__class__.import_path.format(self.sensor),
        ), self.__class__.class_name)
        self.running = multiprocessing.Event()
        self.running.set()

        self.storage = storage

    def __getstate__(self):
        '''
        Remove logging from be pickled.

        On Windows multiprocessing does not use fork. It creates child process
        and sends pickled (serialized) data. Logging can't be pickled so
        it must be removed from 'things to be pickled' dictionary.
        '''
        to_pickle = dict(self.__dict__)
        del to_pickle['log']
        return to_pickle

    def __setstate__(self, to_pickle):
        self.__dict__.update(to_pickle)
        self.log = logger(self.__class__.__name__)

    def run(self):
        '''
        Let the sensor run according to configuration.
        '''
        # SIGINT is ignored because it's 'inherited' and can cause that
        # all sensors will die if one of them gets sigint
        # R0912: Too many branches
        # pylint: disable=R0912
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        setproctitle(self.name)
        self.process = psutil.Process(self.pid)
        self.ppid = self.process.ppid()

        self.log.debug('Starting new sensor {} {}'.format(
            self.sensor,
            self.config
        ))

        # build callback function "personalized" for sensor instance
        send_results = partial(self.send_results, self.sensor_class)

        # AdvancedSensor does not have "standard" settings
        if not issubclass(self.sensor_class, AdvancedSensorBase):
            self.config = SensorConfig(self.config)

        sensor_instance = self.sensor_class(
            self.config, send_results, self.storage, self.config_id
        )
        try:
            if isinstance(sensor_instance, TaskSensorBase):
                runtime = timer()

                while self.running.is_set():
                    if self.do_config.is_set():
                        self.config = SensorConfig(self.config_queue.get())
                        self.log.debug('Reconfiguring sensor {} {}'.format(
                            self.sensor,
                            self.config,
                        ))
                        sensor_instance.reload(self.config)
                        self.do_config.clear()

                    # Calculate exact time when should be next run and sleep that
                    # time.
                    sleeptime = self.config['sampling_period'] - (timer() - runtime)
                    if sleeptime < 0:
                        self.log.warning('We are behind the schedule ({} secs)!'
                                         .format(sleeptime))
                        sleeptime = 0
                    self.log.debug('Will run sensor {} in {} secs'.format(
                        self.sensor,
                        sleeptime
                    ))
                    if sleeptime > 0:
                        time.sleep(sleeptime)

                    runtime = timer()
                    self.log.debug('Run sensor {}'.format(self.sensor))

                    # Setup a timeout.
                    try:
                        if sys.platform in ['linux2', 'darwin']:
                            with timeout(self.config['run_timeout'], TimeoutException):
                                sensor_instance.run()
                        else:
                            timeout_on_windows(
                                sensor_instance.run,
                                self.config['run_timeout'],
                                self.pid
                            )
                    except TimeoutException:
                        sys.exit(SENSOR_TIMEOUT_EXITCODE)

                    # Check if parent changed or died (might raise
                    # psutil.NoSuchProcess exception).
                    if self.ppid != self.process.ppid():
                        raise Exception('Parent changed')

            elif isinstance(sensor_instance, AdvancedSensorBase):
                # Pass the control to the sensor.
                sensor_instance.run()

            else:
                self.log.error('Sensor {} is a child of unknown class {}, '
                               'will not run it.'
                               .format(self.sensor_class.__base__, self.sensor))
        except InvalidDataError as error:
            self.log.error(error.message)

    def stop(self):
        '''
        Stops sensor execution. Usually in a gently manner,
        not so gently (SIGTERM) for AdvancedSensors.
        '''
        self.running.clear()
        if issubclass(self.sensor_class, AdvancedSensorBase):
            self.terminate()

    def send_results(self, sensor_class, timestamp, data):
        '''
        Perform basic checks and put data into queue:
            * Is ``stream`` a valid name?
            * Is datatype specified by ``stream`` valid?
        If any of above checks fails, data is being ignored.
        '''
        for stream, output in data:
            msg = {
                'config_id': self.config_id,
                'data': output,
                'datatype': sensor_class.streams[stream]['type'],
                'timestamp': timestamp,
                'stream_name': stream,
            }
            self.queue.put(msg)

    def reconfigure(self, config):
        '''
        Applies new config to existing sensor.
        If sensor is an AdvancedSensor (AS), it gets terminated.
        Caller should take care to restart the process if needed.

        Sensor will use new config from the next run onwards.

        :param config: New configuration to apply.
        :raises: TerminatedException if AS and got terminated.
        '''
        if config != self.config:
            if issubclass(self.sensor_class, AdvancedSensorBase):
                self.terminate()
                raise TerminatedException
            self.config = config
            self.do_config.set()
            self.config_queue.put(self.config)


class Receiver(AgentInternal):
    '''
    Receiver process - we run one instance of it. Responsible for reading data
        from multiprocessing.Queue and storing it in sqlite buffer.
    '''

    def __init__(self, queue, dbpath):
        '''
        Initialize variables, setup queue and sqlite.
        '''
        super(Receiver, self).__init__(name='monitowl.receiver')
        self.queue = queue
        self.dbpath = dbpath

    def run(self):
        '''
        Collect data from sensorprocs (via multiprocessing.Queue) and store it
        in local buffer (sqlite).
        '''
        super(Receiver, self).run()
        with make_sqlite_conn(self.dbpath) as conn:
            while self.running.is_set():
                # Get data from sensors queue and store it in sqlite:
                # Wait 1 sec, then read from queue until it's empty.
                # This `hack` is necessary because using queue.get with timeout
                # might result in deadlocking queue if process dies.
                # TODO #1102: Event based reading from queue
                time.sleep(1)
                while True:
                    try:
                        msg = self.queue.get_nowait()
                        data = self.serializer.pack(msg['datatype'](msg['data']))

                        cursor = conn.cursor()
                        cursor.execute(
                            'INSERT INTO sensordata (stamp, config_id, stream, '
                            'result) VALUES (?, ?, ?, ?)',
                            [self.serializer.serialize(msg['timestamp']),
                             msg['config_id'],
                             msg['stream_name'],
                             data]
                        )
                    except multiprocessing.queues.Empty:
                        # Go off the loop, sleep 1 sec.
                        break
                conn.commit()
                self.assert_parent_exists()


class Shipper(AgentInternal):
    '''
    Shipper process - we run one instance of it. Responsible for reading data
        from sqlite buffer and sending it to collector.
    '''
    # R0902: Too many instance attributes
    # pylint: disable=R0902

    def __init__(self, send_results, dbpath):
        '''
        Initialize variables, setup queue and sqlite connection.
        '''
        super(Shipper, self).__init__(name='monitowl.shipper')
        self.dbpath = dbpath
        self.send_results = send_results
        self.sleeptime = 1.0
        # collector connection fail counters
        self._confails = 1

    def run(self):
        super(Shipper, self).run()
        with make_sqlite_conn(self.dbpath) as conn:
            while self.running.is_set():
                # Get data from sqlite and send it to collector.
                time.sleep(self.sleeptime)
                cursor = conn.cursor()
                # LIMIT is set due to possible DELETE problem
                # OperationalError: too many SQL variables
                cursor.execute('SELECT * FROM sensordata ORDER BY stamp DESC LIMIT 250')
                data = cursor.fetchall()

                # Adjust sleeptime according to size of data fetched from sqlite
                # sleeptime is one of {0.2, 0.4, 0.6, 0.8, 1.0}(seconds).
                if len(data) > 200:
                    self.sleeptime = max(0.2, self.sleeptime - 0.2)
                elif len(data) < 160:
                    self.sleeptime = min(1.0, self.sleeptime + 0.2)
                if self.sleeptime <= 0.2:
                    self.log.debug('Maximum capacity reached')

                req_list = AgentRequest()
                data_to_remove = []
                for timestamp, config_id, stream, result in data:
                    req = AgentRequestChunk(
                        ID(config_id),
                        StreamName(stream),
                        self.serializer.deserialize(timestamp, 'datetime'),
                        self.serializer.unpack(result)
                    )
                    req_list.append(req)
                    data_to_remove.append((config_id, timestamp))

                if req_list:
                    try:
                        self.send_results(
                            self.serializer.serialize(req_list),
                            {
                                'response': partial(
                                    self._reqdone,
                                    data_to_remove,
                                    conn
                                )
                            },
                        )
                    except requests.exceptions.RequestException as ex:
                        self.log.debug('Error while PUTing: {}'.format(ex))
                self.assert_parent_exists()

    def _reqdone(self, data_to_remove, conn, response, **_kwargs):
        '''
        Requests hook function - run after request finish.
        '''
        if response.status_code == 0:
            # Could not connect to collector.
            self._confails = self._confails + 1
            if self._confails > 200:
                self._confails = 200
            self.log.debug('Connection failed, _confails: {}'.format(self._confails))
            return
        elif response.status_code == 200:
            self.log.debug('Data sent {} chars'.format(len(response.request.body)))
        else:
            self.log.error('Error while sending: {}'.format(response.text))

        self._confails = 1
        if response.status_code in (200, 400):
            # status_code 400 - data was sent but collector ignored it
            # TODO #1145: Do not use `response status code` alone for
            #             communicating status of received data

            try:
                data_saved = json.loads(response.text)
            except ValueError:
                self.log.error('Received data are invalid.')
                return
            if data_saved['status'] == 'Not_all_saved':
                data_to_remove = data_saved['data']

            cursor = conn.cursor()
            # This way of deleting rows might cause
            # OperationalError: too many SQL variables
            data_placeholders = ('?,' * len(data_to_remove))[:-1]
            cursor.execute(
                'DELETE FROM sensordata WHERE config_id IN ({}) AND stamp IN ({})'.format(
                    data_placeholders, data_placeholders
                ), sum(izip(*data_to_remove), ())
            )
            conn.commit()
        else:
            self.log.exception('POST problem, response status: {}'.format(
                response.status_code
            ))


class Agent(object):
    '''
    Main class for agent code - we just run one instance and let it run.
    It is also able to restart killed child processes (sensors etc.).
    '''
    # Too many instance attributes
    # R0913: Too many arguments
    # pylint: disable=R0902,R0913

    def __init__(self, config_filename, agent_id, server_address,
                 webapi_address, sqlite_path, certs_dir, time_diff=600):
        self._queue = multiprocessing.Queue()
        # Get logger initialized in client.
        self.log = logger(self.__class__.__name__)

        setproctitle('monitowl.agent')

        self.agentconfig = {}
        self.configfile = config_filename
        self.agent_id = agent_id
        self.serveraddr = server_address
        self.webapi_address = webapi_address
        self.certs_dir = certs_dir
        self.csr_path = os.path.join(self.certs_dir, 'agent.csr')
        self.crt_path = os.path.join(self.certs_dir, 'agent.crt')
        self.key_path = os.path.join(self.certs_dir, 'agent.key')
        self.ca_path = os.path.join(self.certs_dir, 'ca.crt')
        self.intern_sensors = {
            'error_id': None,
            'config_applied_id': None
        }
        # Acceptable time difference between agent and collector
        # in seconds with millisecond precision
        self.time_diff = datetime.timedelta(seconds=time_diff)
        self.log.debug('Agent: {}, Server address: {}'
                       .format(self.agent_id, self.serveraddr))

        self.serializer = JSONTypeRegistrySerializer(TYPE_REGISTRY)

        self.make_request = self._make_requests_wrapper()
        self.load_config()
        self._subprocesses = []

        self._prepare_sqlite(sqlite_path)
        self.sqlite_path = sqlite_path

        self.storage_manager = StorageManager(self.sqlite_path)

        self.running = True

    def _prepare_sqlite(self, dbpath):
        '''
        Creates sql database.
        '''
        connection = make_sqlite_conn(dbpath)
        cursor = connection.cursor()

        self.log.debug('Connecting to sensordata db at {}'.format(dbpath))

        cursor.execute('PRAGMA auto_vacuum = FULL')
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS sensordata (stamp TEXT, config_id '
            'TEXT, stream TEXT, result TEXT)'
        )
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS sensorstorage (key TEXT, value TEXT)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS index_id on sensordata (config_id);'
        )
        cursor.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS '
            'storage_key on sensorstorage (key)'
        )

        # check integrity of existing database
        cursor.execute('PRAGMA integrity_check')

        connection.commit()
        return connection

    def check_connection(self):
        '''
        Check if connection to server is available.
        '''
        remote = furl(self.serveraddr)
        remote.path = '/'

        self.log.debug('Remote check: {}'.format(remote.url))
        try:
            self.make_request(
                requests.get,
                remote.url
            )
            self.log.info('Connection successful')
        except requests.RequestException:
            self.log.info('Connection unsuccessful')

    def _is_time_synchronized(self, sleep_time=0.2):
        '''
        get collector's current datetime and
        return True if agent and collectors time difference
            is smaller than self.time_diff
        return False otherwise
        :param sleep_time: time to sleep between attempts (in seconds)
        '''

        remote = furl(self.serveraddr)
        remote.path.add('/time/')

        # Make 5 attempts to validate datetime from collector
        for _ in xrange(5):
            self.log.debug(
                'Getting datetime from collector ({})'.format(remote)
            )
            try:
                req = self.make_request(requests.get, remote.url)
                if req.status_code != 200:
                    raise StatusCodeException(
                        'Error while fetching datetime from `{}`; '
                        'got {}, expected {}'
                        .format(remote.url, req.status_code, 200)
                    )
                timestamp = json.loads(req.text)['timestamp']
                collector_time = milliseconds_to_datetime(long(timestamp))
                agent_time = datetime.datetime.utcnow()
                real_diff = abs(collector_time - agent_time)
                self.log.debug(
                    'Agent - collector time difference is {}s: '
                    "agent's time: {}, collector's time: {}."
                    .format(
                        real_diff.total_seconds(), agent_time, collector_time
                    )
                )
                return real_diff < self.time_diff

            except requests.RequestException as ex:
                self.log.info('Connection problem while asking for datetime')
                self.log.debug(ex.message)
            except AssertionError as ex:
                self.log.info(str(ex))
            except MillisecondTimestampRangeError as ex:
                self.log.error(
                    'Collectors timestamp out of range - cannot convert.'
                )
            time.sleep(sleep_time)
        raise ConnectionException(
            '5 attempts for datetime failed. Read error log.'
        )

    def save_config(self, config):
        '''
        Check if config is valid, save it and apply

        :param config: JSON configuration
        :type config: dict.
        '''
        config_schema = {
            '$schema': 'http://json-schema.org/schema#',
            'type': 'object',
            'properties': {
                'sensors': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'config': {'type': 'object'},
                            'sensor': {'type': 'string', 'minLength': 2},
                            'config_id': {'type': 'string', 'minLength': 2},
                            'target': {'type': 'string', 'minLength': 2},
                            'target_id': {'type': 'string', 'minLength': 2}
                        },
                        'required': [
                            'config', 'sensor', 'config_id',
                            'target', 'target_id'
                        ],
                        'additionalProperties': False
                    },
                    'uniqueItems': True
                }
            },
            'required': ['sensors'],
            'additionalProperties': False
        }
        try:
            jsonschema.validate(config, config_schema)
        except jsonschema.ValidationError as error:
            self.log.error('Config invalid, has not been applied: {} ({})'
                           .format(config, error))
            return

        for sensor in list(config['sensors']):
            if sensor['sensor'] == '_error':
                self.intern_sensors['error_id'] = sensor['config_id']
                config['sensors'].remove(sensor)
            elif sensor['sensor'] == '_conf_applied':
                self.intern_sensors['config_applied_id'] = sensor['config_id']
                config['sensors'].remove(sensor)

        self.agentconfig = config
        with open(self.configfile, 'w') as fileh:
            fileh.write(yaml.safe_dump(config))

        if self.intern_sensors['config_applied_id']:
            self.send_new_config(self.agentconfig)
        else:
            self.log.warning(
                'Config invalid, does not provide config_id for _conf_applied sensor. '
                'Could not notify server that configuration has been applied.'
            )

    def send_new_config(self, config):
        '''
        Notify collector that new config has been applied.
        '''
        req_list = AgentRequest()

        req_chunk = AgentRequestChunk(
            ID(self.intern_sensors['config_applied_id']),
            StreamName('_config_applied'),
            datetime.datetime.utcnow(),
            'New configuration has been applied ({})'.format(
                hashlib.sha1(str(config)).hexdigest()
            )
        )
        req_list.append(req_chunk)

        remote = furl(self.serveraddr)
        remote.path.add('/store_data')
        self.make_request(
            requests.put,
            remote.url,
            self.serializer.serialize(req_list)
        )

    def load_config(self):
        '''
        Load configs from conf file. (yaml formated)
        '''
        self.log.debug('Loading configuration from file ({})'
                       .format(self.configfile))
        try:
            loaded_config = yaml.safe_load(open(self.configfile).read())
        except IOError:
            loaded_config = yaml.safe_load('sensors: []')
            self.log.info('No config file, creating new one.')

        self.save_config(loaded_config)

    def get_remote_config(self):
        '''
        get agent config from collector
        '''

        remote = furl(self.serveraddr)
        remote.path.add('/agent_config/')

        for _ in xrange(5):
            self.log.debug(
                'Loading configuration from remote ({})'.format(remote)
            )
            try:
                req = self.make_request(requests.get, remote.url)
                if req.status_code != 200:
                    raise StatusCodeException(
                        'Error while fetching config from `{}`: {}'
                        .format(remote.url, req.text)
                    )
                loaded_config = json.loads(req.text)['config']
                self.save_config(loaded_config)
                return
            except requests.RequestException:
                self.log.info('Connection problem while asking for conf')
            except AssertionError as ex:
                self.log.info(str(ex))
                raise
            time.sleep(10)
        raise ConnectionException(
            '5 attempts for remote config failed. Read error log.'
        )

    def request_certificate(self):
        '''
        send certificate signing request to collector
        '''
        if not os.path.exists(self.csr_path):
            self.log.error('File `{}` does not exist.'.format(self.csr_path))
            sys.exit(1)

        remote = furl(self.serveraddr)
        remote.path.add('csr')

        self.log.debug('Sending certificate signing request to {}'
            .format(remote)
        )

        with open(self.csr_path) as csr:
            csr_content = csr.read()
        res = self.make_request(
            requests.put,
            remote.url,
            csr_content
        )
        if (res.ok):
            self.log.info('Certificate signing request successfully sent.')
        else:
            self.log.error(
                'Error while sending certificate signing request. {} {}.'
                .format(res.status_code, res.reason)
            )

        csr_hash = hashlib.md5(csr_content)
        self.log.info(
            'Agent identificator dependant on sent CSR: `{}`.'
            .format(
                csr_hash.hexdigest()[-5:]
            )
        )

    @staticmethod
    def check_crypto(crt, key):
        """
        Checks if the key matches the certificate.
        """
        agent_crt = crypto.load_certificate(crypto.FILETYPE_PEM, crt)
        agent_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)

        agent_pub = agent_crt.get_pubkey()

        # This seems to work with public as well
        pub_asn1 = crypto.dump_privatekey(crypto.FILETYPE_ASN1, agent_pub)
        priv_asn1 = crypto.dump_privatekey(crypto.FILETYPE_ASN1, agent_key)

        # Decode DER
        pub_der = asn1.DerSequence()
        pub_der.decode(pub_asn1)
        priv_der = asn1.DerSequence()
        priv_der.decode(priv_asn1)

        # Get the modulus
        pub_modulus = pub_der[1]
        priv_modulus = priv_der[1]

        return pub_modulus == priv_modulus

    def fetch_certificate(self):
        '''
        fetch (potentially) signed certificate from webserver
        '''
        remote = furl(self.webapi_address)
        remote.path = 'ws'
        self.log.debug(remote.url)
        reqman = RequestManager(remote.url,
                                ssloptions={
                                    "cert_reqs": ssl.CERT_REQUIRED,
                                    "ca_certs": self.ca_path
                                    })
        try:
            cert = reqman.request(
                'certificates',
                'fetch',
                {'agent_id': self.agent_id}
            )
        except ComputationError as ex:
            if re.search('t been signed yet', str(ex), re.I):
                self.log.info('Certificate has not been signed yet, please accept in admin panel.')
            elif re.search('has been revoked', str(ex), re.I):
                self.log.warning('Certificate for this agent has been revoked. '
                                 'Please accept new one in admin panel.')
            else:
                self.log.error(ex)
            return False
        finally:
            reqman.close()

        with open(self.key_path, 'r') as key_fh:
            if not self.check_crypto(cert, key_fh.read()):
                self.log.warning('A valid certificate exists and it doesn\'t match the private key.'
                                 ' Please revoke/reject all old certificates.')
                return False

        with open(self.crt_path, 'w', 0o400) as crt_fh:
            crt_fh.write(cert)

        self.log.info(
            'Certificate successfully fetched from {}'
            .format(remote.url)
        )
        return True

    def sensor_test(self, name=None, configuration=None):
        '''
        Make single run of sensor(s) and print results.

        It can be started by
        ./run_agent --test-sensors with
        --config-path config_from_file
        --test-sensors sensor_name config_dict

        :param str name: sensor name
        :param dict configuration: sensor configuration
        '''
        def sigint(signum, frame):
            del signum, frame
            self.log.debug('KeyboardInterrupt. Cleaning up. Please wait...')
            sensor.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, sigint)
        config = {'sensor': name, 'config': configuration}

        queue = multiprocessing.Queue()
        sensor = Sensor(
            queue,
            config['sensor'],
            SensorConfig(config['config']),
            'config_id',
            'target',
            'target_id',
            {},
        )
        sensor.start()
        while True:
            self.log.debug('{}: {}'.format(name, queue.get()))

    def run(self):
        '''
        start agent job: run all sensorprocs and communication to collector
        '''
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGINT, self.terminate)

        setproctitle('monitowl.agent')
        # Set custom error handler.
        if self.intern_sensors['error_id'] is not None:
            self.log.addHandler(
                AgentErrorLogHandler(self._queue, self.intern_sensors['error_id'])
            )
        else:
            self.log.warning("No sensorid found for error stream, will not send errors to server!")

        # Check if server's and agent's clocks are more or less synchronized.
        if not self._is_time_synchronized(10):
            self.log.error(
                "Server's and this machine's times "
                'differ by more then {}s'.format(self.time_diff)
            )
            self.running = False
            return
        # Create callback for sending data to collector in shipper.

        remote = furl(self.serveraddr)
        remote.path.add('/store_data')
        send_results = self._make_requests_wrapper(
            requests.put,
            remote.url
        )
        # Spawn processes for data transfer.
        self._start_subprocess(Receiver, (self._queue, self.sqlite_path))
        self._start_subprocess(Shipper, (send_results, self.sqlite_path))

        # Periodically check child processes and restart them if needed.
        recheck_config_timeout = 1
        while self.running:
            recheck_config_timeout -= 1
            if not recheck_config_timeout:
                self.get_remote_config()
                self._spawn_sensors()
                recheck_config_timeout = 60

            time.sleep(1)
            for process in self._subprocesses:
                if isinstance(process, Sensor) and process.memory_limit > 0:
                    # Check memory usage of sensor process, terminate sensor if
                    # limit hit. We can't use process.memory_info because
                    # it's not being updated.
                    try:
                        # UNIX: Resident Set Size
                        # Windows: Mem Usage in taskmgr.exe
                        # TODO #1146: use `ulimit` to limit sensors' memusage on UNIX
                        rss_info = psutil.Process(process.pid).memory_info()[0]
                        if rss_info > process.memory_limit:
                            self.log.error(
                                '`{}`[{}] memory limit reached ({}>{})- restarting'
                                .format(
                                    process.name,
                                    process.pid,
                                    rss_info,
                                    process.memory_limit
                                )
                            )
                            process.terminate()
                    except psutil.NoSuchProcess:
                        # Process is not alive, we will handle it later.
                        pass
                if not process.is_alive():
                    self._restart_subprocess(process)
        self.cleanup()

    def _spawn_sensors(self):
        '''
        Spawns sensors specified in current config, if not already running.

        Sensors already present in the agent have their config updated
        to reflect possible changes.
        No longer existing sensors are terminated and removed.
        '''
        new_sensors = {s['config_id']: s for s in self.agentconfig['sensors']}
        running_sensors = {
            s.config_id: s for s in self._subprocesses if isinstance(s, Sensor)
        }

        def remove_sensor(config_id, sensor):
            '''
            Removes sensor from agent's processes list
            and running sensors temporary mapping.
            '''
            self.log.debug('Terminating sensor {}'.format(sensor.sensor))
            self._subprocesses.remove(sensor)
            del running_sensors[config_id]

        for config_id, sensor in running_sensors.copy().iteritems():
            if config_id not in new_sensors:
                sensor.terminate()
                remove_sensor(config_id, sensor)

        for config_id, sensor in new_sensors.iteritems():
            config = sensor['config']
            if config_id in running_sensors:
                running_sensor = running_sensors[config_id]

                try:
                    running_sensor.reconfigure(config)
                except TerminatedException:
                    remove_sensor(config_id, running_sensor)
                else:
                    continue

            # We want to pass original config to Sensor,
            # because AdvancedSensors don't have "standard" settings.
            memory_limit = SensorConfig(config)['memory_limit']
            storage = self.storage_manager.get_storage("{}:{}".format(
                sensor['sensor'], config_id,
            ))
            self._start_subprocess(
                Sensor, (
                    self._queue,
                    sensor['sensor'],
                    config,
                    config_id,
                    sensor['target'],
                    sensor['target_id'],
                    storage,
                ), memory_limit=memory_limit,
            )

    def _make_requests_wrapper(self, *args):
        '''
        Create wrapper for `requests` library with predefined parameters.
        '''
        certs_exist = os.path.exists(self.crt_path) and os.path.exists(self.key_path)
        if not certs_exist:
            self.log.debug("Agent doesn't have certificate.")
        return partial(
            make_request,
            self.ca_path,
            (self.crt_path, self.key_path) if certs_exist else None,
            {'agent_id': self.agent_id},
            *args
        )

    def _start_subprocess(self, cls, proc_args=None, proc_kwargs=None,
                          memory_limit=0):
        '''
        Run instance of `cls` as child process and add it to childs list
        along with its arguments.

        .. warning:: `cls` must be subclass of multiprocessing.Process!

        :param proc_args: positional arguments of `cls` constructor
        :param proc_kwargs: keyword arguments of `cls` constructor
        :param memory_limit: memory limit for child process (bytes), child
                             is being killed when limit reached. Default 0 -
                             no limit.
        :returns: object representing child process
        :rtype: instance of :obj:`multiprocessing.Process`
        '''
        proc_args = proc_args or []
        proc_kwargs = proc_kwargs or {}
        subprocess = cls(*proc_args, **proc_kwargs)
        subprocess.proc_args = proc_args
        subprocess.proc_kwargs = proc_kwargs
        subprocess.memory_limit = memory_limit
        self._subprocesses.append(subprocess)

        subprocess.start()
        self.log.debug('Fork: new child process `{}`[{}]'
            .format(subprocess.name,
                    subprocess.pid))
        return subprocess

    def _restart_subprocess(self, instance):
        '''
        Remove `instance` from childs list then call `_start_subprocess`
        with `instance.__class__` and given patameters.

        .. warning:: `instance.__class__` must be subclass of
            multiprocessing.Process!

        :param proc_args: positional arguments of `instance.__class__`
                          constructor
        :param proc_kwargs: keyword arguments of `instance.__class__`
                            constructor
        :param memory_limit: memory limit for child process (bytes), child
                             is being killed when limit reached. Default 0 -
                             no limit.
        :returns: object representing new child process
        :rtype: instance of :obj:`multiprocessing.Process`
        '''
        self.log.error('`{}`[{}] {} - restarting, exit code {}'
            .format(instance.name,
                    instance.pid,
                    'timed out' if instance.exitcode == SENSOR_TIMEOUT_EXITCODE
                    else 'died',
                    instance.exitcode))
        self._subprocesses.remove(instance)
        return self._start_subprocess(instance.__class__,
                                      instance.proc_args,
                                      instance.proc_kwargs,
                                      instance.memory_limit)

    def terminate(self, signum, frame):
        '''
        Handles termination signal.
        '''
        del signum, frame

        self.running = False

    def cleanup(self):
        '''
        Cleans up environment. Called after main loop has exited.
        Requests termination on sensors.
        '''
        for subprocess in self._subprocesses:
            subprocess.stop()
        self.storage_manager.shutdown()

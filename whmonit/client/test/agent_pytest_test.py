#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Agent pytest tests.
'''
import json
import os
import sqlite3
from datetime import datetime
from multiprocessing.queues import Empty
import pytest
import requests
from mock import MagicMock, patch
from interruptingcow import timeout
from OpenSSL.crypto import Error as SSLError

from whmonit.common.types import SensorConfig
from whmonit.common.webclient import RequestManager
from whmonit.client.agent import Agent, Shipper, Receiver, Sensor, prepare_sqlite
from whmonit.client.sensors.uptime.linux_01 import Sensor as UptimeSensor
from whmonit.common.test.helpers import UnbufferedNamedTemporaryFile
from whmonit.common.time import datetime_to_milliseconds


# W0212: Access to a protected member of a client class
# W0201: Attribute defined outside __init__
# pylint: disable=W0212,W0201

class TestAgent(object):
    '''
    Agent tests.
    '''

    def setup(self):
        '''
        Setup test.
        '''
        self.storage_manager = patch('whmonit.client.agent.StorageManager')
        self.storage_manager.start()
        self.agentconfig = UnbufferedNamedTemporaryFile('sensors: []', False)
        self.agent = Agent(
            self.agentconfig.name,
            'dzik1',
            'http://localhost:8000/collector',
            'ws://localhost:8080',
            '.agentdata.db',
            os.path.dirname(os.path.realpath(__file__))
        )
        self.agent.make_request = MagicMock()
        self.agent.make_request.return_value.status_code = 200
        self.agent.make_request.return_value.text = json.dumps({
            'type': 'timestamp',
            'timestamp': str(datetime_to_milliseconds(datetime.utcnow()))
        })
        self.agent.get_remote_config = MagicMock()
        self.agent._start_subprocess = MagicMock()
        self.agent._restart_subprocess = MagicMock()
        self.agent._restart_subprocess.side_effect = Exception

        self.csr_file = UnbufferedNamedTemporaryFile('csr content', False)
        self.crt_file = UnbufferedNamedTemporaryFile('crt content', False)
        self.key_file = UnbufferedNamedTemporaryFile('key content', False)
        self.ca_file = UnbufferedNamedTemporaryFile('ca content', False)
        self.agent.csr_path = self.csr_file.name
        self.agent.crt_path = self.crt_file.name
        self.agent.key_path = self.key_file.name
        self.agent.ca_path = self.ca_file.name

    def teardown(self):
        '''
        Teardown test.
        '''
        self.storage_manager.stop()
        self.agentconfig.close()
        self.csr_file.close()
        self.crt_file.close()
        self.key_file.close()
        self.ca_file.close()

    def test_request_certificate(self):
        '''
        Request certificate.
        '''
        self.agent.request_certificate()
        self.agent.make_request.assert_called_once_with(
            requests.put,
            'http://localhost:8000/collector/csr',
            'csr content'
        )

    def test_fetch_certificate(self):
        '''
        Fetch certificate.
        '''
        RequestManager.__init__ = MagicMock()
        RequestManager.__init__.return_value = None
        RequestManager.request = MagicMock()
        RequestManager.request.return_value = 'new crt'
        RequestManager.close = MagicMock()

        with pytest.raises(SSLError):
            self.agent.fetch_certificate()
        RequestManager.request.assert_called_once_with(
            'certificates',
            'fetch',
            {'agent_id': 'dzik1'}
        )

    @pytest.mark.parametrize('offset', [720000, -720000, 86405000])
    def test_agent_server_time_diff(self, offset):
        '''
        Test for client to shutdown when there's
        over 10min differential to / from server
        '''
        self.agent.make_request.return_value.text = json.dumps(
            {'type': 'timestamp',
             'timestamp': (
                 str(datetime_to_milliseconds(datetime.utcnow()) + offset)
             )})
        # Function should terminate, so 1s should be enough
        with timeout(1):
            self.agent.run()
        assert self.agent.running is False

    def test_run_no_sensrs(self):
        '''
        Run with no sensors.
        '''
        try:
            with timeout(1.5):
                self.agent.run()
        except RuntimeError:
            pass

        assert self.agent._start_subprocess.call_count == 2

    def test_run_one_sensor(self):
        '''
        Run with one sensor - uptime.
        '''
        self.agent.agentconfig = {'sensors': [{
            'config': {'sampling_period': 60},
            'sensor': 'uptime',
            'config_id': 'config_id',
            'target': 'target',
            'target_id': 'target_id'
        }]}

        try:
            with timeout(2.5):
                self.agent.run()
        except RuntimeError:
            pass

        assert self.agent._start_subprocess.call_count == 3


@patch('whmonit.client.agent.AgentInternal.run', MagicMock())
class TestShipper(object):
    '''
    Shipper tests.
    '''

    def setup(self):
        '''
        Setup test.
        '''
        self.send_results = MagicMock()
        self.sqlite = sqlite3.connect(':memory:')

        prepare_sqlite(lambda: self.sqlite)
        self.shipper = Shipper(self.send_results, lambda: self.sqlite)
        self.shipper.assert_parent_exists = MagicMock()

    def test_run_no_data(self):
        '''
        Run without upcoming data.
        '''
        try:
            with timeout(1.5):
                self.shipper.run()
        except RuntimeError:
            pass

        assert self.shipper.assert_parent_exists.called

    @staticmethod
    def make_response(status_code, data):
        '''
        Prepares requests.Response instance with given status_code, data
        and mocked request part.
        '''
        response = requests.Response()
        response.status_code = status_code
        response._content = data
        response.request = MagicMock()
        return response

    def store_chunks(self, chunks):
        '''
        For every chunk, stores a list of (chunk[0], chunk[1], 'default', 3.14)
        elements in the database.
        '''
        self.sqlite.executemany(
            'INSERT INTO sensordata(stamp, config_id, stream, result) '
            'VALUES(?, ?, "default", 3.14)',
            chunks,
        )

    def assert_sensordata(self, expected):
        '''
        Asserts that the sensordata table contains expected items.
        '''
        data = sorted(self.sqlite.execute('SELECT * FROM sensordata').fetchall())
        assert data == sorted(expected)

    @pytest.mark.parametrize(('data', 'stored', 'erroneous', 'expected'), (
        (
            ((1, '1' * 40), (2, '2' * 40)),
            ((1, '1' * 40), (2, '2' * 40)),
            (),
            (),
        ),
        (
            ((1, '1' * 40), (2, '2' * 40), (3, '3' * 40)),
            ((1, '1' * 40), (3, '3' * 40)),
            (),
            (('2', '2' * 40),),
        ),
        (
            ((1, '1' * 40), (2, '2' * 40)),
            ((1, '1' * 40),),
            ((1, '1' * 40),),
            (('1', '1' * 40), ('2', '2' * 40)),
        ),
        (
            ((1, '1' * 40), (2, '2' * 40), (2, '1' * 40)),
            ((1, '1' * 40), (2, '2' * 40)),
            ((2, '1' * 40),),
            (('2', '1' * 40),),
        ),
    ))
    def test__reqdone(self, data, stored, erroneous, expected):
        '''
        Should remove sent data from database, excluding erroneous entries.
        '''
        response = self.make_response(200, json.dumps({
            "status": "ERROR_PARTIAL_STORE" if erroneous else "OK",
            "reason": erroneous,
        }))
        self.store_chunks(data)

        self.shipper._reqdone(stored + erroneous, self.sqlite, response)

        self.assert_sensordata([item + ('default', '3.14') for item in expected])

    @pytest.mark.parametrize(('status_code', 'data'), ((200, 'I'), (500, '{}')))
    def test__reqdone_response_error(self, status_code, data):
        '''
        Should not do anything.
        Especially not remove anything from database.
        '''
        response = self.make_response(status_code, data)
        sqlite = MagicMock()
        sqlite.cursor.return_value = MagicMock()

        self.shipper._reqdone((('1' * 40, 1)), sqlite, response)

        assert not sqlite.cursor().executemany.called


@patch('whmonit.client.agent.AgentInternal.run', MagicMock())
class TestReceiver(object):
    '''
    Receiver tests.
    '''

    def setup(self):
        '''
        Setup test.
        '''
        self.send_results = MagicMock()
        self.sqlite = sqlite3.connect(':memory:')

        self.receiver = Receiver(self.send_results, lambda: self.sqlite)
        self.receiver.assert_parent_exists = MagicMock()
        self.receiver.queue = MagicMock()
        self.receiver.queue.get_nowait.side_effect = Empty
        self.receiver.serializer = MagicMock()

    def test_run_no_data(self):
        '''
        Run without upcoming data.
        '''
        try:
            with timeout(1.5):
                self.receiver.run()
        except RuntimeError:
            pass

        assert self.receiver.assert_parent_exists.called


class TestSensor(object):
    '''
    Sensor tests.
    '''

    def setup(self):
        '''
        Setup test.
        '''
        Sensor.pid = 1
        self.queue = MagicMock()
        self.sensor = Sensor(
            self.queue,
            'uptime',
            SensorConfig({'sampling_period': 1}),
            'config_id',
            'target',
            'target_id',
            MagicMock(),
        )

    def test_run(self):
        '''
        Run sensor.
        '''
        self.sensor.send_results = MagicMock()
        try:
            with timeout(1.5):
                self.sensor.run()
        except RuntimeError:
            pass

        assert self.sensor.send_results.called

    def test_send_results(self):
        '''
        Send valid results.
        '''
        timestamp = datetime.utcnow()
        self.sensor.send_results(
            UptimeSensor,
            timestamp,
            [('default', 1.1)]
        )
        self.queue.put.assert_called_once_with({
            'datatype': float,
            'timestamp': timestamp,
            'config_id': 'config_id',
            'data': 1.1,
            'stream_name': 'default'
        })

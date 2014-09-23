# -*- coding: utf-8 -*-
'''
Tests for Agent's StorageManager.
'''
# TODO: Tests with real DB?

import multiprocessing
from mock import MagicMock, patch

from ..agent import StorageManager


class DummyProcess(multiprocessing.Process):
    '''
    Dummy process changing storage when run.
    '''
    def __init__(self, storage):
        super(DummyProcess, self).__init__()
        self.storage = storage

    def run(self):
        self.storage['test'] = 'value'


class TestStorageManager(object):
    '''
    StorageManager tests class.
    '''
    def setup(self):
        '''
        Creates sqlite mocks and StorageManager instance.
        '''
        # Attributes defined outside __init__
        # pylint: disable=W0201

        self.sqliteconn = MagicMock()
        self.cursor = MagicMock()
        self.sqliteconn.cursor.return_value = self.cursor
        self.patcher = patch('whmonit.client.agent.make_sqlite_conn')
        mock_get_conn = self.patcher.start()
        mock_get_conn.return_value = self.sqliteconn
        self.manager = StorageManager('')

    def teardown(self):
        '''
        Shuts down SyncManager.
        '''
        self.manager.manager.shutdown()
        self.patcher.stop()

    def test_get_storage_new(self):
        '''
        Should call on sqlite and produce new storage instance.
        '''
        self.cursor.fetchone.return_value = '{"test": "value"}'
        expected = {'test': 'value'}

        result = self.manager.get_storage('sensor+config')

        assert self.cursor.execute.called
        assert expected == dict(result)

    def test_get_storage_existing(self):
        '''
        Should return existing storage instance.
        '''
        # We use "normal" dict value here, because it doesn't really
        # matter for the test and proxy types are a bit cumbersome to create.
        self.manager.storages = {'sensor+config': {'test': 'value'}}
        expected = {'test': 'value'}

        result = self.manager.get_storage('sensor+config')

        assert not self.cursor.execute.called
        assert expected == result

    def test_shutdown(self):
        '''
        Should call on sqlite to commit all storages.
        '''
        self.manager.storages = {
            'sensor+config': {'test': 'value'},
            'sensor2+config': {'value': 'test'},
        }

        self.manager.shutdown()

        assert self.cursor.execute.call_count == 2
        assert self.sqliteconn.commit.called

    def test_multiprocess_update(self):
        '''
        Storage should get updated in main process when changed
        from a different one.
        '''
        storage = self.manager.get_storage('sensor+config')
        process = DummyProcess(storage)
        expected = {'test': 'value'}

        process.start()
        process.join()

        assert expected == dict(storage)

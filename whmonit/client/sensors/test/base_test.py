# -*- coding: utf-8 -*-
'''Sensors basic test.'''
from datetime import datetime
import pytest
from mock import Mock, patch
from jsonschema import ValidationError

from ..base import (
    AdvancedSensorBase,
    TaskSensorBase,
    InvalidDataError,
    InvalidSendResultsError,
)


class TestClassSensors(object):
    ''' Sensor test class'''
    # R0201: Method could be a function
    # pylint: disable=R0201

    def setup(self):
        '''Test setup.'''
        # W0201: Attributes 'sensor', 'send_data' defined outside __init__
        # pylint: disable=W0201
        self.send_data = Mock()

        class TestTaskSensor(TaskSensorBase):
            '''Dummy TaskSensor for tests.'''
            name = 'test_task_sensor'
            streams = {'default': {'type': float, 'description': 'Desc.'}}
            return_value = ('default', 47.)

            def do_run(self):
                return (self.return_value,)
        self.task_sensor_factory = TestTaskSensor

        class TestAdvancedSensor(AdvancedSensorBase):
            '''Dummy AdvancedSensor for tests.'''
            name = 'advanced_sensor'
            streams = {'default': {'type': float, 'description': 'Desc.'}}
            config_schema = {
                '$schema': 'http://json-schema.org/schema#',
                'type': 'object',
                'properties': {'data_count': {'type': 'integer'}},
                'required': ['data_count'],
                'additionalProperties': False
            }

            def do_run(self):
                for _ in xrange(self.config['data_count']):
                    self.send_results(datetime.utcnow(), (('default', 47.),))

        self.sensor = TestTaskSensor({'sampling_period': 10}, self.send_data, {})
        self.adv_sensor = TestAdvancedSensor({'data_count': 3}, self.send_data, {})

        self.datetime_patch = patch(
            'whmonit.client.sensors.base.datetime',
            Mock(wraps=datetime),
        )
        self.datetime_mock = self.datetime_patch.start()
        self.datetime_mock.utcnow.return_value = datetime(2006, 1, 2, 3, 4, 5)

    def teardown(self):
        '''
        Stops mocks.
        '''
        self.datetime_patch.stop()

    @pytest.mark.parametrize('schema,merged_schema', [
        (
            {
                'type': 'object',
                'properties': {'host': {'type': 'string'}},
                'additionalProperties': False
            },
            {
                '$schema': 'http://json-schema.org/schema#',
                'type': 'object',
                'properties': {
                    'host': {'type': 'string'},
                    'sampling_period': {'type': 'integer', 'default': 10, 'minimum': 1},
                    'memory_limit': {'type': 'integer', 'minimum': 1024},
                    'run_timeout': {'type': 'integer', 'minimum': 5, 'maximum': 3600}
                },
                'dependencies': {},
                'required': ['sampling_period'],
                'additionalProperties': False
            },
        ),
        (
            {
                '$schema': 'http://json-schema.org/schema#',
                'type': 'object',
                'properties': {
                    'host': {'type': 'string'},
                    'login': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['host'],
                'dependencies': {'login': ['password'], 'password': ['login']},
                'additionalProperties': False
            },
            {
                '$schema': 'http://json-schema.org/schema#',
                'type': 'object',
                'properties': {
                    'host': {'type': 'string'},
                    'login': {'type': 'string'},
                    'password': {'type': 'string'},
                    'sampling_period': {'type': 'integer', 'default': 10, 'minimum':1},
                    'memory_limit': {'type': 'integer', 'minimum': 1024},
                    'run_timeout': {'type': 'integer', 'minimum': 5, 'maximum': 3600}
                },
                'required': ['sampling_period', 'host'],
                'dependencies': {'login': ['password'], 'password': ['login']},
                'additionalProperties': False
            },
        )
    ])
    def test_merge_schemas(self, schema, merged_schema):
        '''
        Test if schemas merge correctly.
        '''

        class TestSensor(TaskSensorBase):
            '''Test Sensor.'''
            name = 'test_sensor'
            streams = {}
            config_schema = schema

            def do_run(self):
                return

        assert TestSensor.config_schema == merged_schema

    def test_invalid_send_results_param(self):
        '''
        Passing 'false' send_results should throw an existing exception.
        '''
        with pytest.raises(InvalidSendResultsError):
            self.task_sensor_factory({'sampling_period': 10}, None, {})

    def test_send_results(self):
        '''
        Send correct results.
        '''
        self.sensor.run()
        self.send_data.assert_called_once_with(
            datetime(2006, 1, 2, 3, 4, 5), (('default', 47),)
        )

    def test_advanced_sensor(self):
        '''
        Tests if a simple AdvanceSensor will periodicaly send data.
        '''
        try:
            self.adv_sensor.run()
        except AssertionError:
            pass
        assert self.send_data.call_count == 3

    def test_send_results_bad_stream(self):
        '''
        Send results with wrong stream name.
        '''
        self.sensor.return_value = ('badstream', 47.)
        with pytest.raises(InvalidDataError) as err:
            self.sensor.run()
        assert err.value.message.startswith('Sensor `')

    def test_send_results_bad_datatype(self):
        '''
        Send results with wrong data type.
        '''
        self.sensor.return_value = ('default', 'bad')
        with pytest.raises(InvalidDataError) as err:
            self.sensor.run()
        assert err.value.message.startswith('Datatype returned by sensor')

    def test_stream_bad_type(self):
        '''
        Send results, while stream's type not in PRIMITIVE_TYPE_REGISTERY.
        '''
        self.sensor.streams = {'default': {'type': list, 'description': 'Desc.'}}
        self.sensor.return_value = ('default', [])
        with pytest.raises(InvalidDataError) as err:
            self.sensor.run()
        assert err.value.message.startswith("Datatype <type 'list'> of stream")

    def test_bad_config_schema(self):
        '''
        Should report validation error to error stream and re-raise.
        '''
        with pytest.raises(ValidationError):
            self.task_sensor_factory(
                {'some': ['invalid', 'stuff']}, self.send_data, {}
            )
        self.send_data.assert_called_once_with(
            datetime(2006, 1, 2, 3, 4, 5), ((
                "error",
                "Error while merging schemas: config_schema in class "
                "`TestTaskSensor` should be valid against `meta_schema` "
                "`'sampling_period' is a required property`"),))

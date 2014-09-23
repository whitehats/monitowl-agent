'''
Implementation of simple JSON serialization mechanism.
'''

from __future__ import absolute_import

import json

from whmonit.common.time import datetime_to_milliseconds, milliseconds_to_datetime

from .base import TypeRegistrySerializationBase, DeserializationError


class JSONTypeRegistrySerializer(TypeRegistrySerializationBase):
    '''JSON Serializer implementation.'''

    # Most of the methods could be functions but we want to keep methods.
    # pylint: disable=R0201

    # `schema` is not always used but this is the method interface.
    # pylint: disable=W0613

    # Methods are named after types so can contains CamelCase.
    # pylint: disable=C0103

    # There is probably not much sense in documenting these methods with
    # docstrings.
    # pylint: disable=C0111

    # R0903: Too many public methods
    # pylint: disable=R0904

    signature = 1

    def serialize_bool(self, data):
        return json.dumps(data)

    def deserialize_bool(self, data, schema):
        return json.loads(data)

    def serialize_float(self, data):
        return json.dumps(data)

    def deserialize_float(self, data, schema):
        return json.loads(data)

    def serialize_str(self, data):
        return json.dumps(data)

    def deserialize_str(self, data, schema):
        return str(json.loads(data))

    def serialize_datetime(self, data):
        return str(datetime_to_milliseconds(data))

    def deserialize_datetime(self, data, schema):
        # TODO #704: Too short time ranges.
        # nanotime has different time range than python/c datetime so there
        # might be.
        # `datetime` has range as (1, 2038),
        # `nanotime` has range as (1970, 2554).
        return milliseconds_to_datetime(int(data))

    def serialize_TimeSeries(self, data):
        serialized = []
        for key, value in data.iteritems():
            serialized.append([self.serialize(key), self.serialize(value)])
        return json.dumps(serialized)

    def deserialize_TimeSeries(self, serialized_data, schema):
        # TODO #601: Optimize serialization/deserialization.
        # Current implementation is not pretty, it needs 2x memory of actual
        # data to deserialize it :(.

        expected_type = self.schema_to_type(schema)
        sub_schema = self._unwrap_series(schema)[0]

        value_deserializer = self._select_deserializer(expected_type.item_type)
        deserialized_data = json.loads(serialized_data)
        data = expected_type()

        if not isinstance(deserialized_data, list):
            raise DeserializationError()
        for item in deserialized_data:
            if not isinstance(item, list) or len(item) is not 2:
                raise DeserializationError()
            data.add(self.deserialize_datetime(item[0], 'datetime'),
                     value_deserializer(item[1], sub_schema))

        return data

    def serialize_IntervalSeries(self, data):
        serialized = [
            [self.serialize(key[0]), self.serialize(key[1]), self.serialize(value)]
            for key, value in data.iteritems()]
        return json.dumps(serialized)

    def deserialize_IntervalSeries(self, serialized_data, schema):
        # TODO #1408: Implement real serialization of IntervalSeries

        expected_type = self.schema_to_type(schema)
        sub_schema = self._unwrap_series(schema)[0]

        value_deserializer = self._select_deserializer(expected_type.item_type)
        deserialized_data = json.loads(serialized_data)
        data = expected_type()

        if not isinstance(deserialized_data, list):
            raise DeserializationError()
        for item in deserialized_data:
            if not isinstance(item, list) or len(item) != 3:
                raise DeserializationError()
            data.add(
                (self.deserialize_datetime(item[0], 'datetime'),
                 self.deserialize_datetime(item[1], 'datetime')),
                value_deserializer(item[2], sub_schema))

        return data

    def serialize_ID(self, data):
        return json.dumps(str(data))

    def deserialize_ID(self, data, schema):
        expected_type = self.schema_to_type(schema)
        return expected_type(str(json.loads(data)))

    def serialize_SensorName(self, data):
        return json.dumps(str(data))

    def deserialize_SensorName(self, data, schema):
        expected_type = self.schema_to_type(schema)
        return expected_type(str(json.loads(data))[:16])

    def serialize_LogDBConfigEntry(self, data):
        _dict = {
            "config_id": self.serialize(data.config_id),
            "target_id": self.serialize(data.target_id),
            "agent_id": self.serialize(data.agent_id),
            "sensor_name": self.serialize(data.sensor_name),
            "stream_name": self.serialize(data.stream_name),
            "timestamp": self.serialize(data.timestamp),
            "config": self.serialize(data.config)
        }
        return json.dumps(_dict)

    def deserialize_LogDBConfigEntry(self, data, schema):
        expected_type = self.schema_to_type(schema)
        _dict = json.loads(data)
        return expected_type(
            self.deserialize(_dict["config_id"], "ID"),
            self.deserialize(_dict["target_id"], "ID"),
            self.deserialize(_dict["agent_id"], "ID"),
            self.deserialize(_dict["sensor_name"], "SensorName"),
            self.deserialize(_dict["stream_name"], "StreamName"),
            self.deserialize(_dict["timestamp"], "datetime"),
            self.deserialize(_dict["config"], "SensorConfig")
        )

    def serialize_SensorConfig(self, data):
        return json.dumps(data)

    def deserialize_SensorConfig(self, data, schema):
        expected_type = self.schema_to_type(schema)
        return expected_type(json.loads(data))

    def serialize_StreamName(self, data):
        return json.dumps(str(data))

    def deserialize_StreamName(self, data, schema):
        expected_type = self.schema_to_type(schema)
        return expected_type(str(json.loads(data)))

    def serialize_AgentRequestChunk(self, data):
        _dict = {
            'config_id': self.serialize(data.config_id),
            'stream_name': self.serialize(data.stream_name),
            'timestamp': self.serialize(data.timestamp),
            'data': self.pack(data.data)
        }
        return json.dumps(_dict)

    def deserialize_AgentRequestChunk(self, data, schema):
        expected_type = self.schema_to_type(schema)
        _dict = json.loads(data)
        return expected_type(
            self.deserialize(_dict['config_id'], "ID"),
            self.deserialize(_dict['stream_name'], "StreamName"),
            self.deserialize(_dict['timestamp'], "datetime"),
            self.unpack(_dict['data'])
        )

    def serialize_AgentRequest(self, data):
        serialized = []
        for req in data:
            serialized.append(self.serialize(req))
        return json.dumps(serialized)

    def deserialize_AgentRequest(self, data, schema):
        _list = self.schema_to_type(schema)()
        for req in json.loads(data):
            _list.append(self.deserialize(req, 'AgentRequestChunk'))
        return _list

    def serialize_CertificateState(self, data):
        return json.dumps(str(data))

    def deserialize_CertificateState(self, data, schema):
        expected_type = self.schema_to_type(schema)
        return expected_type(str(json.loads(data)))

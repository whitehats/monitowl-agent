'''Serializer API tests.'''
import struct
import pytest

from whmonit.common.types import PrimitiveTypeRegistry
from ..base import (
    TypeRegistrySerializationBase,
    TypeNotSerializableError,
    NotUniqueTypeNameError,
)
from .helpers import SerializationBaseTestBase


class TestPrimitiveSerialization(SerializationBaseTestBase):
    '''Tests (de)serialization of primitive types.'''
    TYPE_REGISTRY = PrimitiveTypeRegistry()
    TYPE_REGISTRY.register_many((bool, str, float))
    ITEMS = (
        (True, bool, 'bool'),
        (False, bool, 'bool'),
        (3.0, float, 'float'),
        (0.0, float, 'float'),
        ('x', str, 'str'),
    )


def test_signature_implemented():
    '''Test signature self-checks of serializers.'''

    class FakeSerializer(TypeRegistrySerializationBase):
        'Fake'

    type_registry = PrimitiveTypeRegistry()
    type_registry.register_many((str, float))

    pytest.raises(AssertionError, FakeSerializer, type_registry)

    FakeSerializer.signature = 4499
    FakeSerializer(type_registry, False)


def test_primitives_coverage():
    ''' Verify, if serializer class has a test, that checks if serializer for
    every type in registry is implemented.  '''

    class FakeSerializer(TypeRegistrySerializationBase):
        'Fake'
        signature = 1234

    # too few public methods
    # pylint: disable=R0903
    class FakeType(object):
        'Fake'

    type_registry = PrimitiveTypeRegistry()
    type_registry.register(FakeType)

    pytest.raises(TypeNotSerializableError, FakeSerializer, type_registry)
    FakeSerializer.serialize_FakeType = lambda self, x, y: x

    pytest.raises(TypeNotSerializableError, FakeSerializer, type_registry)
    FakeSerializer.deserialize_FakeType = lambda self, x, y: x

    FakeSerializer(type_registry)  # if both serialize/deserialize are implemented
    del FakeSerializer.serialize_FakeType
    pytest.raises(TypeNotSerializableError, FakeSerializer, type_registry)


def test_non_unique_type_names():
    '''Test if that `TypeRegistry` has types with unique names. Names are used
    during serialization/deserialization.'''

    # There is no sense in writing docstrings here.
    # pylint: disable=C0111
    # Most methods from serializers could be functions but we do not want that.
    # pylint: disable=R0201
    # Schema may not always be used in deserialization.
    # pylint: disable=W0613
    # Method names with camel case.
    # pylint: disable=C0103
    class FakeSerializer(TypeRegistrySerializationBase):
        signature = 9999

        def serialize_FakeType(self, data):
            pass

        def deserialize_FakeType(self, data, schema):
            pass

    type1 = type('FakeType', (object,), {})
    type2 = type('FakeType', (object,), {})

    type_registry = PrimitiveTypeRegistry()
    type_registry.register_many((type1, type2))

    pytest.raises(NotUniqueTypeNameError, FakeSerializer, type_registry)


def test_pack_and_unpack_api():
    '''Test that we can `pack` and `unpack` data.
    Test pack protocol also.'''

    type1 = type('FakeType', (object,), {})

    # There is no sense in writing docstrings here.
    # pylint: disable=C0111
    # Most methods from serializers could be functions but we do not want that.
    # pylint: disable=R0201
    # `schema` may not always be used in deserialization.
    # pylint: disable=W0613
    # Method names with camel case.
    # pylint: disable=C0103
    class FakeSerializer(TypeRegistrySerializationBase):
        signature = 9999

        # Gap between serialize and deserialize should be checked in
        # serializer specific tests.
        def serialize_FakeType(self, data):
            return 'type1'

        def deserialize_FakeType(self, data, schema):
            return type1()

    type_registry = PrimitiveTypeRegistry()
    type_registry.register(type1)

    ser = FakeSerializer(type_registry)
    data = type1()
    schema = ser.data_to_schema(data)
    serialized = ser.serialize(data)

    packed = ser.pack(data)

    assert struct.pack('!H', ser.signature) in packed[:2]
    assert schema in packed[4:4 + len(schema)]
    assert serialized in packed[4 + len(schema):]

    unpacked = ser.unpack(packed)
    assert schema, data == unpacked

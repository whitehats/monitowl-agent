'''Tests for JSON Serialization mechanism.'''

from ...types import PrimitiveTypeRegistry
from ..json import JSONTypeRegistrySerializer
from .helpers import SerializationTestBase


class TestJSONSerializer(SerializationTestBase):
    '''Standard test suite for JSON Serializer.'''
    TYPE_REGISTRY = PrimitiveTypeRegistry
    serializer_class = JSONTypeRegistrySerializer

# -*- encoding: utf-8 -*-
'''
Registry to keep serializers together for easy access.
'''

import struct

from whmonit.common.error import Error
from whmonit.common.types import PRIMITIVE_TYPE_REGISTRY as TYPE_REGISTRY

from .base import TypeRegistrySerializationBase
from .json import JSONTypeRegistrySerializer


# E0710: Exception doesn't inherit from standard "Exception" class
# pylint: disable=E0710
class SerializerRegistryError(Error):
    # W0232: Class has no __init__ method
    # R0903: Too few public methods
    # pylint: disable=W0232, R0903
    ''' Base class for serializers registry errors. '''


class AlreadyRegisteredError(SerializerRegistryError):
    # W0232: Class has no __init__ method
    # R0903: Too few public methods
    # pylint: disable=W0232, R0903
    ''' This serializer has already been registered. '''
    params = 'serializer'
    text = 'The serializer you want to reregister is {serializer}.'


class SerializerRegistry(object):
    '''
    A registry of serializers. Allows to find all registered serializers
    by their signatures.

    It also provides methods to serialize / deserialize data using
    registered serializers by their signatures.
    '''

    def __init__(self):
        self.serializers = dict()

    def register(self, serializer):
        '''
        Register serializer. Raises an exception if trying to register
        a non-serializer object, or a serializer whose signature is already
        present in registry.

        :param serializer: Serializer instance
        :type serializer: Subclass of :obj:`TypeRegistrySerializationBase`

        :returns: ``None``
        :raises: :class:`AlreadyRegisteredError`
        :raises: :class:`TypeError`
        '''
        if not isinstance(serializer, TypeRegistrySerializationBase):
            raise TypeError("serializer is %r but it should be  %r" %
                            (type(serializer), TypeRegistrySerializationBase))
        if serializer.signature in self.serializers:
            raise AlreadyRegisteredError(serializer)
        self.serializers[serializer.signature] = serializer

    def serializer(self, signature=None, schema=None):
        '''
        Get serializer instance by signature or schema.
        If schema is set, it's being parsed to get signature, then
        serializer which such signature is returned.
        If signature is set, serializer with matching signature
        is returned.

        :param signature: Signature of serializer we want to get.
        :type signature: :obj:`int`

        :param schema: Schema from which we want to get signature.
        :type schema: :obj:`str`

        .. warning::

            At least one of params has to be provided.

        :returns: Proper serializer
        :rtype: :obj:`TypeRegistrySerializationBase`
        :raises: :class:`KeyError`
        :raises: :class:`ValueError`
        '''
        if schema:
            signature = struct.unpack('!H', schema[:2])[0]
        if signature:
            return self.serializers[signature]
        raise ValueError("Both `signature` and `schema` cannot be `None`")

    def __contains__(self, key):
        '''
        Check if serializer is registered.

        :param key: Serializer object or serializer signature.
        :type key: Instance of :obj:`TypeRegistrySerializationBase` or
                    :obj:`int`

        :returns: ``True`` if serializer is registered, ``False`` otherwise
        :rtype: :obj:`bool`
        :raises: :class:`TypeError`
        '''
        if isinstance(key, int):
            return key in self.serializers
        elif isinstance(key, TypeRegistrySerializationBase):
            return key.signature in self.serializers
        else:
            raise TypeError('Keys can only be integers.')

    def __getitem__(self, key):
        '''
        Implementation of container protocol (``obj[key]`` notation).

        :param key: Signature of serializer we want to get.
        :type key: :obj:`int`

        :returns: Instance of :obj:`TypeRegistrySerializationBase`
        :raises: :class:`KeyError`
        :raises: :class:`TypeError`
        '''
        if not isinstance(key, int):
            raise TypeError('Keys are integers which store '
                            'serializer signature.')
        return self.serializers[key]

    def unpack(self, data):
        '''
        Unpacks given data using serializer specified in schema of data.

        :param data: Packed data we want to unpack.
        :type data: :obj:`str`

        :returns: Unpacked data.
        :rtype: *Primitive* specified in ``schema`` of ``data``.

        :raises: :class:`KeyError`
        '''
        signature = struct.unpack('!H', data[:2])[0]
        return self.serializers[signature].unpack(data)

    def pack(self, signature, data):
        '''
        Packs given data using serializer specified by ``signature``.

        :param signature: Signature of serializer we want to use.
        :type signature: :obj:`int`

        :param data: Any *primitive* we want to pack.
        :type data: *primitive*

        :returns: Packed data.
        :rtype: :obj:`str`

        :raises: :class:`KeyError`
        '''
        return self.serializers[signature].pack(data)

    def serialize(self, signature, data):
        '''
        Serializes given data using serializer specified by ``signature``.

        :param signature: Signature of serializer we want to use.
        :type signature: :obj:`int`

        :param data: Any *primitive* we want to serialize.
        :type data: *primitive*

        :returns: Serialized data.
        :rtype: :obj:`str`

        :raises: :class:`KeyError`
        '''
        return self.serializers[signature].serialize(data)

    def deserialize(self, signature, data, schema):
        '''
        Deserializes given data using serializer specified in ``signature``.

        :param signature: Signature of serializer we want to use.
        :type signature: :obj:`int

        :param data: Serialized data we want to deserialize.
        :type data: :obj:`str`

        :param schema: Schema of type to which we are deserializing.
        :type schema: :obj:`str`

        :returns: Deserialized ``data``.
        :rtype: *Primitive* specified by schema.

        :raises: :class:`KeyError`
        '''
        return self.serializers[signature].deserialize(data, schema)


SERIALIZERS_REGISTRY = SerializerRegistry()
SERIALIZERS_REGISTRY.register(JSONTypeRegistrySerializer(TYPE_REGISTRY))

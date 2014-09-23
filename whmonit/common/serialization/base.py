'''
Serialization mechanism base
============================

This module contains base classes and exceptions for making serializers
of :class:`.TypeRegistry`'s types.

Background
----------

    :ref:`timeseries` and :ref:`primitives` are extensively used to represent
    data and are often exchanged by all system components.

    To keep data types organized :ref:`TypeRegistry` is used. To exchange data
    between components, [this] serialization mechanism is used.

Requirements:

    Most typical use cases:

        1. sending data over the network from :ref:`agents <agent>`
    to :ref:`collector`
        2. writing/reading data with :ref:`LogDB interface <LogDBBase>`
        3. sending data over the network from :ref:`webserver` to `webclient`

    Not every case has the same serialization requirements. For example in case
    (1) when :ref:`agents <agent>` are regular servers, speed is the most
    important factor, when :ref:`agents <agent>` are mobile phones, data
    compression is the most important.  In case (2) also the compression may be
    crucial, while in case (3) the expected data format is the key (JSON, XML, ..).

    To meet those requirements this serialization mechanism was introduced.

Requirements and assumptions
----------------------------

* Serialization mechanism must be backward compatibile!

  This requirement is needed to provide a way to deserialize older data with
  the same serializer.

  Examples:

  - agent sends cached data which was produced before updating the
  serialization mechanism

  - data in the database are serialized with one serializer and should be
  always readable

  If you want to break the compatibility just make new serialization mechanism.

* Serialization mechanism can serialize or deserialize (or both) all or
  some types registered with specific :ref:`TypeRegistry` instance (probably
  including :ref:`timeseries`).

* Serialization mechanism is extensible. If the new serialization format is
  needed, new implementation can be easily added (read more in
  :ref:`TypeRegistrySerializationBase documentation
  <TypeRegistrySerializationBase>`.

* Serialization mechanism must be able to make self-sufficient data
  packages which can be easily deserialized without additional information
  (those packages have to contain the data and the metadata needed by
  deserializer).

* Serialization always serializes/deserializes whole objects. No streaming
  support. Streamming support can be `faked` by fragmenting iterable objects.


'''
import struct

from whmonit.common.types import (NotASpecificTypeError,
                                  NotRegisteredError,
                                  NameNotRegisteredError)
from whmonit.common.error import Error, ArgumentTypeError
from whmonit.common.types import GenericContainer


class SerializerBaseError(Error):
    '''Base error for serialization mechanism exceptions.'''


class SerializationError(SerializerBaseError, RuntimeError):
    '''Base error for serialization actions.'''


# too many ancestors pylint says
# pylint: disable=R0901
class SerializationTypeError(SerializationError, TypeError):
    '''Result of serialization has wrong type.'''
    text = '''Serialization of `{data_type}` (with `{serializer_name}`)
    returned data with wrong type (serialized type is `{serialized_type}` but
    should be `{expected_type}`).'''
    params = 'data_type, serializer_name, serialized_type, expected_type'


# too many ancestors pylint says
# pylint: disable=R0901
class DeserializationError(SerializationError, RuntimeError):
    '''Base error for deserialization actions.'''


class DeserializationTypeError(DeserializationError, TypeError):
    '''Result of deserialization has wrong type.'''
    text = '''Deserialization (with `{deserializer_name}`) returned data with
    wrong type (deserialized data type is `{deserialized_type}` but should be
    `{expected_type}`).'''
    params = 'deserializer_name, deserialized_type, expected_type'


class TypeNotSerializableError(SerializerBaseError):
    '''Type is not serializable.'''
    text = '''There is no known method to serialize {type}.'''
    params = 'type'


class NotUniqueTypeNameError(SerializerBaseError):
    '''Type names collision.'''
    text = '''Several types ({types}) registered in the same TypeRegistry have
    the same names ({name}) so proper serializer cannot be chosen.'''
    params = 'types, name'


class InvalidSignatureError(DeserializationError):
    '''Invalid Serializer's signature.'''
    text = '''Current serializer ({serializer_instance}) has signature as
    `{serializer_signature}`, but data came with `{data_signature}` which
    means that probably it was serialized with another serializer. Cannot
    deserialize data.'''
    params = 'serializer_instance, serializer_signature, data_signature'


class TypeRegistrySerializationBase(object):
    '''Interface definition for :class:`.TypeRegistry` serialization mechanisms.

    .. note::

        To provide new serialization mechanism for a given :ref:`TypeRegistry`
        please read this section to know how serialization mechanism works.


    Implementation details:

        Serialization mechanism can serialize or deserialize :ref:`primitives`
        (only those ``primitives`` which are registered with :ref:`TypeRegistry`
         instance passed to serialization mechanism during initialization).

        Type names must be unique inside :ref:`TypeRegistry`. This requirement
        is needed while serializing (to auto-magically make serialized schemas
        for data) and while deserialization (to select proper serializer by
        ``name`` with python's ``__name__`` of that type).

        .. warning::

            As ``__name__`` is used to build schema, deserialization must be
            done against serialization mechanism bound to
            :class:`.TypeRegistry` with the same types (with the same type
            names) registered (precisely at least the same types has to be
            registered during deserialization and serialization).

        Serialization mechanism does not know about :ref:`primitive
        <primitives>` internal structure. Each :ref:`primitive <primitives>`
        type may have its own ``serialization`` / ``deserialization`` method
        implemented.  Examples:

            - for ``float`` methods like ``serialize_float`` and
            ``deserialize_float`` can be implemented.

        The only complex type is :meth:`TypeRegistry.TimeSeries` (complex type
        can nest other types within and serializer can automatically handle
        nesting).

        .. warning::

            Lists, tuples, dicts are not supported at this moment (you can
            serialize them as your own named structures but there is no way to
            write dynamic schema for nested lists, dicts etc.).

            If you want to serialize known structures, provide new, well
            described type (we call it :ref:`primitive <primitives>`), register
            it with :ref:`TypeRegistry` and write serialization methods for it.


    Definitions:

        Schema:

                String-based schema description.  In :class:`.TypeRegistry`
                serialization we want to know only what primitives are inside
                :meth:`.TimeSeries` classes. We do not need to model complex
                types, so schema is a string with simple description.
                Examples::

                    Schema 1: "float"
                    Schema 2: "PSTuple"
                    Schema 3: "TimeSeries(float)"
                    Schema 4: "TimeSeries(TimeSeries(float))"

        .. _serialization_package:
        Package:

            ``Package`` is a data package (list of bytes, `str` type in
            python2) containing serialization mechanism signature, schema and
            serialized data merged together. That package can be easily
            deserialized by the same serialization mechanism without additional
            data outside ``pack``.

        Signature:

            Signature is a unique identifier of a specific serialization
            mechanism implementation. This value is used in packing data into
            a ``pack``.  By reading ``signature`` proper deserializer can be
            used.

            .. warning::

                * This value must be unique across the project.

                * This value must NOT change in time.

                * If your serializer needs to be upgraded without backward
                  compatibility, make new serializer and choose new signature.


    Writing new serialization mechanism
    -----------------------------------

    * To make new serialization mechanism
      :class:`TypeRegistrySerializationBase` must be subclassed.

    * :attr:`signature` must be provided for that subclass.

    * For each ``primitive`` methods like ``serialize_<NAME>`` and
      ``deserialize_<NAME>`` may be implemented where ``<NAME>`` is the python's
      type name (``__name__``).

    * If :meth:`TypeRegistry.TimeSeries` also needs to be serialized you have
      to implement ``serialize_TimeSeries`` and ``deserialize_TimeSeries``.

    .. automethod:: __init__
    '''

    #: This value is a text representation of serialization mechanism implementation.
    #: It must be ``int`` (precisely 2-byte ``short int``) and unique
    #: across serialization mechanisms used in the project.
    #:
    #: This value must NOT change in time to make sure that
    #: the same serialization mechanism will be used for deserialization.
    #:
    #: This value must be overridden in subclasses.
    signature = NotImplemented

    def __init__(self, type_registry, types_coverage=True):
        '''
        :param type_registry: types of that registry are serialized
        :type type_registry: :class:`.TypeRegistry`
        :param types_coverage: check that serializers/deserializers are
            implemented for all types in `type_registry`. Check also that
            primitives has unique names across `TypeRegistry`.

        While creating instance of this class some additional checks are made:

            * whether :attr:`signature` is set
            * check if serializers are implemented for each type in `type_registry`
                (see :meth:`_check_types_coverage`, it can raise some exceptions)
        '''
        if self.signature is NotImplemented:
            raise AssertionError('Cannot determine serializer signature! Please implement it!')
        if not isinstance(self.signature, int):
            # TODO #801: make sure that `signature` is 2-bytes long at maximum.
            raise AssertionError('`{}` serializer signature has to be 2-byte short `int` '
                                 'but now it is instance of `{}`.'
                                 .format(self, type(self.signature)))

        self._type_registry = type_registry
        if types_coverage:
            self._check_types_coverage()

    def _check_types_coverage(self):
        '''
        Check if serializer class has methods to serialize/deserialize all
        `primitives` registered within :class:`.TypeRegistry`.

        Check also if all registered primitives have unique names (python's
        `__name__`), because types names are used to build schemas.

        :raises: * :class:`TypeNotSerializableError` when method for certain type
                   is not implemented.
                 * :class:`NotUniqueTypeNameError` when two types in
                   :class:`TypeRegistry` have the same name (`__name__`).

        This check is done only against `primitives` within :class:`.TypeRegistry'.
        '''
        primitives = {}
        for primitive in self._type_registry.primitives:
            # Check whether type names are unique.
            if primitive.__name__ in primitives:
                raise NotUniqueTypeNameError(', '.join((str(primitive),
                                                        str(primitives[primitive.__name__]))),
                                             primitive.__name__)
            primitives[primitive.__name__] = primitive

            # Check if serialization/deserialization method for that
            # type exists.
            self._select_serializer(primitive)
            self._select_deserializer(primitive)

    def type_to_schema(self, type_):
        '''Return a string representation of a given `type_`. Works only for
        types registered in :class:`TypeRegistry` to which this serializer is
        bound.'''

        if issubclass(type_, GenericContainer) or type_ in self._type_registry.primitives:
            return type_.__name__.replace('<', '(').replace('>', ')')
        else:
            raise NotASpecificTypeError(type, None)

    def data_to_schema(self, data):
        '''Does the same as :meth:`type_to_schema` but for data instances rather
        than classes/types.'''
        return self.type_to_schema(type(data))

    def schema_to_type(self, schema):
        '''Returns a type which string representation is by `schema`. Currently
        handles only types registered in :class:`TypeRegistry`.

        :param schema: type's text representation
        :type schema: basestring
        :returns: type
        :raises: :class:`ArgumentTypeError` if `schema` is not `basestring`,
                :class:`NameNotRegisteredError` if `type` for `schema` is not
                registered in :class:`TypeRegistry`.
        '''
        if not isinstance(schema, basestring):
            raise ArgumentTypeError('schema', type(schema), 'basestring')

        if self._unwrap_series(schema):
            # W0633: Unpacking non-sequence
            # pylint: disable=W0633
            subschema, series = self._unwrap_series(schema)
            return series(self.schema_to_type(subschema))

        elif schema in (type_.__name__ for type_ in self._type_registry.primitives):
            primitives_map = {type_.__name__: type_ for type_ in self._type_registry.primitives}
            return primitives_map[schema]

        else:
            raise NameNotRegisteredError(schema)

    def _unwrap_series(self, schema):
        '''Handle TimeSeries nesting (unwrapping) from schema.'''
        if schema.startswith('TimeSeries(') and schema.endswith(')'):
            return (schema[11:-1], self._type_registry.TimeSeries)
        if schema.startswith('TimeSeries<') and schema.endswith('>'):
            return (schema[11:-1], self._type_registry.TimeSeries)
        if schema.startswith('IntervalSeries(') and schema.endswith(')'):
            return (schema[15:-1], self._type_registry.IntervalSeries)
        if schema.startswith('IntervalSeries<') and schema.endswith('>'):
            return (schema[15:-1], self._type_registry.IntervalSeries)
        return None

    def _select_serializer(self, type_, method_name='serialize_{type_name}'):
        '''Returns method of the same class instance which can be used
        to serialize `type_`.

        :param type_: type you want to serialize
        :param method_name: method name signature

        :raises: :class:`NotRegisteredError` if `type_` is not registered within
            :class:`TypeRegistry`, :class:`TypeNotSerializableError` if there
            is no method which name match `method_name` formated with `type_` name.
        '''
        if type_ not in self._type_registry:
            raise NotRegisteredError(type_)
        elif issubclass(type_, GenericContainer):
            type_name = type_.__name__[:type_.__name__.find('<')]
            name = method_name.format(type_name=type_name)
        else:
            name = method_name.format(type_name=type_.__name__)

        if hasattr(self, name) and callable(getattr(self, name)):
            return getattr(self, name)
        raise TypeNotSerializableError(type_)

    def _select_deserializer(self, type_):
        '''See :meth:`_select_serializer`.'''
        return self._select_serializer(type_, method_name='deserialize_{type_name}')

    def serialize(self, data):
        '''Serialize the data with automatic schema detection.

        :param data: data of type registered with :class:`TypeRegistry`
        :returns: serialized data
        :rtype: str
        :raises: :class:`SerializationTypeError` is raised if data returned
            by serialization methods is not `str`.
        '''
        serializer = self._select_serializer(type(data))
        result = serializer(data)

        if not isinstance(result, str):
            raise SerializationTypeError(type(data), serializer, type(result), str(str))
        return result

    def deserialize(self, serialized_data, schema):
        '''Deserialize data using ``schema``.

        :param data: serialized data
        :type data: str
        :param schema: string based schema
        :type schema: str

        :returns: data
        :raises: :class:`DeserializationError` if deserialized data is not
            type defined by `schema`.
        '''
        expected_type = self.schema_to_type(schema)
        deserializer = self._select_deserializer(expected_type)
        result = deserializer(serialized_data, schema)

        if not isinstance(result, expected_type):
            raise DeserializationTypeError(deserializer, type(result), expected_type)
        return result

    def pack(self, data):
        ''' This method produces self-sufficient :ref:`data package
        <serialization_package>` of serialized data which can be easily
        deserialized without additional information.

        :returns: str

        .. seealso::

            :ref:`More about data packages. <serialization_package>`
        '''
        schema = self.data_to_schema(data)
        sdata = self.serialize(data)
        struct_schema = '!HH{:d}s{:d}s'.format(len(schema),
                                               len(sdata))
        return struct.pack(struct_schema, int(self.signature), len(schema),
                           schema, self.serialize(data))

    def unpack(self, data):
        ''' Gets binary ``data``, checks if it contains data that can be
        deserialized (signature check). If ``data`` can be deserialized,
        returns schema and deserialized data.

        :returns: schema, data
        :raises: InvalidSignatureError
        '''
        packed_signature = struct.pack('!H', self.signature)
        data_signature = data[:2]

        if packed_signature != data_signature:
            raise InvalidSignatureError(self, packed_signature, data_signature)

        packed_schema_len = struct.unpack('!H', data[2:4])[0]
        packed_schema = struct.unpack('!{:d}s'.format(packed_schema_len),
                                      data[4:4 + packed_schema_len])[0]

        return self.deserialize(data[4 + packed_schema_len:], packed_schema)

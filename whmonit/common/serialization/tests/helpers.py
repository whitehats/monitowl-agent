'''
Test suite for serializer classes.
'''

import sys
from random import Random
from datetime import datetime

import pytest
import random_words

from ...types import NotRegisteredError, NameNotRegisteredError
from ..base import (
    TypeRegistrySerializationBase,
    TypeNotSerializableError,
)


class SerializationBaseTestBase(object):
    '''
    Fixture-style object for testing base serialization API.

    Subclasses should assign proper values for:
    `TYPE_REGISTRY` - a PrimitiveTypeRegistry or it's subclass,
    `ITEMS` - list of tuples in form (value, type, type string).
              Those will become tests parameters.

    Note that the fixture itself does not register any types,
    so you might want to do TYPE_REGISTRY.register(...) as well.
    '''
    # Methods could be functions.
    # pylint: disable=R0201

    TYPE_REGISTRY = NotImplemented
    ITEMS = []

    @classmethod
    def generate_data(cls):
        '''
        Generates test data.

        Returned data is a list of dicts in form {attribute_name: value}.
        Same values might be returned multiple times under different
        attribute_name for the sake of meaningful attribute names in
        tests definitions.
        '''

        # Missing docstring.
        # Method could be a function.
        # Unused argument `schema`.
        # pylint: disable=C0111,R0201,W0613
        class FakeSerializer(TypeRegistrySerializationBase):
            signature = 51239

            def serialize_bool(self, data):
                return data

            def deserialize_bool(self, data, schema):
                return data

            def serialize_str(self, data):
                return data

            def deserialize_str(self, data, schema):
                return data

            def serialize_float(self, data):
                return data

            def deserialize_float(self, data, schema):
                return data

        serializer = FakeSerializer(cls.TYPE_REGISTRY)

        return [{
            'serializer': serializer,
            'input_data': item[0],
            'input_type': item[1],
            'expected_schema': item[2],
            'input_schema': item[2],
            'expected_type': item[1],
        } for item in cls.ITEMS]

    def pytest_generate_tests(self, metafunc):
        '''Parametrizes tests based on current ITEMS value.'''
        params = [
            [item[argname] for argname in metafunc.fixturenames]
            for item in metafunc.cls.generate_data()
        ]

        metafunc.parametrize(metafunc.fixturenames, params)

    def test_type_to_schema(self, serializer, input_type, expected_schema):
        '''Test serializing schema from type.'''
        assert serializer.type_to_schema(input_type) == expected_schema

    def test_data_to_schema(self, serializer, input_data, input_type, expected_schema):
        '''Test serializing schema from data type.'''
        data_schema = serializer.data_to_schema(input_data)
        type_schema1 = serializer.type_to_schema(type(input_data))
        type_schema2 = serializer.type_to_schema(input_type)

        assert data_schema == type_schema1
        assert type_schema1 == type_schema2
        assert type_schema2 == expected_schema

    def test_schema_to_type(self, serializer, input_schema, expected_type):
        '''Test deserialization of schema.'''
        assert serializer.schema_to_type(input_schema) == expected_type


class SerializationTestBase(object):
    '''Test Suite for every `TypeRegistrySerializationBase` implementation.

    Serializers test suites should inherit from this class
    and assing proper values for:
    `TYPE_REGISTRY` - a PrimitiveTypeRegistry subclass definition,
    `serializer_class` - class to test.
    This way standard test suite will be provided for serializer.

    If you want to extend test suite, for example test more types than a few
    standard types or you want to set more test data for test cases please
    check :meth:`pytest_generate_tests` method first!

    If you want to write new test, you can use several `pytest magical` method
    arguments called `fixtures` (`fixtures` are done in `pytest_generate_tests`
    in this module). The list of arguments are described in
    :meth:`pytest_generate_tests`.  '''

    # Too long method names.
    # Method could be a function.
    # pylint: disable=C0103,R0201

    TYPE_REGISTRY = NotImplemented
    serializer_class = NotImplemented

    @classmethod
    def setup_class(cls):
        '''Test Suite validity check.'''
        if cls.serializer_class is NotImplemented:
            module = sys.modules[cls.__module__]
            raise AssertionError('`serializer_class` attribute is missing in `{cls}` test class. '
                                 'Please fix test in `{module}` (in file `{file}`)'.format(
                                 cls=cls, module=module.__name__, file=module.__file__))

    def pytest_generate_tests(self, metafunc):
        '''
         If test (method) uses one or more arguments which we treat like
         `pytest fixtures`, run whole machinery to make dynamic objects for
         tests.

         Supported fixtures which do not parametrize the test:

             * type_registry - TypeRegistry instance
             * serializer - serializer instance

         Supported fixtures which parametrize test:

             * serializer_dependent_data
             * serializer_independent_data
             * serializer_data == serializer_dependent_data +
                                  serializer_independent_data

        If you use `pytest.fixtures` (read about them before writing tests)
        which parametrize test it works like ``pytest.mark.parametrize``.

        It is not allowed to mix `fixtures` which parametrize the test with
        those which do not parametrize the test.

        Available fixtures which parametrize tests:

            `serializer_dependent_data` will produce dictionaries
            serializer-aware data for tests which test serializer
            implementation. Dictionaries have items like:

                * `serializer` - serializer instance
                * `type_registry` - TypeRegistry instance
                * `data` - python object to serialize
                * `data_type` - type of python object
                * `serialized_schema` - string with schema
                * `serialized_data` - string with serialized object

            `serializer_independent_data` will produce dictionaries which does
            not contain serializer-specific data. It is good for testing
            serialization API.  `serialize_independent_data` contains the same
            keys in dictionary like `serializer_dependent_data`, except that
            `serialized_data` key is set to `None`.

            `serializer_data` contains merged data from `dependent` and
            `independent` data (lists of test data are chained, so test will be
            `called` for each example from both sets). You can use it only with
            tests which are aware that input data may be serializer dependent
            or independent or with serializer independent tests. Be careful
            with that.


            Implementation details:

                * TypeRegistry and Serializer instances are created:

                    :meth:`generate_type_registry_and_serializer`

                * Generate data for fixtures:

                    :meth:`generate_serializer_independent_data` and
                    :meth:`generate_serializer_dependent_data`

                * Run test.

            You can override TypeRegistry and Serializer creation mechanism:

                * by overriding TypeRegistry and Serializer creation method
                  (:meth:`generate_type_registry_and_serializer`),

                * by overriding data creation methods
                  (:meth:`generate_serializer_*_data`).


            .. warning::

                While adding own testing data by overriding
                :meth:`generate_serializer_*_data` do not forget to call
                ``super(<CLS>, self).generate_serializer_*_data`` to join your
                test cases to existing test cases instead of overriding it.

            '''
        # This method is too complicated (too many branches).
        # pylint: disable=R0912

        parametrization_args = set(('serializer_dependent_data',
                                    'serializer_independent_data',
                                    'serializer_data')).intersection(metafunc.funcargnames)
        non_parametrization_args = set(('type_registry',
                                        'serializer')).intersection(metafunc.funcargnames)

        # Call test which does not need parametrization.
        if not parametrization_args and not non_parametrization_args:
            return metafunc.addcall()

        if len(parametrization_args) > 1:
            raise AssertionError('You cannot mix `serializer_independent_data` and '
                                 '`serializer_dependent_data` and `serialized_data` in test `{}`.'.
                                 format(metafunc.function))
        if parametrization_args and non_parametrization_args:
            raise AssertionError('You cannot use parametrization arguments together with '
                                 'non-parametrization ones in test `{}`.'.format(metafunc.function))

        type_registry, serializer = self.generate_type_registry_and_serializer()

        # Run test one time and pass required fixtures/arguments to it
        # (fixtures which does not parametrize the test).
        if non_parametrization_args and not parametrization_args:
            funcargs = {}
            if 'type_registry' in metafunc.funcargnames:
                funcargs['type_registry'] = type_registry
            if 'serializer' in metafunc.funcargnames:
                funcargs['serializer'] = serializer
            return metafunc.addcall(funcargs=funcargs,
                                    id='-'.join(str(x.__class__.__name__)
                                                for x in funcargs.itervalues()))

        def fix_args_dictionary(args):
            'Fix keys in test data dictionaries.'
            if not isinstance(args, dict):
                raise AssertionError('`generate_serialized_*_data` methods have to return '
                                     'iterable of dicts! Read the documentation.')
            if len(set(('data', 'serialized_schema', 'type_registry', 'serializer')).
               intersection(args)) < 4:
                raise AssertionError('`generate_serialized_*_data` methods have to provide at '
                                     'least `data`, `serialized_schema`, `type_registry` and '
                                     '`serializer` keys')
            if not 'data_type' in args:
                args['data_type'] = type(args['data'])
            if not 'serialized_data' in args:
                args['serialized_data'] = None
            return args

        parametrization_arg_name = tuple(parametrization_args)[0]

        test_data_no = 0

        def addcall(args, test_data_no):
            '''Add test call with test data bound.'''
            metafunc.addcall(funcargs={parametrization_arg_name: fix_args_dictionary(args)},
                             id='%s-%s-%s-%s' % (str(args['serializer'].__class__.__name__),
                                                 str(args['serialized_schema']),

                                                 str(args['serialized_data'][:30])
                                                 if args['serialized_data'] else
                                                 '',

                                                 str(test_data_no)))

        if parametrization_arg_name in ('serializer_independent_data', 'serializer_data'):
            for funcargs in self.generate_serializer_independent_data(type_registry, serializer):
                addcall(funcargs, test_data_no)
                test_data_no += 1

        if parametrization_arg_name in ('serializer_dependent_data', 'serializer_data'):
            for funcargs in self.generate_serializer_dependent_data(type_registry, serializer):
                addcall(funcargs, test_data_no)
                test_data_no += 1

    def generate_type_registry_and_serializer(self):
        '''Make TypeRegistry instance with basic types, make also serializer
        bound to that TypeRegistry.'''
        type_registry = self.TYPE_REGISTRY()
        type_registry.register_many([str, float, datetime])

        serializer = self.serializer_class(type_registry)

        return type_registry, serializer

    def generate_serializer_independent_data(self, type_registry, serializer):
        '''Make test data without serialized representation.'''
        random = Random(9955)

        for _ in xrange(30):
            yield {
                'type_registry': type_registry,
                'serializer': serializer,
                'data': random.uniform(-1000, 1000),
                'serialized_schema': 'float',
            }

        random_sentences = random_words.LoremIpsum()

        for _ in xrange(30):
            yield {
                'type_registry': type_registry,
                'serializer': serializer,
                'data': str(random_sentences.get_sentence()),
                'serialized_schema': 'str',
            }

    # unused arguments (in target implementation can be used probably)
    # pylint: disable=W0613
    def generate_serializer_dependent_data(self, type_registry, serializer):
        '''Override this method to produce serializer specific test data.'''
        return []

    def test_schemas(self, serializer_independent_data):
        '''Test schema serialization mechanism.'''

        data = serializer_independent_data
        serializer = data['serializer']

        schema = serializer.type_to_schema(type(data['data']))
        data_schema = serializer.data_to_schema(data['data'])

        # Check if schema serialization is correct.
        assert schema == data_schema == data['serialized_schema']
        assert isinstance(schema, str)

        # Check if schema deserialization is correct.
        assert serializer.schema_to_type(schema) == \
            serializer.schema_to_type(data_schema) == \
            serializer.schema_to_type(data['serialized_schema']) == \
            data['data_type']

        assert isinstance(data['data'], serializer.schema_to_type(schema))

    def test_unregistered_type(self, serializer):
        '''
        Test whether error will be raised if we try
        to serialize unregistered type.
        '''

        with pytest.raises(NameNotRegisteredError):
            serializer.schema_to_type('I never registered that type :)')

    def test_serialize_api(self, serializer_data):
        '''Test if serialized object is a string.'''

        data = serializer_data
        assert isinstance(data['serializer'].serialize(data['data']), str)

    def test_serialize_and_deserialize_api(self, serializer_data):
        '''Test simple serialization and deserialization, check if the data
        before serialization and after deserialization are equal.'''

        data = serializer_data
        serializer = data['serializer']

        serialized = serializer.serialize(data['data'])
        schema = serializer.data_to_schema(data['data'])

        assert isinstance(serialized, str)
        assert isinstance(schema, str)

        assert schema == data['serialized_schema']
        if data['serialized_data']:
            assert serialized == data['serialized_data']

        deserialized = serializer.deserialize(serialized, schema)
        assert deserialized == data['data']

    def test_serializer_errors(self):
        '''Test internal serializer checks.'''

        type_reg = self.TYPE_REGISTRY()

        # Serializer is instantiated before registering new type to TypeRegistry
        # to check if serializer does not cache it in strange way.
        serializer = self.serializer_class(type_reg)

        my_type = type('my_unique_type_1775', (), {})
        my_type_not_registered = type('my_unique_type_1775_not_registered', (), {})

        type_reg.register(float)
        type_reg.register(my_type)

        # Self checks.
        assert my_type in type_reg

        # Type is registered but serialization method is not implemented.
        with pytest.raises(TypeNotSerializableError):
            serializer.serialize(my_type())

        # Type is not registered.
        with pytest.raises(NotRegisteredError):
            serializer.serialize(my_type_not_registered())

    def test_pack_and_unpack_api(self, serializer_independent_data):
        '''Try to pack and unpack data.'''

        ser = serializer_independent_data['serializer']

        assert serializer_independent_data['data'] == \
            ser.unpack(ser.pack(serializer_independent_data['data']))

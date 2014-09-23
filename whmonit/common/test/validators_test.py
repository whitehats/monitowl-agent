# -*- coding: utf-8 -*-
'''
Tests for custom validators.
'''

import jsonschema
import pytest

from .. import validators


class TestValidatorWithDefault(object):
    '''
    Tests for ValidatorWithDefault.
    '''
    # Method could be a function
    # pylint: disable=R0201

    @pytest.mark.parametrize(('schema', 'data', 'expected'), [
        ({
            'type': 'object',
            'properties': {
                'test': {
                    'type': 'integer',
                    'default': 10,
                },
            },
        }, {}, {'test': 10}),
        ({
            'type': 'object',
            'properties': {
                'test': {
                    'type': 'integer',
                },
            },
        }, {}, {}),
        ({
            'oneOf': [
                {
                    'type': 'object',
                    'properties': {
                        'test1': {'type': 'string', 'enum': ['a']},
                        'test2': {'type': 'string', 'default': 'z'},
                    },
                    'required': ['test1'],
                    'additionalProperties': False,
                },
                {
                    'type': 'object',
                    'properties': {
                        'test1': {'type': 'string', 'enum': ['b']},
                    },
                    'required': ['test1'],
                    'additionalProperties': False,
                }
            ]
        }, {'test1': 'b'}, {'test1': 'b'})
    ])
    def test_success(self, schema, data, expected):
        '''
        Default values should be substituted when specified.
        '''
        validator = validators.ValidatorWithDefault(schema)

        validator.validate(data)  # It validates in place

        assert expected == data

    def test_type_failure(self):
        '''
        Default value of wrong type should not be substituted.
        '''
        schema = {
            'type': 'object',
            'properties': {
                'test': {'type': 'integer', 'default': 'fail'},
            },
        }
        validator = validators.ValidatorWithDefault(schema)

        data = {}

        with pytest.raises(jsonschema.ValidationError) as exc:
            validator.validate(data)

        assert exc.value.message == "'fail' is not of type 'integer'"
        assert {} == data

    def test_required_corner_case(self):
        '''
        When required property is not found,
        defaults should not be substituted.

        Corner case for validators using 'oneOf' and similar.
        '''
        schema = {
            'oneOf': [
                {
                    'type': 'object',
                    'properties': {
                        'test1': {'type': 'string', 'enum': ['a']},
                        'test2': {'type': 'string', 'default': 'z'},
                    },
                    'required': ['test1'],
                    'additionalProperties': False,
                },
                {
                    'type': 'object',
                    'properties': {
                        'test1': {'type': 'string', 'enum': ['b']},
                    },
                    'required': ['test1'],
                    'additionalProperties': False,
                }
            ]
        }
        validator = validators.ValidatorWithDefault(schema)

        data = {}

        with pytest.raises(jsonschema.ValidationError) as exc:
            validator.validate(data)

        assert exc.value.message == "{} is not valid under any of the given schemas"
        assert {} == data


class TestValidatorWithUniqueItems(object):
    '''Tests for ValidatorWithUniqueItems'''
    # Method could be a function
    # pylint: disable=R0201

    @staticmethod
    def generate_schema(key):
        '''
        Substitute 'uniqueKey' value with given one and return schema.
        '''
        return {
            '$schema': 'http://json-schema.org/schema#',
            'type': 'object',
            'properties': {
                'children': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/child',
                        'uniqueKey': key
                    }
                },
            },
            'definitions': {
                'child': {
                    'properties': {
                        'key1': {
                            'type': 'string'
                        },
                        'key2': {
                            'type': 'string'
                        }
                    }
                }
            },
            'required': ['children'],
            'additionalProperties': False
        }

    @pytest.mark.parametrize(('key', 'data'), [
        ('key1', {'children': [
            {'key1': 'val1.1', 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 'common'}
        ]}),
        (['key1', 'key2'], {'children': [
            {'key1': 'val1.1', 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 'common'},
            {'key1': 'common', 'key2': 'val1.2'},
            {'key1': 'common', 'key2': 'val2.2'}
        ]}),
        ('key2', {'children': [
            {'key1': 'common', 'key2': 'val1.2'},
            {'key1': 'common', 'key2': 'val2.2'}
        ]})
    ])
    def test_valid_data(self, key, data):
        '''
        ValidatorWithUniqueItems accepts input where children' properties have
        unique values for specified keys.
        '''
        val = validators.ValidatorWithUniqueItems(
            TestValidatorWithUniqueItems.generate_schema(key)
        )
        val.validate(data)

    @pytest.mark.parametrize(('key', 'data'), [
        ('key1', {'children': [
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'}
        ]}),
        ('key1', {'children': [
            {'key1': 'common', 'key2': 'val1.2'},
            {'key1': 'common', 'key2': 'val2.2'}
        ]}),
        (['key1', 'key2'], {'children': [
            {'key1': 'val1.1', 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'val1.2'},
            {'key1': 'common', 'key2': 'val2.2'}
        ]}),
        ('key2', {'children': [
            {'key1': 'val1.1', 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 'common'}
        ]}),
        ('key2', {'children': [
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'}
        ]})
    ])
    def test_invalid_data(self, key, data):
        '''
        Test that ValidatorWithUniqueItems raises ValidationError on duplicate
        values for given key.
        '''
        val = validators.ValidatorWithUniqueItems(
            TestValidatorWithUniqueItems.generate_schema(key)
        )
        with pytest.raises(jsonschema.ValidationError) as exc:
            val.validate(data)

        assert exc.value.message == 'Duplicate value `{}` for key `{}`.'.format(
            ('common', 'common') if isinstance(key, list) else 'common',
            key
        )

    @pytest.mark.parametrize(('key', 'data'), [
        ('key1', {'children': [
            {'key1': 2.718281, 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 2.718281}
        ]}),
        (['key1', 'key2'], {'children': [
            {'key1': 2.718281, 'key2': 'common'},
        ]}),
        (['key1', 'key2'], {'children': [
            {'key1': 'val2.1', 'key2': 2.718281},
        ]}),
        (['key1', 'key2'], {'children': [
            {'key1': 2.718281, 'key2': 2.718281},
        ]}),
    ])
    def test_that_standard_validation_occurs(self, key, data):
        '''
        Test that ValidatorWithUniqueItems runs "standard" jsonschema validators
        appart from uniqueness.
        '''
        # C0103: Invalid method name
        # pylint:disable=C0103
        val = validators.ValidatorWithUniqueItems(
            TestValidatorWithUniqueItems.generate_schema(key)
        )
        with pytest.raises(jsonschema.ValidationError) as exc:
            val.validate(data)
        assert exc.value.message == "2.718281 is not of type 'string'"

    @pytest.mark.parametrize(('key', 'data'), [
        ('key1', {'children': [
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'}
        ]}),
        ('key1', {'children': [
            {'key1': 'common', 'key2': 'val1.2'},
            {'key1': 'common', 'key2': 'val2.2'}
        ]}),
        (['key1', 'key2'], {'children': [
            {'key1': 'val1.1', 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'val1.2'},
            {'key1': 'common', 'key2': 'val2.2'}
        ]}),
        ('key2', {'children': [
            {'key1': 'val1.1', 'key2': 'common'},
            {'key1': 'val2.1', 'key2': 'common'}
        ]}),
        ('key2', {'children': [
            {'key1': 'common', 'key2': 'common'},
            {'key1': 'common', 'key2': 'common'}
        ]})
    ])
    def test_that_no_uniquekey_causes_no_validation(self, key, data):
        '''
        Test that ValidatorWithUniqueItems performs no uniqueness validation
        when no `uniqueKey` key given.
        '''
        # C0103: Invalid method name
        # pylint:disable=C0103
        schema = TestValidatorWithUniqueItems.generate_schema(key)
        del schema['properties']['children']['items']['uniqueKey']
        val = validators.ValidatorWithUniqueItems(schema)
        val.validate(data)

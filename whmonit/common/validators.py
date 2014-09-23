# -*- coding: utf-8 -*-
'''
Custom JSONSchema validators.
'''

from jsonschema import Draft4Validator, validators
from jsonschema.exceptions import ValidationError


def extend_with_default(validator_class):
    '''
    Factory function for validator with 'default' values substitution.
    '''
    validate_props = validator_class.VALIDATORS["properties"]
    validate_required = validator_class.VALIDATORS["required"]
    validate_type = validator_class.VALIDATORS["type"]

    def set_default(validator, props, instance, schema):
        '''
        Substitutes default value in a validating object instance.
        '''
        required = schema.get("required", [])

        valid = True
        for err in validate_required(validator, required, instance, schema):
            valid = False
            yield err
        for err in validate_props(validator, props, instance, schema):
            valid = False
            yield err

        for prop, subschema in props.iteritems():
            if "default" in subschema:
                typ = subschema["type"]
                default = subschema["default"]
                for err in validate_type(validator, typ, default, None):
                    valid = False
                    yield err
                if valid:
                    instance.setdefault(prop, default)

    return validators.extend(validator_class, {"properties": set_default})


ValidatorWithDefault = extend_with_default(Draft4Validator)


def unique_by_key(validator_class):
    '''
    Factory function for validator with 'uniqueKey' check for objects array.
    '''
    validate_items = validator_class.VALIDATORS["items"]

    def unique_keys(validator, items, instance, schema):
        '''
        Checks for duplicate objects in array.
        '''
        for err in validate_items(validator, items, instance, schema):
            yield err
        if 'uniqueKey' not in items:
            return

        uniq_key = items['uniqueKey']
        keys_set = set()
        if validator.is_type(uniq_key, 'array'):
            get = lambda d: tuple(d.get(k, None) for k in uniq_key)
        else:
            get = lambda d: d.get(uniq_key, None)
        for i in instance:
            val = get(i)
            if val in keys_set:
                yield ValidationError(
                    'Duplicate value `{}` for key `{}`.'
                    .format(val, uniq_key)
                )
            keys_set.add(val)

    return validators.extend(validator_class, {'items': unique_keys})


ValidatorWithUniqueItems = unique_by_key(Draft4Validator)

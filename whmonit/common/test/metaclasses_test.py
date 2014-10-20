# -*- coding: utf-8 -*-
'''
Test metaclasses.
'''
from abc import abstractproperty

import pytest
from .. import metaclasses


class CustomMeta(metaclasses.BaseCheckMeta):
    '''Test metaclass'''
    @staticmethod
    def check_has_name(dct, **dummy):
        '''
        Check if class has `name` defined.
        '''
        if 'name' not in dct:
            yield metaclasses.CheckException('Should have `name`.')

    @staticmethod
    def check_knows_the_answer(dct, **dummy):
        '''
        Check if class has `answer` set to 42
        '''
        if 'answer' not in dct:
            yield metaclasses.CheckException('Should have `answer`.')
        elif dct['answer'] != 42:
            yield metaclasses.CheckException('Should know correct `answer`.')


class TestCheckMetaclasses(object):
    '''Metaclasses check test'''
    # R0201: Method could be a function
    # pylint: disable=R0201

    def test_both_checks_fails(self):
        '''Test if both checks fail and both are yielded.'''
        with pytest.raises(metaclasses.InvalidClassError) as err:
            class CustomClass(object):
                '''Test class failing checks.'''
                # R0903: Too few public methods
                # W0612: Unused variable
                # pylint: disable=R0903,W0612
                __metaclass__ = CustomMeta

        assert len(err.value.env['check_errors']) == 2

    def test_checks_pass(self):
        '''Check if proper class can pass checks.'''
        class CustomClass(object):
            '''Test class passing checks.'''
            # R0903: Too few public methods
            # W0612: Unsused variable
            # pylint: disable=R0903,W0612
            __metaclass__ = CustomMeta
            name = 'My_name'
            answer = 42

    def test_abstract_property(self):
        '''
        Check if class that does not override
        abstractproperties can't be instantiated.
        '''
        class CustomAbstractClass(object):
            '''Test abstract class.'''
            # R0903: Too few public methods
            # pylint: disable=R0903
            __metaclass__ = CustomMeta
            name = 'My_name'
            answer = 42

            @abstractproperty
            def abs_prop(self):
                '''Test abstract property.'''
                pass

        class CustomClassBad(CustomAbstractClass):
            '''Test class failing checks.'''
            # R0903: Too few public methods
            # W0223: Abstract property not overriden
            # pylint: disable=R0903,W0223
            name = 'My_name'
            answer = 42

        with pytest.raises(TypeError) as err:
            CustomClassBad()
        assert err.value.message.startswith("Can't instantiate abstract")

        class CustomClass(CustomAbstractClass):
            '''Test class passing checks.'''
            # R0903: Too few public methods
            # pylint: disable=R0903
            name = 'My_name'
            answer = 42
            abs_prop = None
        CustomClass()

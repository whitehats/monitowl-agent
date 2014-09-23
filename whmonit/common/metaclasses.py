# -*- encoding: utf-8 -*-
'''
Common metaclasses.
'''

from abc import ABCMeta


class CheckException(object):
    ''' Exception raised on failed check on component class. '''
    def __init__(self, error_msg):
        ''' Constructor for CheckException. '''
        self.message = error_msg
        self.check_name = None

    def __repr__(self):
        ''' Returns string representation of object. '''
        return '{} | {}'.format(self.check_name, self.message)


class InvalidClassException(Exception):
    ''' Derived class assumptions broken. '''
    def __init__(self, _cls, check_errors):
        ''' Constructor for InvalidClassException. '''
        super(InvalidClassException, self).__init__()
        self._cls = _cls
        self.check_errors = check_errors

    def __str__(self):
        ''' Returns string representation of object. '''
        return 'Class {} is not valid.\n{}'.format(
            self._cls,
            '\n'.join(str(error) for error in self.errors)
        )


class BaseCheckMeta(ABCMeta):
    '''
    Metaclass that performs various checks on class
    detecting basic developer mistakes.
    You can define check by creating new static method prefixed with 'check_',
    example 'check_action_names_are_cute'.

    Each 'check_' function is executed with following arguments:

    * ``mcs`` - <class 'whmonit.common.metaclasses.BaseCheckMeta'>
    * ``clsname`` - name of component class
    * ``cls`` - newly created class
    * ``bases`` - list of component class' base classes
    * ``dct`` - dictionary of component class' attributes (__dict__)
    '''

    def __init__(cls, clsname, bases, dct):
        '''
        Trigger predefined checks on given class after it has been constructed.
        '''
        super(BaseCheckMeta, cls).__init__(clsname, bases, dct)
        errors = []
        mcs = cls.__metaclass__
        for member_name in mcs.__dict__:
            if not member_name.startswith('check_'):
                continue
            func = getattr(mcs, member_name)
            if not callable(func):
                continue
            for error in func(mcs=mcs, clsname=clsname, cls=cls, bases=bases, dct=dct):
                error.check_name = func.func_name
                errors.append(error)
        if errors:
            raise InvalidClassException(_cls=cls, check_errors=errors)

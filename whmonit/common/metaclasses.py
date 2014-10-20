# -*- encoding: utf-8 -*-
'''
Common metaclasses.
'''

from abc import ABCMeta


from whmonit.common.error import Error


class CheckException(object):
    ''' Exception raised on failed check on component class. '''
    def __init__(self, error_msg):
        ''' Constructor for CheckException. '''
        self.message = error_msg
        self.check_name = None

    def __str__(self):
        ''' Returns string representation of object. '''
        return '{}: {}'.format(self.check_name, self.message)


class InvalidClassError(Error):
    ''' Derived class assumptions broken. '''
    params = 'cls, check_errors'

    @property
    def text(self):
        ''' Prepare text content for the exception. '''
        return 'Class {} breaks the following assumptions:{}'.format(
            self.env['cls'],
            ''.join('\n\n' + str(error) for error in self.env['check_errors'])
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
            raise InvalidClassError(cls=cls, check_errors=errors)

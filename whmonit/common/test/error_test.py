'''
Tests for whmonit.common.error.ErrorType and whmonit.common.error.Error.
'''
import pytest

from whmonit.common.error import Error, BadError


def test_simple_error():
    ''' The simplest Error exception is one that has a docstring. '''
    class SimpleError(Error):
        ''' Hello world. '''

    with pytest.raises(SimpleError) as excinfo:
        raise SimpleError()

    assert str(excinfo).endswith('Hello world.')


def test_parametrized_error():
    ''' An Error exception can be parametrized; `params` contains names of
    parameters, and `text` contains a template to fill. '''
    class ParamError(Error):
        ''' Params here. '''
        params = 'name, offense'
        text = '{name} is guilty of {offense}.'

    with pytest.raises(ParamError) as excinfo:
        raise ParamError('kernel', 'panic')

    assert 'Params here.' in str(excinfo)
    assert 'kernel is guilty of panic' in str(excinfo)


def test_derived_error():
    ''' You can derive an exception from another Error exception. The base
    Error exception docstring and parameters are ignored then. This is useful
    mostly to build a hierarchy of exceptions; the derived exception should
    have a more specific docstring/parameters anyway, so no point in preserving
    the ones from base exception. '''
    class BaseError(Error):
        ''' First string. '''
        params = 'foo'
        text = 'No {foo}'

    class DerivedError(BaseError):
        ''' Second string. '''
        params = 'baz, aldrin'
        text = '{baz} {aldrin} was here'

    with pytest.raises(DerivedError) as excinfo:
        raise DerivedError('Jan', 'Kowalski')

    assert 'Second string.' in str(excinfo)
    assert 'Jan Kowalski was here' in str(excinfo)
    assert 'First string.' not in str(excinfo)
    assert 'No' not in str(excinfo)
    assert isinstance(excinfo.value, BaseError)


def test_can_have_property_for_text():
    ''' An Error exception can have a string-returning property for the `text`
    member. The property is then expected to return a ready-to-use string after
    substitutions, as no additional substitutions are performed in this case.
    '''
    class TestError(Error):
        ''' Example error. '''
        params = 'foo, bar'

        @property
        def text(self):
            ''' Prepare text content for the exception. '''
            return 'Left is {}, right is {}.'.format(
                self.env['foo'], self.env['bar'])

    with pytest.raises(TestError) as excinfo:
        raise TestError('x', 'y')

    assert 'Example error.' in str(excinfo.value)
    assert 'Left is x, right is y.' in str(excinfo.value)


def test_multiline_text():
    ''' An Error exception will format a '\n\n' substring into a new line. '''
    class TestError(Error):
        ''' Some error. '''
        params = 'items'

        @property
        def text(self):
            ''' Prepare text content for the exception. '''
            return ''.join('\n\n* ' + item for item in self.env['items'])

    with pytest.raises(TestError) as excinfo:
        raise TestError(['hello', 'world'])

    assert 'hello\n' in str(excinfo.value)


def test_param_cant_be_magic_string():
    ''' An Error exception cannot have a certain magic string
    "this_exception_class" as a parameter name, as it is used internally. '''
    with pytest.raises(BadError):
        class TestError(Error):  # unused variable: pylint: disable=W0612
            ''' That other error. '''
            params = 'this_exception_class'
            text = 'So what?'

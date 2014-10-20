'''
Base classes for exceptions in whmonit.

:py:class:`Error` is a desired base class for all exceptions in whmonit. It
provides some shortcuts making it easier to put values into exception text, as
well as does some basic type-checking on the format of exception.

Note: this class is not unittested by intention: it only provides visual aid
while debugging.
'''
import textwrap
import re


class BadError(Exception):
    ''' Exception is badly defined. See :py:class:`ErrorType`. '''
    pass


class ErrorType(type):
    ''' A metaclass for :py:class:`Error`:.

    Checks for validity of Error subclasses, and inserts constructor that
    has proper arguments.

    Enforced rules for :py:class:`Error` subclasses:

    #. class name must end with "Error"
    #. must define a docstring
    #. cannot have a constructor (constructor is injected automatically here)
    #. one of the following:

       #. cannot have class members called `params` and `text`
       #. has at least two class members `params` and `text`, both strings.

    #. if there is a class member `env`, it must be a dictionary.

    If `params` and `text` are defined, `params` must be a comma-separated list
    of identifiers. `params` will become list of arguments for constructor.
    When printing exception, a string consisting of docstring concatenated with
    str.format()ed `text` and ``message`` will be shown. Formatting will use
    `params` as keys bound to constructor arguments. If `env` is present, it
    will additionally add its keys to format.

    Example:

    >>> users = {'mary': 'abc123', 'john': 'ilovemary'}
    >>> class WrongPasswordError(Error):
    ...     """ Use this error, if user set inappropriate password 3 times. """
    ...     params = 'username, password'
    ...     text = ('User\`s (`{username!r}`) password `{password!r}` is incorrect. ' +
    ...             'Current users: {users!r}.')
    ...     env = {'users': users}
    ...
    >>> raise WrongPasswordError('abc123', 'topsecret')
    Traceback (most recent call last):
    [...]
    WrongPasswordError: User's (`abc123`) password `topsecret` is incorrect.
    Current users: {'john': 'ilovemary', 'mary': 'abc123'}.

    Suggested way for using this class: whenever a module defines more than
    a single exception, define a subclass `Error` in this module's namespace,
    then subclass is for specific exceptions. If there's just a single
    exception, subclass `Error` directly into specific class.
    '''
    def __init__(cls, name, bases, dct):
        if '__doc__' not in dct:
            raise BadError('You need to provide docstring for your exception.')

        if not name.endswith('Error'):
            raise BadError('''Exception's class name must end with "Error".''')

        params = []
        text_property = property(lambda self: '')
        if 'params' in dct and 'text' in dct:
            if not isinstance(dct['params'], basestring):
                raise BadError('`params` must be string.')

            text = dct['text']
            if isinstance(text, basestring):
                text_property = property(lambda self: text.format(**self.env))
            elif isinstance(text, property):
                text_property = text
            else:
                raise BadError('`text` must be string or property.')

            params = filter(len, re.split(',\s+', dct['params']))

        elif 'text' in dct:
            raise BadError('You need to provide a `params` class member if '
                           'you have `text`.')

        elif 'params' in dct:
            raise BadError('You need to provide a `text` class member if you '
                           'have `params`.')

        if 'this_exception_class' in params:
            raise BadError('You cannot use "this_exception_class" as param.')

        if '__init__' in dct:
            raise BadError('You cannot have an __init__ method.')

        if 'env' in dct and not isinstance(dct['env'], dict):
            raise BadError('`env` must be a dictionary if provided.')

        params_init = ''.join(', ' + p for p in params)
        params_dict = ', '.join('{!r}: {}'.format(p, p) for p in params)

        code = '''def __init__(self{}, message=""):
            if not hasattr(self, 'initialized'):
                self.message = message
                self.env = {{{}}}
                try:
                    self.env.update(self.__class__.env)
                except AttributeError:
                    pass
                self.initialized = True
            super(this_exception_class, self).__init__(str(self))
        '''.format(
            params_init, params_dict
        )

        env = {'this_exception_class': cls}
        exec code in env

        cls.__init__ = env['__init__']
        cls.text = text_property
        super(ErrorType, cls).__init__(name, bases, dct)


class Error(Exception):
    ''' Base class for exceptions in whmonit. See documentation of
    :py:class:`ErrorType` for more details. '''
    __metaclass__ = ErrorType

    def __str__(self):
        try:
            text = self.__class__.__doc__.strip() + ' ' + self.text
            if self.message:
                text += self.message
        except IndexError:
            # happens when the format string uses positional arguments instead
            # of keywords
            text = ('{}\n\n\n\n(Warning: format string with positional arguments, ' +
                    'this is a bug in this exception! Format string: {!r},' +
                    'dictionary: {!r})').format(
                        self.__class__.__doc__.strip(),
                        self.text,
                        str(self.env))

        texts = text.split('\n\n')
        for i in xrange(len(texts)):
            texts[i] = re.sub('\s+', ' ', texts[i]).strip()
            texts[i] = textwrap.fill(
                texts[i],
                initial_indent='' if i else ' ' * len(self.__class__.__name__))
        texts[0] = texts[0][len(self.__class__.__name__):]

        return '\n'.join(texts)


class ArgumentError(Error):
    '''
    .. note::

        Base class for other exceptions. Never use it directly.

    Argument Error is base class for all function/method arguments' errors.  As
    first `param` you should always set the parameter name (`argument_name` is
    the param name). As second parameter `argument` (argument value` should be
    used, if is used. '''
    pass


class ArgumentTypeError(ArgumentError, TypeError):
    '''Argument has wrong type.'''
    text = 'Argument `{argument_name}` is type `{argument_type}`, but should be `{expected_type}`'
    params = 'argument_name, argument_type, expected_type'


class ArgumentValueError(ArgumentError, ValueError):
    '''Argument has inappropriate value.'''
    text = ('The value `{value}` of argument `{argument_name}` is not valid. '
            'It should restrict following rules: {rules}.')
    params = 'argument_name, value, rules'


class LengthNotInRangeError(ArgumentValueError):  # pylint: disable=R0901
    '''Argument's length not in range.'''
    text = 'Argument `{argument_name}` has length {length} but it must be in [{range1}, {range1}].'
    params = 'argument_name, length, valid_length'


class LengthMismatchError(ArgumentValueError):  # pylint: disable=R0901
    '''Argument's length not equal expected value.'''
    text = 'Argument {argument_name} has length {length} but it must have {expected_length}'
    params = 'argument_name, length, expected_length'


class WrongArgumentsTogetherError(ArgumentError, RuntimeError):
    '''These arguments cannot be used together in one call.'''
    text = 'You cannot set {argument_name1} and {argument_name2} together!'
    params = 'argument_name1, argument_name2'

'''
Helper functions and variables for using in tests
'''

from tempfile import NamedTemporaryFile

from ..types import PrimitiveTypeRegistry
from ..iterator import subsets

# artificial primitive used in tests
BASIC_PRIMITIVES = [type('type_%s' % x, (object,), {}) for x in xrange(5)]

# all combinations of primitives for testing
COMBINATION_OF_PRIMITIVES = subsets(BASIC_PRIMITIVES)


def make_registry(list_of_primitives_to_register):
    '''
    initialize type registry for testing
    '''
    reg = PrimitiveTypeRegistry()
    reg.register_many(list_of_primitives_to_register)
    return reg


def UnbufferedNamedTemporaryFile(content='', delete=True):
    '''
    Temporary file with no buffer.
    '''
    # C0103: Invalid name "UnbufferedNamedTemporaryFile"
    # pylint: disable=C0103
    fileh = NamedTemporaryFile(bufsize=0, delete=delete)
    fileh.write(content)
    return fileh

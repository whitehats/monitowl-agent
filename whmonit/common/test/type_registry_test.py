'''
Tests for primitives in TypeRegistry
'''

import pytest

from .helpers import COMBINATION_OF_PRIMITIVES
from ..types import (
    PrimitiveTypeRegistry, AlreadyRegisteredError, NotRegisteredError,
)


@pytest.mark.parametrize('types', COMBINATION_OF_PRIMITIVES)
def test_registration_mechanism(types):
    'make default register and try to register all primitive metas'
    reg = PrimitiveTypeRegistry()
    for type_ in types:
        reg.register(type_)

    reg2 = PrimitiveTypeRegistry()
    reg2.register_many(types)

    for type_ in types:
        assert type_ in reg
        assert type_ in reg2
        pytest.raises(AlreadyRegisteredError, reg2.register, type_)
        pytest.raises(AlreadyRegisteredError, reg.register, type_)

    for type_ in types:
        reg2.unregister(type_)
        reg.unregister(type_)

    for type_ in types:
        assert type_ not in reg
        assert type_ not in reg2
        pytest.raises(NotRegisteredError, reg2.unregister, type_)
        pytest.raises(NotRegisteredError, reg.unregister, type_)

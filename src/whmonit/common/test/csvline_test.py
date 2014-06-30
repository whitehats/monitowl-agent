# -*- coding: utf-8 -*-
'''
Test csvline helpers.
'''

import pytest

from .. import csvline


@pytest.mark.parametrize(('data', 'types', 'expected'), [
    ('test,1', [], ['test', '1']),
    ('test,2', [str, int], ['test', 2]),
    ('test,3,', [], ['test', '3', '']),
    ('test,4', [str, int, int], ['test', 4]),
    ('True,test', [bool], [True, 'test']),
])
def test_read(data, types, expected):
    '''
    Reads string into proper list of values.
    '''
    result = csvline.read(data, types)

    assert expected == list(result)


@pytest.mark.parametrize(('data', 'expected'), [
    (['test', '1'], 'test,1'),
    (['test', 2], 'test,2'),
    ([True, 'test'], 'True,test'),
    (['test', '3', ''], 'test,3,'),
])
def test_write(data, expected):
    '''
    Writes list of values into proper string.
    '''
    result = csvline.write(data)

    assert expected == result

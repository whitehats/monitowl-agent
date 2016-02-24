'''
Additional generic iterables.
'''

from itertools import combinations, chain, tee, izip, izip_longest


def subsets(list_):
    '''
    Returns sum of all combinations from given list.
    '''
    return list(chain.from_iterable(
                combinations(list_, x)
                for x in xrange(len(list_) + 1))
                )


def generic_range(start, stop, step):
    ''' A generic version of `xrange` which works with anything that has an
    addition and comparison operators, ie. datetime objects. '''

    while start < stop:
        yield start
        start += step


def generic_count(start, step):
    ''' A generic version of `itertools.count` which works with anything that
    has an addition operator, ie. datetime objects.'''

    while True:
        yield start
        start += step


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    first, second = tee(iterable)
    next(second, None)
    return izip(first, second)


def pairwise_with_final(iterable, fillvalue=None):
    '''
    Like `pairwise`, but fills last element with `fillvalue` on uneven
    iterables lengths.
    '''
    first, second = tee(iterable)
    next(second, None)
    return izip_longest(first, second, fillvalue=fillvalue)

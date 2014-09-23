'''
Tests for whmonit.common.test.itertime_test
'''
import random

from unittest import TestCase
from datetime import datetime as dt
from datetime import timedelta as td
from itertools import islice

from ..iterator import generic_range, generic_count, subsets


def test_subsets():
    '''tests for subset function'''
    assert subsets([]) == [()]
    assert len(subsets([])) == 2 ** len([])
    assert subsets(['a', 'b']) == [(), ('a', ), ('b', ), ('a', 'b')]

    testinglist = []
    for _cntr in xrange(10):
        testinglist.append(random.randint(0, 100))
        assert len(subsets(testinglist)) == 2 ** len(testinglist)


class GenericRangeTest(TestCase):
    def test_stop_before_start(self):
        self.assertListEqual(
            [],
            list(generic_range(
                dt(2012, 5, 1), dt(2012, 1, 1), td(seconds=1))))

    def test_single_item(self):
        self.assertListEqual(
            [dt(2012, 3, 1)],
            list(generic_range(
                dt(2012, 3, 1), dt(2012, 3, 12), td(days=30))))

    def test_several_items(self):
        self.assertListEqual(
            [dt(1998, 1, 2), dt(1998, 2, 1), dt(1998, 3, 3)],
            list(generic_range(
                dt(1998, 1, 2), dt(1998, 3, 5), td(days=30))))

    def test_no_end_element(self):
        self.assertListEqual(
            [],
            list(generic_range(
                dt(2001, 5, 3), dt(2001, 5, 3), td(seconds=60))))

        self.assertListEqual(
            [dt(2015, 3, 6), dt(2015, 3, 7), dt(2015, 3, 8)],
            list(generic_range(
                dt(2015, 3, 6), dt(2015, 3, 9), td(days=1))))


class GenericCountTest(TestCase):
    def test_with_datetimes(self):
        start = dt(2012, 1, 1)
        step = td(days=5)

        self.assertEqual(
            list(start + step * k for k in xrange(10)),
            list(islice(generic_count(start, step), 0, 10)))

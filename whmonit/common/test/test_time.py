import pytest
import unittest
from datetime import datetime as dt

from whmonit.common.time import round_time
from whmonit.common.time import MillisecondTimestampRangeError
from whmonit.common.time import MillisecondTimestampTypeError
from whmonit.common.time import check_millisecond_timestamp
from whmonit.common.time import datetime_to_milliseconds
from whmonit.common.time import milliseconds_to_datetime


class TestTime(unittest.TestCase):
    def test_round_time(self):
        d = dt(year=2012, month=1, day=1, hour=1)
        self.assertEqual(d, round_time(d))

        d = dt(year=2012, month=1, day=1, hour=1, minute=1, second=1)
        _d = dt(year=2012, month=1, day=1, hour=1, minute=1, second=0)
        self.assertEqual(_d, round_time(d, 60 * 1000))

        d = dt(year=2012, month=1, day=1, hour=2, minute=1, second=1)
        _d = dt(year=2012, month=1, day=1, hour=2, minute=0, second=0)
        self.assertEqual(_d, round_time(d, 60 * 60 * 1000))

        d = dt(year=2012, month=1, day=1, hour=1, minute=1, second=0, microsecond=333333)
        _d = dt(year=2012, month=1, day=1, hour=1, minute=1, second=0)
        self.assertEqual(_d, round_time(d, 1000))

        self.assertEqual(3600 * 1000, round_time(3600 * 1000 + 2333, 60 * 60 * 1000))


@pytest.mark.parametrize('ts', [0,
                                1,
                                -5000,
                                123213131,
                                123081249714412,
                                -12917481247])
def test_check_millisecond_timestamp(ts):
    check_millisecond_timestamp(ts)


@pytest.mark.parametrize(('ts', 'error_type'),
                         [(3.0, 0),
                          ('1', 0),
                          (u'1', 0),
                          (39999999999999999999, 1),
                          (-39999999999999999999, 1),
                          (21076191833471518962, 1),
                          (-21076191833471518962, 1),
                          (19693734395595293058, 1),
                          (-19693734395595293058, 1)])
def test_check_millisecond_timestamp_for_invalid_data(ts, error_type):
    # error_type == 0 - Wrong type
    # error_type == 1 - Out of range
    if error_type == 0:
        with pytest.raises(MillisecondTimestampTypeError):
            check_millisecond_timestamp(ts)
        return
    elif error_type == 1:
        with pytest.raises(MillisecondTimestampRangeError):
            check_millisecond_timestamp(ts)
        return
    raise AssertionError('Fix your test data')


@pytest.mark.parametrize(['ts', 'dt'],
                         [(1381363200000, dt(2013, 10, 10, 0, 0)),
                          (-62135596800000, dt(1, 1, 1)),
                          (0, dt(1970, 1, 1)),
                          (1279655165001L, dt(2010, 7, 20, 19, 46, 5, 1000)),
                          (1279655165231L, dt(2010, 7, 20, 19, 46, 5, 231000)),
                          ])
def test_milliseconds_to_datetime_to_milliseconds(ts, dt):
    assert milliseconds_to_datetime(ts) == dt
    assert ts == datetime_to_milliseconds(dt)
    assert milliseconds_to_datetime(datetime_to_milliseconds(dt)) == dt
    assert datetime_to_milliseconds(milliseconds_to_datetime(ts)) == ts

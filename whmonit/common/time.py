'''
Time module
-----------

This module contains common functions which operate on `time` and `dates`.


**Important note**:

If not declared otherwise, ``timestamp`` in the system is meant as milliseconds
in UTC from epoch. In python and databases this must be stored as 8-byte
``signed int``. Values out of range should be treated as errors rather than be
truncated (this can be done using :meth:`check_millisecond_timestamp` method).

:py:obj:`datetime.datetime` objects must be naive (without time zone specified)
- that ``datetime`` object is treated as UTC time.

.. warning::

    Rather then using ``tzinfo`` in :py:obj:`datetime.datetime`,
    you should always get :py:obj:`datetime.datetime` by calling
    ``datetime.datetime.utcnow``.

'''
# TODO #704: python's datetime object has range limitations.
from __future__ import absolute_import

import math
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .error import Error


def round_time(timestamp, milliseconds=60 * 1000, func=math.ceil):
    '''
    Round time

    Default: round time to full minutes (with ceil function)

    :param timestamp: milliseconds (int or float) or `datetime` object
    :param milliseconds: precision (in milliseconds) of 'rounding' (default:60*1000 = 1 minute)
    :param func: 'round' function (default: math.ceil)

    :returns: rounded `timestamp` object (`int`, `float` or `datetime` object)

    '''
    was_dt = False
    if isinstance(timestamp, datetime):
        was_dt = True
        secs = datetime_to_milliseconds(timestamp)
    else:
        secs = timestamp

    secs /= milliseconds
    secs = func(secs)
    secs *= milliseconds
    if was_dt:
        return milliseconds_to_datetime(int(secs))
    return int(secs)


class MillisecondTimestampRangeError(Error, ValueError):
    '''Milliseconds timestamp is out of range.'''
    text = ('Got {bits}-bit value (`{value}`) but expected no more than '
            '{expected_bits} bit signed integer.')
    params = 'value, bits, expected_bits'


class MillisecondTimestampTypeError(Error, TypeError):
    '''Milliseconds timestamp has wrong type.'''
    text = 'Got `{type}` but expected `{expected}`.'
    params = 'type, expected'


def check_millisecond_timestamp(timestamp):
    ''' Check that ``timestamp`` is ``int`` (or ``long``) and is no bigger than
    8-bytes. '''

    if not isinstance(timestamp, (int, long)):
        raise MillisecondTimestampTypeError(type(timestamp), int)
    if timestamp.bit_length() > 64:
        raise MillisecondTimestampRangeError(timestamp, timestamp.bit_length(), 64)
    return timestamp


def datetime_to_utc(_datetime):
    ''' DEPRECATED You shouldn't use ``tzinfo``, but always get new
    :py:obj:`datetime.datetime` by calling ``datetime.datetime.utcnow``.

    Convert :obj:`datetime.datetime` to UTC if ``tzinfo`` was set and
    return new naive ``datetime`` object or return original ``_datetime`` if
    ``tzinfo`` was not set.'''

    del _datetime
    assert False, 'Use of deprecated function. Read documentation.'


def datetime_to_milliseconds(_datetime):
    ''' Convert naive :obj:`datetime.datetime` to millisecond timestamp
    (``int``).

    You shouldn't pass timezone aware :obj:`datetime.datetime`,
    but make sure they are in UTC.'''

    timestamp = int(round(
        calendar.timegm(_datetime.timetuple()) * 1000
        + _datetime.microsecond / 1000.0
    ))

    check_millisecond_timestamp(timestamp)
    return timestamp


def milliseconds_to_datetime(timestamp):
    ''' Convert millisecond timestamp (``int``) to naive :obj:`datetime.datetime`. '''
    check_millisecond_timestamp(timestamp)
    #: Because utcfromtimestamp uses system C functions, it can't handle "big"
    #: timestamp values. We use little hack here with python timedelta
    #: class which doesn't have that problem.
    return datetime.utcfromtimestamp(0) + timedelta(milliseconds=timestamp)


def month_diff(date1, date2):
    '''
    Calculates difference between two dates in months.
    '''
    delta = relativedelta(date1, date2)

    # This is for taking floor,
    # eg (-1 month -2 days) is actually (-2 months) when counting starting point.
    sub = int(
        delta.days < 0 or
        delta.hours < 0 or
        delta.minutes < 0 or
        delta.seconds < 0 or
        delta.microseconds < 0
    )

    return float(delta.years * 12 + delta.months - sub)


def year_diff(date1, date2):
    '''
    Calculates difference between two dates in years.
    '''
    return math.floor(month_diff(date1, date2) / 12)


def day_diff(date1, date2):
    '''
    Calculates difference between two dates in days.

    This should work for leap seconds since timedelta stores days and seconds separately.
    The only problem remains with additional second at the end of some days but the
    hour 23:59:60 isn't even accepted by datetime - this second, while counting seconds,
    will be skipped.

    Also, there's no need for floor, since seconds are always positive
    '''
    return float((date1 - date2).days)


def week_diff(date1, date2):
    '''
    Calculates difference between two dates in weeks.
    This is just for convenience
    '''
    return math.floor(day_diff(date1, date2) / 7)


def second_diff(date1, date2):
    '''
    Calculates difference between two dates in seconds.
    '''
    return (date1 - date2).total_seconds()


def diff_function(period):
    '''
    Return function that calculates difference between two dates in ``periods``.

    :param period: string with period name, one of ``[second, day, week, month, year]``
    :raises: :class:`KeyError` if ``period`` is another value
    '''
    return globals()['{}_diff'.format(period)]

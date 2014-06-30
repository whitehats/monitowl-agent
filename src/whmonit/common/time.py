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

If ``datetime`` objects are time zone aware, they must be converted to naive
datetime objects (for example by using :py:func:`datetime_to_utc`)

.. warning::

    Due to DST please use ``pytz.timezone.localize`` to set timezone on
    ``datetime`` object rather then setting timezone as ``tzinfo`` in
    ``datetime`` object constructor.

'''
# TODO #704: python's datetime object has range limitations.
from __future__ import absolute_import

import math
import calendar
from datetime import datetime, timedelta

import pytz

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
    ''' Convert :obj:`datetime.datetime` to UTC if ``tzinfo`` was set and
    return new naive ``datetime`` object or return original ``_datetime`` if
    ``tzinfo`` was not set.'''

    if _datetime.tzinfo:
        return _datetime.astimezone(pytz.UTC).replace(tzinfo=None)
    return _datetime


def datetime_to_milliseconds(_datetime):
    ''' Convert naive :obj:`datetime.datetime` to millisecond timestamp
    (``int``).

    If you pass timezone aware datetime, the result may be invalid. Use
    :meth:`datetime_to_utc` for localized datetime objects.'''

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

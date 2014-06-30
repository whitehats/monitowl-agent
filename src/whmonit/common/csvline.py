# -*- coding: utf-8 -*-
'''
Helpers for dealing with single line string in CSV format.
'''

import csv
from cStringIO import StringIO
from itertools import izip_longest


def read(line, types=[]):
    '''
    Reads a CSV formatted string into list of values.
    Does a primitive type resolution.

    :param line: CSV formatted string.
    :param types: List of types for each value.
                  If len(types) < len(line), str will be used for rest.
    '''
    # Dangerous default value [] as argument.
    # pylint: disable=W0102

    output = csv.reader([line]).next()
    if len(types) > len(output):
        types = types[:len(output)]
    for typ, out in izip_longest(types, output, fillvalue=str):
        if typ == bool:
            yield out == 'True'
        else:
            yield typ(out)


def write(line):
    '''
    Writes a list of values into CSV formatted string.

    :param line: List of values.
    '''
    output = StringIO()
    writer = csv.writer(output, lineterminator='')
    writer.writerow(line)
    return output.getvalue()

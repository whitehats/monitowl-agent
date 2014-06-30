# -*- coding: utf-8 -*-
'''Uptime sensor test.'''
from mock import mock_open, patch
from ..linux_01 import Sensor


class TestClassUptime():
    '''Uptime test class'''
    #W0201: Attributes 'sensor' defined outside __init__.
    #W0232: Class has no __init__ method.
    #pylint: disable=W0201, W0232
    def setup(self):
        '''Test setup.'''
        def empty_handler():
            '''Just an empty handler.'''
            pass

        self.sensor = Sensor({"frequency": 10}, empty_handler)

    def test_read_uptime(self):
        '''Test reading uptime.'''
        mop = mock_open(read_data='340353.11 334152.36')
        with patch('__builtin__.open', mop, create=True) as mock_thang:
            assert (('default', 340353.11),) == self.sensor.do_run()
            mock_thang.assert_called_once_with('/proc/uptime')

    def test_name(self):
        '''Test for valid name.'''
        assert self.sensor.name == 'uptime'

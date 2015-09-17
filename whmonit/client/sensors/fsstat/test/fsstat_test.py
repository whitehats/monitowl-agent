'''
Tests for whmonit.client.sensors.fsstat
'''
from mock import Mock

from ..linux_01 import Sensor


class TestFsstat(object):
    ''' Test fsstat sensor. '''

    def test_common_usage(self):
        ''' Test everyday usage. '''

        result = Sensor({'sampling_period': 3}, Mock(), None).do_run()
        assert len(result) == 4

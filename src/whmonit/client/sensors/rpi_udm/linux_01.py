#!/usr/bin/env python
'''UDM data transfer.'''
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """Raspberry PI ultrasonic distance meter."""

    name = 'rpi_udm'
    streams = {'distance': float}

    def __init__(self, *args, **kwargs):
        super(Sensor, self).__init__(*args, **kwargs)
        import importlib
        self.ultra = importlib.import_module('whmonit.client.sensors.rpi_udm.ultrasonic_2')

    def do_run(self):
        """Executes itself."""

        distance = self.ultra.do_it()
        if not distance:
            return ()

        return (('distance', float(distance)), )

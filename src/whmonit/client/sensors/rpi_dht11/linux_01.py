#!/usr/bin/env python
import os
import sh
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """Raspberry PI temperature and humidity indicator/sensor."""

    name = 'rpi_dht11'
    streams = {'humidity': float, 'temperature': float}

    def __init__(self, *args, **kwargs):
        super(Sensor, self).__init__(*args, **kwargs)
        self.DHT11 = sh.Command(os.path.join(os.path.dirname(__file__), 'dht11'))

    def do_run(self):
        """Executes itself."""

        # The result of script are two float numbers separated by whitespace.
        # The decimal point separator is a dot.
        # Example of typical output: 39.2 29.0
        # Output can be also "Invalid Data!!",
        # but then return's float() function will crash.
        data = self.DHT11()

        humidity, temperature = data.split(None, 1)

        try:
            # if dht11 program return invalid data
            humidity = float(humidity)
            temperature = float(temperature)
        except ValueError:
            return ()

        return (('humidity', float(humidity)), ('temperature', float(temperature)))

#!/usr/bin/env python

#import RPi.GPIO as GPIO
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """Raspberry PI PIR motion detector."""

    name = 'rpi_pir'
    streams = {'motion': float}

    def __init__(self, *args, **kwargs):
        super(Sensor, self).__init__(*args, **kwargs)
        import importlib
        self.GPIO = importlib.import_module('RPi.GPIO')

    def do_run(self):
        """Executes itself."""
        GPIO = self.GPIO

        # Use BCM GPIO references
        GPIO.setmode(GPIO.BCM)

        # Define GPIO to use on Pi
        GPIO_PIR = 7

        # Set pin as input
        GPIO.setup(GPIO_PIR, GPIO.IN)

        if GPIO.input(GPIO_PIR):
            # motion detected
            return (('motion', 1.0),)
        else:
            # no motion
            return (('motion', 0.0),)

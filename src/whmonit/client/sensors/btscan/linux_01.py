#!/usr/bin/env python
'''Bluetooth scanner. It returns number of found devices with bluetooth turned on nearby.'''

import sh
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """Bluetooth scanner."""

    name = 'btscan'
    streams = {'quantity': float}

    def do_run(self):
        """Executes itself."""

        lines = 0
        quantity = 0
        run = sh.hcitool("scan")

        for line in run:
            lines += 1
        if lines > 1:
            quantity = lines - 1

        return (('quantity', float(quantity)), )

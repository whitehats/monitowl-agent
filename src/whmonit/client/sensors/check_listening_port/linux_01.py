#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Check listening port sensor.
'''
import socket
from voluptuous import Required, Range, All, Lower, Any
from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    """
    Sensor class checking for local listening port.

    It looks through the process table, so does not
    try to open any connections.
    """

    name = 'check_listening_port'
    streams = {
        'is_open': bool,
        'pid': float,
        'name': str,
        'uid': float,
        'user': str,
    }
    config_schema = {
        Required('port'): All(int, Range(1, 65535)),
        Required('protocol'): All(Lower, Any('tcp', 'udp')),
    }

    types = {
        'tcp': socket.SOCK_STREAM,
        'udp': socket.SOCK_DGRAM,
    }

    def do_run(self):
        """
        Returns information about a process listening on given port.
        Only 'is_open' stream is returned if no such process could be found.
        """
        import psutil

        typ = Sensor.types.get(self.config['protocol'])

        for proc in psutil.process_iter():
            try:
                connections = proc.connections()
            except psutil.AccessDenied:
                # TODO #1100: Log error to agent
                continue

            for conn in connections:
                valid = (
                    conn.type == typ and
                    not conn.raddr and
                    conn.laddr[1] == self.config['port']
                )
                if valid:
                    return (
                        ('is_open', True),
                        ('pid', float(proc.pid())),
                        ('name', proc.name()),
                        ('uid', float(proc.uids().real)),
                        ('user', proc.username()),
                    )
        return (('is_open', False),)

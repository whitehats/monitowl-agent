# -*- encoding: utf-8 -*-
from abc import abstractproperty, ABCMeta
from nanotime import nanotime
from voluptuous import Required, Schema, Optional, All, Range


__all__ = ['Sensor']


class SensorBaseError(Exception):
    """Base class for sensor errors.

    Message of this class errors will be logged to sensor error channel.
    """


class ConfigurationError(Exception):
    """Sensor configuration error."""


# Method %r is abstract in class %r but is not overridden.
#%s %r has no %r member. Attribute %r defined outside __init__
# pylint: disable=W0223, E1101, R0201
class SensorBase(object):
    '''
    Base class for all sensors in the system.

    This module provides base core for making sensors.

    .. note::
            All global imports must not include additional requirements
            (non-standard python or whmonit modules).

            All additional requirements and custom modules must be loaded in
            constructor ``__init__``.

            This is done because sensors must be also loadable by server (to know
            what streams sensor has or what is the name of the sensor but server
            may not be able and may not want to fully initialize a sensor).

    ``__init__``
    '''
    __metaclass__ = ABCMeta
    # TODO: field checking can be implemented in metaclass

    config_schema = None
    # TODO: documentation + field checking

    @abstractproperty
    def name(self):
        """Sensor's name. Max 16 chars."""
        # TODO: documentation + field checking
        pass

    @abstractproperty
    def streams(self):
        """
        Sensor's streams.

        Sensor streams are defined as python :obj:`dict` (:class:`SensorBase.streams`)
        where keys are `names` (max. 16 character string) and values are corresponding
        :ref:`primitives`. Sensor can produce data associated with one of its
        streams (the data must be of type defined by associated stream).

        The idea behind stream types is to allow each stream (each :ref:`primitive
        <primitives>`) to be handled efficiently during transfer over a network and
        also when storing in :ref:`storage`. To learn more about how to define new
        primitives and add network or storage encoders and decoders look :ref:`here
        <primitives>`.

        .. note::

            `error` stream is always added automagically to each streams
            definition, so during implementation you must not define it.

        Example streams definition for cpu sensor::

            {
                'cpu': CPUTuple,
                'my_stream': float,
            }

        This example is valid as long as `CPUTuple` is defined as :ref:`primitive
        <primitives>`.
        """
        # TODO: documentation + field checking

    # TODO: config split -> internal_configuration, external_configuration
    def __init__(self, config, send_results, config_id=None):
        """
            Where:
            config: yaml
            send_results: callback function to supply results.
        """
        self.config = None
        self.reload(config)
        self._self_checks()
        if not send_results:
            raise SensorError("I need sendresults method as a parm!")
        self.send_results = send_results
        self.config_id = config_id

    def reload(self, config):
        """Reload sensor configuration."""

        # run to parent classes and merge schemas
        schema = self.config_schema
        tmp = self.__class__
        while tmp != SensorBase:
            tmp = tmp.__base__
            if tmp.config_schema:
                tmp_schema = tmp.config_schema
                tmp_schema.update(schema)
                schema = tmp_schema

        # validate config
        schema = Schema(schema)
        self.config = schema(config)

    def _self_checks(self):
        """Checks if sensor's name is correct."""
        import re
        from whmonit.common.enums import INTERNAL_SENSORS
        # check name
        if not re.match('\w+', self.name):
            raise ConfigurationError("Sensor's name does not match to \w+")
        if self.name in INTERNAL_SENSORS:
            raise ConfigurationError(
                "Sensor's name cannot be `{}`"
                .format(self.name)
            )

    def do_run(self):
        """
        Should return: (datatype, data).
        """
        raise NotImplementedError

    def log(self, logmsg):
        """This way sensors can pass diagnostics/error information."""
        # TODO: logmsg should have a format ex: (header, txt, stacktrace)
        print logmsg


class AdvancedSensorBase(SensorBase):

    """Long-running sensor process class."""
    # TODO: change name to EventSensor

    def run(self):
        """
        AdvancedSensor should run self.send_results(timestamp,data) to supply
        results.
        """
        self.do_run()

        # no way we are here..
        assert False


class TaskSensorBase(SensorBase):

    """One time sensor process class."""
    # all TaskSensors should have frequency set
    config_schema = {Required('frequency'): int,
                     Optional('memory_limit'): All(int, Range(min=1024)),
                     Optional('run_timeout'): All(int, Range(min=5, max=3600))}

    def run(self):
        """Run a check."""
        runtime = nanotime.now()
        data = self.do_run()
        # please validate
        if data is not None:
            self.send_results(runtime.datetime(), data)

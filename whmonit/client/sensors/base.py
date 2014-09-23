# -*- encoding: utf-8 -*-
import psutil
import sys
from abc import abstractproperty, ABCMeta
from copy import deepcopy
from datetime import datetime
from jsonschema import ValidationError

from whmonit.common.validators import ValidatorWithDefault


__all__ = ['Sensor']


class SensorBaseError(Exception):
    '''Base class for sensor errors.

    Message of this class errors will be logged to sensor error channel.
    '''


class ConfigurationError(Exception):
    '''Sensor configuration error.'''


class SensorBaseMeta(ABCMeta):
    '''
    Metaclass for :py:class:`SensorBase`:.
    Validates Sensor schema, calculates complete config schema
    (merging class and parents schemas), and saves it.
    '''
    def __new__(mcs, clsname, bases, dct):
        # Every config_schema should be valid against this meta_schema
        # If a certain config_schema does not validate you might have to
        # rewrite meta_schema and probably complete_schema as well.
        meta_schema = {
            '$schema': 'http://json-schema.org/schema#',
            'type': 'object',
            'properties': {
                '$schema': {
                    'type': 'string',
                    'default': 'http://json-schema.org/schema#'
                },
                'type': {'type': 'string', 'enum': ['object'], 'default': 'object'},
                'properties': {'type': 'object', 'default': {}},
                'dependencies': {'type': 'object', 'default': {}},
                'required': {'type': 'array', 'default': []},
                'additionalProperties': {'type': 'boolean', 'default': False}
            },
            'additionalProperties': False
        }
        validator = ValidatorWithDefault(meta_schema)
        schema = dct.get('config_schema', {})
        validator.validate(schema)
        # Merge config_schema with parent's config_schema.
        if bases[0] != object:
            parent_schema = deepcopy(bases[0].config_schema)
            parent_schema['properties'].update(schema['properties'])
            parent_schema['dependencies'].update(schema['dependencies'])
            parent_schema['required'] = list(
                set(parent_schema['required']) | set(schema['required'])
            )
            schema = parent_schema
        dct['config_schema'] = schema
        return ABCMeta.__new__(mcs, clsname, bases, dct)


# Method %r is abstract in class %r but is not overridden.
# %s %r has no %r member. Attribute %r defined outside __init__
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
    __metaclass__ = SensorBaseMeta
    # TODO #1428: field checking can be implemented in metaclass

    config_schema = {}
    # TODO #1428: documentation + field checking

    @abstractproperty
    def name(self):
        '''Sensor's name. Max 16 chars.'''
        # TODO #1428: documentation + field checking
        pass

    @abstractproperty
    def streams(self):
        '''
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
        '''
        # TODO #1428: documentation + field checking

    def __init__(self, config, send_results, storage, config_id=None):
        '''
            Where:
            config: yaml
            send_results: callback function to supply results.
            storage: Dict-like object which sensor can
                     use to store/retrieve persistent data.
                     Mostly for AdvancedSensors.
        '''

        # Make sensor process behave nice on the CPU.
        proc = psutil.Process()
        if sys.platform in ['linux2', 'darwin']:
            proc.nice(19)
            proc.ionice(psutil.IOPRIO_CLASS_IDLE)
        else:
            proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            proc.ionice(0)

        self.config = None
        if not send_results:
            raise SensorError("I need send_results method as a param!")
        self.send_results = send_results
        self.reload(config)
        self._self_checks()
        self.storage = storage
        self.config_id = config_id
        # add error stream
        self.__class__.streams['error'] = str

    @classmethod
    def validate_config(cls, config):
        '''
        Validates configuration against complete config schema of a sensor.
        '''
        schema = cls.config_schema
        validator = ValidatorWithDefault(schema)
        validator.validate(config)
        return config

    def reload(self, config):
        '''Reload sensor configuration.'''

        try:
            self.config = self.__class__.validate_config(config)
        except ValidationError as err:
            # This should never happen in run time, it's a coding error
            # and should be caught in tests.
            self.log(
                'error while merging schemas: config_schema in class `{}`'
                '''should be valid against `meta_schema`
                {}'''.format(self.__class__.__name__, err.message)
            )
            raise err

    def _self_checks(self):
        '''Checks if sensor's name is correct.'''
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
        '''
        Should return: (datatype, data).
        '''
        raise NotImplementedError

    def log(self, logmsg):
        '''This way sensors can pass diagnostics/error information.'''
        # TODO #1429: logmsg should have a format ex: (header, txt, stacktrace)
        self.send_results(datetime.utcnow(), (('error', logmsg),))


class AdvancedSensorBase(SensorBase):
    '''Long-running sensor process class.'''

    def run(self):
        '''
        AdvancedSensor should run self.send_results(timestamp,data) to supply
        results.
        '''
        self.do_run()

        # no way we are here..
        assert False


class TaskSensorBase(SensorBase):
    '''One time sensor process class.'''
    # all TaskSensors should have frequency set
    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'frequency': {'type': 'integer'},
            'memory_limit': {'type': 'integer', 'minimum': 1024},
            'run_timeout': {'type': 'integer', 'minimum': 5, 'maximum': 3600}
        },
        'required': ['frequency'],
        'additionalProperties': False
    }

    def run(self):
        '''Run a check.'''
        runtime = datetime.utcnow()
        data = self.do_run()
        # please validate
        if data is not None:
            self.send_results(runtime, data)

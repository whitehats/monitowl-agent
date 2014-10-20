# -*- encoding: utf-8 -*-
import inspect
import psutil
import re
import sys
from abc import abstractproperty
from copy import deepcopy
from datetime import datetime
from jsonschema import ValidationError

from whmonit.common.enums import INTERNAL_SENSORS
from whmonit.common.metaclasses import BaseCheckMeta, CheckException
from whmonit.common.types import PRIMITIVE_TYPE_REGISTRY
from whmonit.common.validators import ValidatorWithDefault


class InvalidDataError(Exception):
    '''Coding error: invalid stream_name, or datatype in stream.'''


class InvalidSendResultsError(Exception):
    '''Sensor instance received an invalid (not callable) send_results method.'''


class SensorBaseMeta(BaseCheckMeta):
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
        return super(SensorBaseMeta, mcs).__new__(mcs, clsname, bases, dct)

    def __init__(cls, clsname, bases, dct):
        '''
        Initialization step for base sensor class.

        Adds 'error' stream to the streams list.
        '''
        if not inspect.isabstract(cls):
            dct['streams']['error'] = {
                'type': str, 'description': 'Error stream.',
            }
        super(SensorBaseMeta, cls).__init__(clsname, bases, dct)

    @staticmethod
    def check_name(clsname, cls, dct, **dummy):
        '''
        Check if sensor's name is correct - maximum 32 characters.
        '''
        if inspect.isabstract(cls):
            return
        name = dct['name']
        if not re.match('^\\w{1,32}$', name):
            yield CheckException(
                "{}.name: `{}` doesn't match '^\\w{1,32}$'".format(clsname, name)
            )
        if name in INTERNAL_SENSORS:
            yield CheckException(
                '{}.name cannot be `{}`'.format(clsname, name)
            )

    @staticmethod
    def check_streams(clsname, cls, dct, **dummy):
        '''
        Check if Sensor's stream names are of length 32 or less
        and stream types are dicts with:
         'type': of type :ref:`primitive <primitives>`
         'description': of type :ref:`str`
        '''
        if inspect.isabstract(cls):
            return
        for name, return_type in dct['streams'].iteritems():
            if not re.match('^\\w{1,32}$', name):
                yield CheckException(
                    "{}.streams' name: `{}` can only contain '\\w' characters "
                    "and can't be longer then 32.".format(clsname, name)
                )
            if not isinstance(return_type, dict):
                yield CheckException(
                    "{}.streams' type_info: `{}` is not a dictionary"
                    .format(clsname, return_type)
                )
                return
            if 'type' not in return_type or 'description' not in return_type:
                yield CheckException(
                    "{}.streams' type: `{}` is not a proper dictionary "
                    "with 'type' and 'description'".format(clsname, return_type)
                )
                return
            if return_type['type'] not in PRIMITIVE_TYPE_REGISTRY:
                yield CheckException(
                    "{}.streams['type_info']['type'] type: `{}` is not one of "
                    "PRIMITIVE_TYPE_REGISTRY".format(clsname, return_type['type'])
                )
            desc = return_type['description']
            if not isinstance(desc, str):
                yield CheckException(
                    "{}.streams['type_info']['description']: `{}` is not a string"
                    .format(clsname, desc)
                )
            elif desc[-1] != '.' or not desc[0].isupper():
                yield CheckException(
                    "{}.streams['type_info']['description']: `{}` "
                    "should start with an uppercase and end with fullstop"
                    .format(clsname, desc)
                )


# Method %r is abstract in class %r but is not overridden.
# %s %r has no %r member. Attribute %r defined outside __init__
# pylint: disable=W0223, E1101, R0201
class SensorBase(object):
    '''
    Base class for all sensors in the system.

    This module provides base core for making sensors.

    config_schema is a JSONSchema for Sensor configuration.
        All schemas should validate dictionaries (objects).

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

    config_schema = {}

    @abstractproperty
    def name(self):
        '''Sensor's name. Max 32 chars, must match ^\\w{1,32}$'''
        pass

    @abstractproperty
    def streams(self):
        '''
        Sensor's streams.

        Sensor streams are defined as python :obj:`dict` (:class:`SensorBase.streams`)
        where keys are `names` (max. 32 character string) and values are dictionaries with two keys:
            'type' - corresponding :ref:`primitives`.
                Sensor can produce data associated with one of its
                streams (the data must be of type defined by associated stream).
            'description' - description of the stream

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
                'cpu': {
                    'type': CPUTuple,
                    'description': 'cpu stream description'
                },
                'my_stream': {
                    'type': float,
                    'description': 'my_stream description'
                }
            }

        This example is valid as long as `CPUTuple` is defined as :ref:`primitive
        <primitives>`.
        '''

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
        if not callable(send_results):
            raise InvalidSendResultsError("send_results param is not callable")
        self.do_send_results = send_results
        self.reload(config)
        self.storage = storage
        self.config_id = config_id

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
                'Error while merging schemas: config_schema in class `{}` '
                'should be valid against `meta_schema` `{}`'
                .format(self.__class__.__name__, err.message)
            )
            raise err

    def send_results(self, timestamp, data):
        '''
        do_send_results wrapper.
        Performs basic checks and calls do_send_results:
            * Is ``stream`` a valid name?
            * Is datatype secified by ``stream`` valid?
        If any of above checks fails, data is ignored.
        '''
        for stream, output in data:
            if stream not in self.streams:
                raise InvalidDataError(
                    "Sensor `{}` doesn't have stream `{}`. "
                    'Data ignored.'.format(self.__class__.name, stream)
                )
            stream_type = self.streams[stream]['type']
            if not isinstance(output, stream_type):
                raise InvalidDataError(
                    "Datatype returned by sensor `{}` doesn't match "
                    'datatype declared in stream `{}`. Got {!r}, '
                    'expected `{!r}`. Data ignored.'
                    .format(
                        self.__class__.name,
                        stream,
                        type(output),
                        stream_type
                    )
                )
            if not PRIMITIVE_TYPE_REGISTRY.is_valid_type(stream_type):
                raise InvalidDataError(
                    'Datatype {!r} of stream `{}` in sensor `{}` is not '
                    'valid *primitive*. Data ignored.'
                    .format(
                        stream_type,
                        stream,
                        self.__class__.name
                    )
                )
        self.do_send_results(timestamp, data)

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

'''
Base classes for all sensors.

.. _Sensor:

Sensor
======

Sensor is a piece of software which is responsible for measuring/gathering data
about a `target host`.

Requirements
------------

* There are two type of sensors:

 * task sensor - sensor runs at defined schedule or interval, returns output
   immediately.

   HINT: task sensor can be run as *event sensor* (using wrapper).

 * event sensor - sensor once started is running for a long time. It returns
   output only when some event occurs. The output is received through callback.

* streams - available sensor outputs.

  Stream is defined by a `name` (string) and `primitive`. It means that sensor
  can produce data to one of defined streams. These data type has to be the
  same as defined for this stream.

  If sensor produces data for a stream with another type than defined it is
  treaded as `sensor is badly written`.

* error channel - each sensor has an `error` channel (this name is reserved and
  must not be overridden while declaring streams). The type of error channel is
  defined in `primitives`.

* configuration:

  * internal configuration - what every sensor must have defined (those
    configuration instruct agent how and when to run the sensor)

    * max running time

      * task sensor - if sensor runs for a longer time that this value it
        will be killed by an agent.

      * event sensor - if sensor does not send heartbeat for time longer than
        this value it will be killed by an agent.

    * schedule

      * `int` (seconds) - how often sensor must be called

      * `str` (cron format) - when sensor must be called exactly (FUTURE)

    * overlap - should sensor be run another time if previous call not ended
      yet (default: false)

  * external configuration - additional custom sensor configuration

    This must be simple JSON like dictionary with sensor configuration (dict,
    list, int, float, unicode)


Task sensor requirements
~~~~~~~~~~~~~~~~~~~~~~~~

Event sensor requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

  Long running sensors must have some heartbeat mechanism!

Sensor metadata and code
------------------------

Sensor code is needed only in two places. On agent (to run the code) and on
ConfDB node (to store metadata about sensors). Other nodes should communicate
to ConfDB to ask about sensors.

'''
from .base import AdvancedSensorBase, TaskSensorBase

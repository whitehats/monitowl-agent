# -*- coding: utf-8 -*-
'''
.. _agent:
.. _client:


Agent (client)
==============

Agent:

    * uses sensors to gather the data from the system (or remote locations)

    * sends gathered data to collector


Requirements
------------

Agent is a program which does following tasks:

* manages sensors (processes)

  Each sensor is separate process - sensor crash/deadlock should have no effect
  on agent.

  * each agent `has` a fake sensor `agent` which produce data about agent
    itself (like configuration changes, agent errors etc.). These are stored in
    LogDB as any sensor data. It is internal logging and error channel.

    It is an internal logging and error channel for an agent.
    Instead of making sensor for reporting agent status, agent can just log
    internal state as `agent` sensor.

  * runs task sensors (agent has a schedule, runs sensor on time and gathers
    output)

  * runs event sensors (agent passes the ``return data on event`` callback to
    allow return output from sensor when event will occur)

  * keeps sensors running

    * if sensor dies it should be restarted

    * if sensor dies several times in a row it is marked as broken

    * if sensor does not response for a long time it should be killed (if this
      situation happens several times, sensor should be marked as broken)

  * agent must catch all sensor errors and report that errors to sensors
    `error` channel

    Errors like syntax errors, requirement error, initialization error, wrong
    stream type error should be reported and sensor should be stopped.

  * agent must kill all children processes when it dies or exists

  * agent must kill all children processes if sensor exits

  * gathers data from sensors

  * stores gathered data in a local cache in case of transmission errors or
    collector unavailability

* sends gathered data to collector:

  * SSL certificates authentication (client and server authentication)

  * HTTP(S) (websocket or REST)

* receives commands from collector:

  * to pull new configuration

  * to flush local cache and send all gathered data to collector

  * to restart

  * to drop local cache (forgot the data)



Secure communication
--------------------
Agent during initialization:

* generates ssl key and CSR
* uploads CSR to Collector
* pools Collector asking for signed CRT

Server has main CA and sub-CA for each group of agents. UI presents list of accepted agent crt
and pending verify requests. User can verify crt by selecting which sub-CA will sign the CSR.
Server maintains a list [agent_crt, agent_id] so Collector can verify if incoming data is proper.

This approach is very similar to Puppet solution:
 http://www.masterzen.fr/2010/11/14/puppet-ssl-explained/

Ideas for future
----------------

* [rejected] ``timeout`` parameter for data sending [now LogDB can resolve
  ``missing`` data reading configuration and facts]

* [rejected] send configuration changes to LogDB, gather it from ConfDB
  (through Collector) [now while applying new changes to ConfDB, data should be
  automatically saved to LogDB, if not LogDB reject the data from agents]

* TCP/UDP - sometimes performance is priority so UDP needs to be used and
  only the newest data needs to be send without storing it in local cache
  (requested by an IT-SA 2013 visitor)

* agent must send mail (alarm the administrator)

  * when error channel cannot be accessed (due to policy? mobiles?)

  * when there are transmission errors (client/server versions/serializations
    mismatch?)

  * what to do on sensor error?

  * what to do on agent error?

'''

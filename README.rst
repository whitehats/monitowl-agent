`MonitOwl`_ Agent
-----------------

This is a part of `MonitOwl`_ - monitoring software. This repository contains only monitowl-agent - part that is responsible for:

1. Collecting the data from hardware (like S.M.A.R.T. from hard drives)
2. Collecting the data from operating system (network traffic, iostats, processes or user activity, system logs)
3. Collecting the data from installed software (software logs)
4. Collecting the data from remote network devices
5. Sending packed and encrypted data packages to MonitOwl server

Security
========

All of the agent<->server communication is done with HTTPS.

Agent needs a *ca.crt* file with CA that signed server certificate. This way agent ensures that server connection is not spoofed.

During initalization agent generates *key* and *csr*, then asks server to sign it and downloads *crt* file. This way server can be sure that agent connection is not spoofed.

Installation
============

You will need two informations:

1. MonitOwl instance frontend server URL (ex: *https://cusomer.monitowl.com*).
2. MonitOwl instance CA certificate. Both of them will be provided to you by our sales team.

Using setuptools
^^^^^^^^^^^^^^^^

::

    $ git clone https://github.com/whitehats/monitowl-agent.git
    $ python setup.py install
    $ monitowl-agent -r --webapi-url $SERVER_URL --logs-max_size 10000000

Running manually
^^^^^^^^^^^^^^^^

::

    $ git clone https://github.com/whitehats/monitowl-agent.git
    $ pip install -r requirements.txt
    $ ./run_agent -r --webapi-url $SERVER_URL --logs-max_size 10000000

**Note**: Either way, we strongly recommend using python *virtualenv* to run dependency packages.

Automatic deployment
^^^^^^^^^^^^^^^^^^^^

We do support ansible, chef, puppet and cloud-init scripts. If your desired method is missing, please contact our support team.

Development
===========

We welcome contributions to our open source projects. The MonitOwl team has it's own internal git repository where the real development is done. Github repository is synchronized periodically (usually once a month).

The MonitOwl Agent is licensed under the Apache License 2.0. Details can be found in the LICENSE file.

Support
=======

This software is released as-is. MonitOwl provides warranty and support on this software only for own customers, according to selected support package. If you have any issues with the software, please feel free to post an Issue on our Issues page.

.. _MonitOwl: http://monitowl.com

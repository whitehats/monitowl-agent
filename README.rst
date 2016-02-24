.. image:: https://travis-ci.org/whitehats/monitowl-agent.svg?branch=master
    :target: https://travis-ci.org/whitehats/monitowl-agent

.. image:: https://codecov.io/github/whitehats/monitowl-agent/coverage.svg?branch=master
    :target: https://codecov.io/github/whitehats/monitowl-agent?branch=master

`MonitOwl`_ Agent
-----------------

This is a part of `MonitOwl`_ - monitoring software. This repository contains monitowl-agent - part that is responsible for:

1. Collecting the data from hardware (like S.M.A.R.T. from hard drives)
2. Collecting the data from operating system (network traffic, iostats, processes or user activity, system logs)
3. Collecting the data from installed software (software logs)
4. Collecting the data from remote network devices
5. Sending packed and encrypted data packages to MonitOwl server


Installation
============

Before you start ensure that you have MonitOwl instance frontend server address (ex: *https://customer.monitowl.com*).


Using single executable (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Single command

::

    $ curl -L https://github.com/whitehats/monitowl-agent/raw/master/install.sh | sudo sh -s URL

where ``URL`` should be replaced with MonitOwl instance frontend server address (see above).

This will:

1. Download the latest monitowl-agent release (from `here`_).
2. Update (or create) a configuration file pointing at ``URL``.
3. Detect your init system and install appropriate init script/service.
4. (Re)start the monitowl-agent system service.

Building the executable yourself
################################

::

    $ git clone https://github.com/whitehats/monitowl-agent.git
    $ cd monitowl-agent
    $ pip install -r requirements.txt
    $ pip install pyinstaller
    $ pyinstaller bundle.spec

The resulting file will be in ``dist/monitowl-agent``.

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

Security
========

All of the agent<->server communication is done with HTTPS. Agent needs a *ca.crt* file with CA that signed server certificate. This way agent ensures that server connection is not spoofed. During initalization agent generates *key* and *csr*, then asks server to sign it and downloads *crt* file. This way server can be sure that agent connection is not spoofed.

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
.. _here: https://github.com/whitehats/monitowl-agent/releases

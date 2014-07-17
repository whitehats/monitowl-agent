"""
Agent tests
"""

from unittest import TestCase, skip
from mock import MagicMock, patch
from whmonit.client.agent import Agent, Sensor
import time
import os
import multiprocessing
import BaseHTTPServer


@patch('whmonit.client.agent.StorageManager', MagicMock())
class AgentTest(TestCase):
    # too many public methods
    # pylint: disable=R0904
    """Agent unit tests."""

    def setUp(self):
        # invalid name
        # pylint: disable=C0103
        self.config_path_nonexistent = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "agentconfig.yaml_nonexist"
        )
        self.config_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "agentconfig.yaml_correct"
        )
        #set configfile to non-exist file
        if os.path.isfile(self.config_path_nonexistent):
            os.remove(self.config_path_nonexistent)

    def test_load_non_exist(self):
        """Try to save nonexistent config."""
        Agent(self.config_path_nonexistent,
              'dzik1',
              'http://localhost:8000',
              'ws://localhost:8080',
              '.agentdata.db',
              './')

    @skip("test is invalid, jenkins crashing on it")
    def test_loadsaveconf(self):
        """Try to load and save config."""
        agent = Agent(self.config_path, 'dzik1', 'http://localhost:8000')
        agent.configfile = self.config_path_nonexistent
        agent.save_config(agent.agentconfig)

        if not os.path.isfile(self.config_path_nonexistent):
            assert False

    @skip("test is invalid, jenkins crashing on it")
    def test_check_connection(self):
        """test check_connection"""
        agent = Agent(self.config_path, 'dzik1', 'http://localhost:8000')
        agent.check_connection()
        #TODO: mock collector


class SensorTest(TestCase):
    # too many public methods
    # pylint: disable=R0904
    """SensorProc unit tests."""

    def setUp(self):
        # invalid name
        # pylint: disable=C0103
        self.queue = multiprocessing.Queue()

        self.sensorproc = Sensor(
            self.queue,
            "uptime",
            {"frequency": 1, 'run_timeout': 5},
            "config_id",
            "target",
            "target_id",
            MagicMock(),
        )

    def test_runsensor(self):
        """Run a sensorproc and check if it produces data."""
        self.sensorproc.start()

        time.sleep(4)
        self.sensorproc.terminate()
        assert self.queue.get(timeout=3)

    def test_put2queue(self):
        """Check if putting data in queue works."""
        msg = {
            'config_id': "sdsdfsdf",
            'data': 1.1,
            'datatype': float,
            'timestamp': time.time(),
            'stream_name': "default",
        }
        self.queue.put(msg)

        assert self.queue.get(timeout=3)


@skip("#247 disabled because it produces logging output in subprocess")
class CommProcTest(TestCase):
    # too many public methods
    # pylint: disable=R0904
    """Communication protocol unit tests."""

    def test_runsensor(self):
        """Run a CommProc and test if it tries to send data."""

        self.data = 0

        def handle_req(request, client_addr, server):
            """Handles requests between client and server."""
            # unused argument
            # pylint: disable=W0613
            self.data += 1

        httpd = BaseHTTPServer.HTTPServer(('', 0), handle_req)

        print("port: %s" % httpd.server_address[1])
        queue = multiprocessing.Queue()
        commproc = CommProc(
            queue,
            "http://localhost:%s" % httpd.server_address[1],
            "0123-agent_id"
        )

        cprocess = multiprocessing.Process(target=commproc.run)
        cprocess.start()

        msg = {
            'target_id': "012_target_id",
            'sensor': "test_sensorname",
            'config_id': "0123_config_id",
            'config': "{}",
            'data': "0123_i_the_data",
            'datatype': "str",
            'timestamp': time.time(),
        }
        queue.put(msg)
        httpd.handle_request()
        cprocess.terminate()

        assert self.data > 0

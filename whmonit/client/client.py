''' Create Agent instance, configure and let it run '''
import sys
import os
import time
import argparse
import logging
import hashlib
import yaml
from socket import gethostname
from uuid import getnode as mac_addr
from furl import furl
from OpenSSL import crypto

from whmonit.client.agent import Agent
from whmonit.common.log import LogFileHandler, getLogger


CERT_FILE = "agent.crt"
CSR_FILE = "agent.csr"
KEY_FILE = "agent.key"

LOG = getLogger('client')


def init_crypto():
    '''
    Generate private key and CSR for secure communication
    '''
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    req = crypto.X509Req()
    subj = req.get_subject()
    subj.C = "PL"
    subj.ST = "Dolnyslask"
    subj.L = "Wroclaw"
    subj.O = "MonitOwl Agents"
    subj.OU = "Agents"
    subj.CN = gethostname()

    req.set_pubkey(key)
    req.sign(key, 'sha1')

    with open(CSR_FILE, "wt", 0o400) as fileh:
        fileh.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))
    with open(KEY_FILE, "wt", 0o400) as fileh:
        fileh.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    LOG.info("Crypto files Key and CSR created")


def main(args):
    '''
    this will be lanched when user run this from cmd line
    '''
    # R0912: Too many branches
    # R0915: Too many statements
    # pylint: disable=R0912,R0915
    parser = argparse.ArgumentParser()

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '-r', '--run',
        action='store_const',
        dest='action',
        const='run',
        help="run agent in long running mode",
    )
    action_group.add_argument(
        '--get-config',
        action='store_const',
        dest='action',
        const='get_config',
        help="",
    )
    action_group.add_argument(
        '--check-connection',
        action='store_const',
        dest='action',
        const='checkconn',
        help="check connectivity to server (with auth)",
    )
    action_group.add_argument(
        '--request-certificate-sign',
        action='store_const',
        dest='action',
        const='csr',
        help="send certificate signing request to server",
    )
    action_group.add_argument(
        '--fetch-certificate',
        action='store_const',
        dest='action',
        const='fetch_cert',
        help="fetch signed certificate from WebApi",
    )
    action_group.add_argument(
        '--initialize',
        action='store_const',
        dest='action',
        const='initialize',
        help="init agent configuration (create crypto keys)",
    )
    action_group.add_argument(
        '--test-sensors',
        dest='sensor_config',
        default=None,
        type=yaml.load,
        nargs=2,
        metavar=('SENSOR_NAME', 'CONFIG_DICT'),
        help='''test sensors without connecting to webapi,
            example usage: btscan "{'sampling_period':6}" ''',
    )

    debug_group = parser.add_argument_group('Logging')
    debug_group.add_argument(
        '-l', '--level',
        action='store',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        dest='level',
        default='error',
        help="change logging level (default: error). "
    )
    debug_group.add_argument(
        '-v', '--verbose',
        action='store_const',
        dest='level',
        const='info',
        help="shortcut for -l info",
    )
    debug_group.add_argument(
        '-d', '--debug',
        action='store_const',
        dest='level',
        const='debug',
        help="shortcut for -l debug",
    )
    debug_group.add_argument(
        '--logs',
        action='store',
        dest='logs',
        metavar='FILENAME',
        help="Log to file instead of write to stderr.",
    )
    debug_group.add_argument(
        '--logs-max_size',
        action='store',
        dest='max_logs_size',
        help="Disk space limit for log files in bytes.",
        type=int
    )
    debug_group.add_argument(
        '--logs-max_files',
        action='store',
        dest='max_logs',
        help="Maximum number of stored log files.",
        type=int
    )

    parser.add_argument(
        '-c', '--config-path',
        dest='config_filename',
        default=".agentconfig.yaml",
        help="config file to use (try to use absolute paths to avoid surprises)",
    )

    parser.add_argument(
        '--webapi-url',
        dest='webapi_address',
        help='WebApi address',
    )

    parser.add_argument(
        '--id',
        dest='agent_id',
        help='agent id (must be valid, hexdigest sha1 hash)',
        default=hashlib.sha1('{}{}'.format(gethostname(), mac_addr())).hexdigest()
    )

    parser.add_argument(
        '--dbpath',
        dest='sqlite_path',
        help='Path to buffer database file.',
        default='.agentdata.db'
    )
    parser.add_argument(
        '--certs-dir',
        dest='certs_dir',
        help='Path to certificates directory.',
        default='./'
    )

    values = parser.parse_args(args)

    do_test = values.sensor_config

    if not (do_test or values.webapi_address):
        parser.error(
            'Please specify --test-sensors or --webapi-url.'
        )

    LOG.setLevel(getattr(logging, values.level.upper()))
    if values.logs:
        kwargs = {
            key: val for key, val in [
                ('filename', values.logs),
                ('backup_count', values.max_logs),
                ('max_disk_space', values.max_logs_size)
            ]
            if val
        }
        chlr = LogFileHandler(**kwargs)
        chlr.setLevel(getattr(logging, values.level.upper()))
        LOG.addHandler(chlr)
        LOG.propagate = False

    if values.action == 'initialize':
        init_crypto()
        return

    collector_address = furl().set(scheme='https', host=values.webapi_address, path='collector').url
    webapi_address = furl().set(scheme='wss', host=values.webapi_address).url
    # run action
    agent = Agent(values.config_filename,
                  values.agent_id,
                  collector_address,
                  webapi_address,
                  values.sqlite_path,
                  values.certs_dir)

    if not do_test:
        if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
            init_crypto()

        # TODO #1153: action for single attempt to fetch CRT
        if not os.path.exists(CERT_FILE):
            agent.request_certificate()
            while not agent.fetch_certificate():
                time.sleep(10)

    if values.action == 'run':
        agent.run()
    elif values.action == 'get_config':
        agent.get_remote_config()
    elif values.action == 'checkconn':
        agent.check_connection()
    elif values.action == 'csr':
        agent.request_certificate()
    elif values.action == 'fetch_cert':
        agent.fetch_certificate()
    elif values.sensor_config:
        agent.sensor_test(values.sensor_config[0], values.sensor_config[1])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

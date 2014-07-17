""" Create Agent instance, configure and let it run """
import sys
import os
import time
import optparse
import logging
import hashlib
from OpenSSL import crypto
from socket import gethostname

from whmonit.client.agent import Agent


CERT_FILE = "agent.crt"
CSR_FILE = "agent.csr"
KEY_FILE = "agent.key"

# TODO: agent should be rewritten using supervisor or other method to control
# processes


def init_crypto():
    """
    Generate private key and CSR for secure communication
    """
    log = logging.getLogger('monitowl.client')
    if not (os.path.exists(CERT_FILE) or os.path.exists(CSR_FILE) or os.path.exists(KEY_FILE)):
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

        with open(CSR_FILE, "wt") as fileh:
            fileh.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))
        with open(KEY_FILE, "wt") as fileh:
            fileh.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        log.debug("Key and CSR created")
        #TODO: take care of file permissions
        #TODO: transfer the CSR to the collector

    else:
        log.error("One or more crypto files already exist!")


def main(args):
    """
    this will be lanched when user run this from cmd line
    """
    oparser = optparse.OptionParser()

    action_group = optparse.OptionGroup(oparser, "Actions")
    action_group.add_option(
        '-r', '--run',
        action='store_const',
        dest='action',
        const='run',
        help="run agent in long running mode",
    )
    action_group.add_option(
        '--get-config',
        action='store_const',
        dest='action',
        const='get_config',
        help="",
    )
    action_group.add_option(
        '--check-connection',
        action='store_const',
        dest='action',
        const='checkconn',
        help="check connectivity to server (with auth)",
    )
    action_group.add_option(
        '--request-certificate-sign',
        action='store_const',
        dest='action',
        const='csr',
        help="send certificate signing request to server",
    )
    action_group.add_option(
        '--fetch-certificate',
        action='store_const',
        dest='action',
        const='fetch_cert',
        help="fetch signed certificate from WebApi",
    )
    action_group.add_option(
        '--initialize',
        action='store_const',
        dest='action',
        const='initialize',
        help="init agent configuration (create crypto keys)",
    )

    oparser.add_option_group(action_group)

    debug_group = optparse.OptionGroup(oparser, "Logging")
    debug_group.add_option(
        '-l', '--level',
        action='store',
        type='choice',
        choices=['debug', 'info', 'warning', 'error', 'none', 'quiet'],
        dest='level',
        default='error',
        help="change logging level (default: error). "
        "Choices: quiet, error, warning, info, verbose, debug"
    )
    debug_group.add_option(
        '-v', '--verbose',
        action='store_const',
        dest='level',
        const='info',
        help="shortcut for -l info",
    )
    debug_group.add_option(
        '-d', '--debug',
        action='store_const',
        dest='level',
        const='debug',
        help="shortcut for -l debug",
    )
    debug_group.add_option(
        '-q', '--quiet',
        action='store_const',
        dest='level',
        const='quiet',
        help="shortcut for -l quiet",
    )
    debug_group.add_option(
        '--logs',
        action='store',
        dest='logs',
        metavar='FILENAME',
        help="Log to file instead of write to stderr.",
    )

    oparser.add_option_group(debug_group)
    oparser.add_option(
        '-c', '--config',
        dest='config_filename',
        default=".agentconfig.yaml",
        help="config file to use (try to use absolute paths to avoid surprises)",
    )

    oparser.add_option(
        '--collector-url',
        dest='server_address',
        help='server (collector) address',
    )
    oparser.add_option(
        '--webapi-url',
        dest='webapi_address',
        help='WebApi address',
    )

    # TODO: #1164: Rename `agent name` to `agent id`
    oparser.add_option(
        '-n', '--name',
        dest='agent_name',
        help='agent name (must be valid, hexdigest sha1 hash)',
        default=hashlib.sha1(gethostname()).hexdigest()
    )

    oparser.add_option(
        '--dbpath',
        dest='sqlite_path',
        help='Path to buffer database file.',
        default='.agentdata.db'
    )
    oparser.add_option(
        '--certs-dir',
        dest='certs_dir',
        help='Path to certificates directory.',
        default='./'
    )

    args, _ = oparser.parse_args(args)

    # TODO: configure logging acording to args
    log = logging.getLogger('monitowl.client')
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s(%(process)d) %(levelname)s %(message)s')
    chlr = logging.StreamHandler()
    chlr.setLevel(logging.DEBUG)
    chlr.setFormatter(formatter)
    log.addHandler(chlr)

    if not args.action:
        print >> sys.stderr, "Please use --help to list avalible options."
        sys.exit(1)

    if not args.server_address or not args.webapi_address:
        print >> sys.stderr, "Please specify server urls (--collector-url and --webapi-url)."
        sys.exit(1)

    if args.action == 'initialize':
        init_crypto()
        return

    # run action
    agent = Agent(args.config_filename,
                  args.agent_name,
                  args.server_address,
                  args.webapi_address,
                  args.sqlite_path,
                  args.certs_dir)

    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        init_crypto()
    # TODO #1153: action for single attempt to fetch CRT
    if not os.path.exists(CERT_FILE):
        agent.request_certificate()
        while True:
            # W0703: Catching too general exception Exception
            # pylint: disable=W0703
            try:
                if agent.fetch_certificate():
                    break
            except Exception as ex:
                print >> sys.stderr, "Exception:", ex
            time.sleep(10)

    if args.action == 'run':
        agent.run()
    elif args.action == 'get_config':
        agent.get_remote_config()
    elif args.action == 'checkconn':
        agent.check_connection()
    elif args.action == 'csr':
        agent.request_certificate()
    elif args.action == 'fetch_cert':
        agent.fetch_certificate()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


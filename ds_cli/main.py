"""Datashark CLI entry point
"""
import sys
from json import dumps
from argparse import ArgumentParser
import requests
from ds_core import BANNER
from ds_core.config import CONFIG
from ds_core.logging import LOGGING_MANAGER
from . import LOGGER


def print_resp(resp):
    try:
        resp.raise_for_status()
        print(dumps(resp.json(), indent=2))
    except requests.HTTPError as exc:
        LOGGER.error(exc)


def info_cmd(args):
    url = f'{args.base_url}/info'
    LOGGER.info("GET %s", url)
    print_resp(requests.get(url, auth=args.auth))


def process_cmd(args):
    url = f'{args.base_url}/process'
    data = {'filepath': args.filepath}
    LOGGER.info("POST %s (%s)", url, data)
    print_resp(requests.post(url, auth=args.auth, data=data))


def parse_args():
    parser = ArgumentParser(description="Datashark Command Line Interface")
    parser.add_argument('--debug', '-d', action='store_true')
    parser.add_argument(
        '--host',
        default=CONFIG.get_('datashark', 'cli', 'host', default='127.0.0.1'),
    )
    parser.add_argument(
        '--port',
        default=CONFIG.get_('datashark', 'cli', 'port', default=13740),
    )
    parser.add_argument(
        '--scheme',
        default=CONFIG.get_('datashark', 'cli', 'scheme', default='http'),
    )
    parser.add_argument(
        '--user',
        default=CONFIG.get_('datashark', 'cli', 'user', default='user'),
    )
    parser.add_argument(
        '--pswd',
        default=CONFIG.get_('datashark', 'cli', 'pswd'),
    )
    cmd = parser.add_subparsers(dest='cmd')
    cmd.required = True
    info = cmd.add_parser('info')
    info.set_defaults(func=info_cmd)
    process = cmd.add_parser('process')
    process.set_defaults(func=process_cmd)
    process.add_argument('filepath')
    return parser.parse_args()


def app():
    """Application entry point"""
    LOGGER.info(BANNER)
    args = parse_args()
    LOGGING_MANAGER.set_debug(args.debug)
    args.auth = requests.auth.HTTPBasicAuth(args.user, args.pswd)
    args.base_url = f'{args.scheme}://{args.host}:{args.port}'
    LOGGER.info("base url: %s", args.base_url)
    exitcode = 0
    try:
        exitcode = args.func(args)
    except requests.ConnectionError:
        LOGGER.error("failed to connect to datashark service!")
        exitcode = 2
    except:
        LOGGER.exception("unexpected exception!")
        exitcode = 1
    sys.exit(exitcode)

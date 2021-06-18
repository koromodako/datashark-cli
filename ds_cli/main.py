"""Datashark CLI entry point
"""
import sys
from json import dumps
from pathlib import Path
from argparse import ArgumentParser
from yarl import URL
import requests
from ds_core import BANNER
from ds_core.config import DSConfiguration, DEFAULT_CONFIG_PATH
from ds_core.logging import LOGGING_MANAGER
from . import LOGGER


def print_resp(resp):
    try:
        resp.raise_for_status()
        print(dumps(resp.json(), indent=2))
    except requests.HTTPError as exc:
        LOGGER.error(exc)
        return exc.response.status_code
    return 0


def info_cmd(args):
    url = args.base_url.with_path('/info')
    LOGGER.info("GET %s", url.human_repr())
    return print_resp(requests.get(url, auth=args.auth))


def process_cmd(args):
    url = args.base_url.with_path('/process')
    data = {'filepath': args.filepath}
    LOGGER.info("POST %s (%s)", url.human_repr(), data)
    return print_resp(requests.post(url, auth=args.auth, json=data))


def parse_args():
    parser = ArgumentParser(description="Datashark Command Line Interface")
    parser.add_argument(
        '--debug', '-d', action='store_true', help="Enable debugging"
    )
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Configuration file",
    )
    cmd = parser.add_subparsers(dest='cmd')
    cmd.required = True
    info = cmd.add_parser('info')
    info.set_defaults(func=info_cmd)
    process = cmd.add_parser('process')
    process.set_defaults(func=process_cmd)
    process.add_argument('filepath')
    args = parser.parse_args()
    args.config = DSConfiguration(args.config)
    return args


def run(args):
    LOGGING_MANAGER.set_debug(args.debug)
    args.auth = requests.auth.HTTPBasicAuth(
        args.config.get('datashark.cli.username', default='user'),
        args.config.get('datashark.cli.password'),
    )
    args.base_url = URL.build(
        scheme=args.config.get('datashark.cli.scheme', default='http'),
        host=args.config.get('datashark.cli.host', default='127.0.0.1'),
        port=args.config.get('datashark.cli.port', default=13740),
    )
    LOGGER.info("base url: %s", args.base_url.human_repr())
    return args.func(args)


def app():
    """Application entry point"""
    LOGGER.info(BANNER)
    args = parse_args()
    exitcode = 0
    try:
        exitcode = run(args)
    except requests.ConnectionError:
        LOGGER.error("failed to connect to datashark service!")
        exitcode = 2
    except:
        LOGGER.exception("unexpected exception!")
        exitcode = 1
    sys.exit(exitcode)

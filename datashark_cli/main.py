"""Datashark CLI entry point
"""
import ssl
from asyncio import run
from pathlib import Path
from getpass import getpass
from argparse import ArgumentParser
from aiohttp import TCPConnector, ClientSession, ClientTimeout
from datashark_core import BANNER
from datashark_core.config import DatasharkConfiguration, override_arg
from datashark_core.logging import LOGGING_MANAGER
from datashark_core.filesystem import get_workdir
from . import LOGGER
from .command import setup as setup_commands
from .agent_api import AgentAPI


def _agents_list(val):
    return val.split(',')


def parse_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Datashark Command Line Interface")
    parser.add_argument(
        '--debug', '-d', action='store_true', help="Enable debugging"
    )
    parser.add_argument(
        '--config',
        '-c',
        type=DatasharkConfiguration,
        help="Path to Datashark configuration file",
    )
    parser.add_argument(
        '--agents',
        '-a',
        type=_agents_list,
        help="Comma separated list of agent's addresses e.g. host_0:port,host_1:port,...",
    )
    parser.add_argument('--ca', help="Server CA certificate")
    parser.add_argument('--key', help="Client private key")
    parser.add_argument('--cert', help="Client certificate")
    parser.add_argument(
        '--ask-pass',
        action='store_true',
        help="Ask for client private key password",
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help="Limit of simultaneous connections overall",
    )
    parser.add_argument(
        '--limit-per-host',
        type=int,
        default=10,
        help="Limit of simultaneous connections to the same endpoint, 0 means unlimited",
    )
    cmd = parser.add_subparsers(dest='cmd', help="Command to invoke")
    cmd.required = True
    setup_commands(cmd)
    args = parser.parse_args()
    args.agents = override_arg(
        args.agents,
        args.config,
        'datashark.cli.agents',
        default=['localhost:13740'],
    )
    args.ca = override_arg(args.ca, args.config, 'datashark.cli.ca')
    if args.ca:
        args.ca = Path(args.ca)
    args.key = override_arg(args.key, args.config, 'datashark.cli.key')
    if args.key:
        args.key = Path(args.key)
    args.cert = override_arg(args.cert, args.config, 'datashark.cli.cert')
    if args.cert:
        args.cert = Path(args.cert)
    return args


def prepare_ssl_context(args):
    """Prepare SSL context"""
    if not args.ca or not args.key or not args.cert:
        return None
    # prepare ssl context to authenticate server
    ssl_context = ssl.create_default_context(
        ssl.Purpose.SERVER_AUTH, cafile=str(args.ca)
    )
    # prepare ssl context to send client certificate to server
    password = None
    if args.ask_pass:
        password = getpass("Enter client private key password: ")
    ssl_context.load_cert_chain(
        certfile=str(args.cert),
        keyfile=str(args.key),
        password=password,
    )
    return ssl_context


async def start_session(args):
    """Start a client session and run command handler"""
    ssl_context = prepare_ssl_context(args)
    # build agent URL list depending on ssl_context
    scheme = 'https' if ssl_context else 'http'
    args.agents = [AgentAPI(f'{scheme}://{agent}/') for agent in args.agents]
    # create TCP connector using custom ssl context
    connector = TCPConnector(
        limit=args.limit,
        ssl_context=ssl_context,
        limit_per_host=args.limit_per_host,
    )
    client_timeout = ClientTimeout(
        total=12 * 60 * 60, connect=60, sock_connect=None, sock_read=None
    )
    client_session = ClientSession(
        timeout=client_timeout, connector=connector, raise_for_status=True
    )
    async with client_session as session:
        await args.async_func(session, args)


def app():
    """Application entry point"""
    LOGGER.info(BANNER)
    args = parse_args()
    if not args:
        return
    LOGGING_MANAGER.set_debug(args.debug)
    LOGGER.debug("command line arguments: %s", args)
    # check workdir
    try:
        LOGGER.info("working directory: %s", get_workdir(args.config))
    except ValueError as exc:
        LOGGER.critical(str(exc))
        return
    # run asynchronous function
    run(start_session(args))

"""Datashark CLI entry point
"""
import ssl
from asyncio import run
from pathlib import Path
from getpass import getpass
from argparse import ArgumentParser
from yarl import URL
from aiohttp import TCPConnector, ClientSession
from datashark_core import BANNER
from datashark_core.config import DatasharkConfiguration, override_arg
from datashark_core.logging import LOGGING_MANAGER
from .command import setup as setup_commands
from . import LOGGER


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
        nargs='+',
        help="Base URLs (scheme://host:port) of processing agents",
    )
    parser.add_argument('--ca', help="Server CA certificate")
    parser.add_argument('--key', help="Client private key")
    parser.add_argument('--cert', help="Client certificate")
    parser.add_argument(
        '--ask-pass',
        action='store_true',
        help="Ask for client private key password",
    )
    cmd = parser.add_subparsers(dest='cmd', help="Command to invoke")
    cmd.required = True
    setup_commands(cmd)
    args = parser.parse_args()
    args.agents = [
        URL(agent)
        for agent in override_arg(
            args.agents,
            args.config,
            'datashark.cli.agents',
            default=['http://localhost:13740'],
        )
    ]
    args.ca = Path(
        override_arg(
            args.ca,
            args.config,
            'datashark.cli.ca',
            input("Enter agents CA certificate path: "),
        )
    )
    if not args.ca.is_file():
        LOGGER.error("You must provide a valid agents CA certificate path!")
        return None
    args.key = Path(
        override_arg(
            args.key,
            args.config,
            'datashark.cli.key',
            input("Enter CLI key path: "),
        )
    )
    if not args.key.is_file():
        LOGGER.error("You must provide a valid CLI private key path!")
        return None
    args.cert = Path(
        override_arg(
            args.cert,
            args.config,
            'datashark.cli.cert',
            input("Enter CLI cert path: "),
        )
    )
    if not args.cert.is_file():
        LOGGER.error("You must provide a valid CLI certificate path!")
        return None
    return args


async def start_session(args):
    """Start a client session and run command handler"""
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
    # create TCP connector using custom ssl context
    connector = TCPConnector(ssl=ssl_context)
    with ClientSession(connector=connector) as session:
        await args.async_func(session, args)


def app():
    """Application entry point"""
    LOGGER.info(BANNER)
    args = parse_args()
    if not args:
        return
    LOGGING_MANAGER.set_debug(args.debug)
    LOGGER.debug("command line arguments: %s", args)
    run(start_session(args))

"""Datashark CLI entry point
"""
from asyncio import run
from getpass import getpass
from argparse import ArgumentParser
from functools import partial
from yarl import URL
from datashark_core import BANNER
from datashark_core.config import DatasharkConfiguration
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
        '--agents',
        '-a',
        nargs='+',
        help="Base URLs (scheme://host:port) of processing agents",
    )
    parser.add_argument(
        '--username',
        '-u',
        help="Username to authenticate with the agents"
    )
    parser.add_argument(
        '--config',
        '-c',
        type=DatasharkConfiguration,
        help="Path to Datashark configuration file",
    )
    cmd = parser.add_subparsers(dest='cmd', help="Command to invoke")
    cmd.required = True
    setup_commands(cmd)
    args = parser.parse_args()
    args.agents = [
        URL(agent) for agent in
        override_arg(
            args.agents,
            args.config,
            'datashark.cli.agents',
            default=['http://localhost:13740']
        )
    ]
    args.username = override_arg(
        args.username,
        args.config,
        'datashark.cli.username',
        default='user'
    )
    args.password = override_arg(
        None,
        args.config,
        'datashark.cli.password',
        default=partial(getpass, "Enter your password: ")
    )
    return args


def override_arg(arg, config, config_key, default):
    """Select best argument based on given arguments"""
    if arg:
        return arg
    if config:
        config_val = config.get(config_key, default=None)
        if config_val:
            return config_val
    if callable(default):
        return default()
    return default


def app():
    """Application entry point"""
    LOGGER.info(BANNER)
    args = parse_args()
    LOGGING_MANAGER.set_debug(args.debug)
    LOGGER.debug("command line arguments: %s", args)
    run(args.async_func(args))

"""Processors command
"""
from argparse import Namespace
from aiohttp import ClientSession
from datashark_core.logging import cprint

ALIASES = [
    ('ds-aliases', 'datashark -c {config} aliases'),
    ('ds-cook', 'datashark -c {config} cook'),
    ('ds-find', 'datashark -c {config} find'),
    ('ds-info', 'datashark -c {config} info'),
    ('ds-process', 'datashark -c {config} process'),
    ('ds-processors', 'datashark -c {config} processors'),
]

async def aliases_cmd(session: ClientSession, args: Namespace):
    """Aliases command implementation"""
    cprint("# datashark common aliases")
    for alias, command in ALIASES:
        cprint(f"alias {alias}='{command.format(config=args.config.filepath)}'")


def setup(subparsers):
    """Setup aliases command"""
    parser = subparsers.add_parser('aliases', help="Datashark aliases")
    parser.set_defaults(async_func=aliases_cmd)

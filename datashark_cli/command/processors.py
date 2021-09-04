"""Processors command
"""
from datashark_core.model.api import ProcessingRequest


async def processors_cmd(args):
    """Processors command implementation"""


def setup(subparsers):
    parser = subparsers.add_parser('processors', help="")
    parser.add_argument('search')
    parser.set_defaults(async_func=processors_cmd)

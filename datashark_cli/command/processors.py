"""Processors command
"""
from argparse import Namespace
from aiohttp import ClientSession
from datashark_core.logging import cprint, cwidth


async def processors_cmd(session: ClientSession, args: Namespace):
    """Processors command implementation"""
    for agent in args.agents:
        agent.display_banner()
        processors_resp = await agent.processors(session, args.search)
        if not processors_resp:
            continue
        for processor in processors_resp.processors:
            cprint(processor.get_docstring())
            cprint('-' * cwidth())


def setup(subparsers):
    """Setup processor"""
    parser = subparsers.add_parser('processors', help="")
    parser.add_argument('--search', '-s', help="")
    parser.set_defaults(async_func=processors_cmd)

"""Info command
"""
from argparse import Namespace
from aiohttp import ClientSession


async def info_cmd(session: ClientSession, args: Namespace):
    """Info command implementation"""
    for agent in args.agents:
        agent.display_banner()
        info_resp = await agent.info(session)
        if not info_resp:
            continue
        info_resp.display()


def setup(subparsers):
    """Setup info command"""
    parser = subparsers.add_parser('info', help="")
    parser.set_defaults(async_func=info_cmd)

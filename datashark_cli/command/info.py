"""Process command
"""
from datashark_core.model.api import AgentInfoResponse


async def info_cmd(session, args):
    """Process command implementation"""
    for agent in args.agents:
        url = agent / 'info'
        async with session.get(url) as a_resp:
            resp = AgentInfoResponse.build(await a_resp.json())
            print(resp)


def setup(subparsers):
    parser = subparsers.add_parser('info', help="")
    parser.set_defaults(async_func=info_cmd)

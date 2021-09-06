"""Process command
"""
from datashark_core.model.api import AgentInfoResponse


async def enumerate_agents_info(session, args):
    """Enumerate agent information"""
    for agent in args.agents:
        url = agent / 'info'
        async with session.get(url) as a_resp:
            yield agent, AgentInfoResponse.build(await a_resp.json())


async def info_cmd(session, args):
    """Process command implementation"""
    async for agent, agent_info in enumerate_agents_info(session, args):
        print('-' * 60)
        print(agent)
        print('-' * 60)
        agent_info.display()


def setup(subparsers):
    parser = subparsers.add_parser('info', help="")
    parser.set_defaults(async_func=info_cmd)

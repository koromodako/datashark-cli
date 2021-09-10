"""Processors command
"""
from aiohttp import ClientResponseError
from datashark_core.logging import cprint, cwidth, COLORED
from datashark_core.model.api import ProcessorsRequest, ProcessorsResponse
from .. import LOGGER


async def enumerate_agents_processors(session, args):
    """Enumerate agent information"""
    req = ProcessorsRequest(search=args.search)
    for agent in args.agents:
        url = agent / 'processors'
        try:
            async with session.post(url, json=req.as_dict()) as a_resp:
                resp = ProcessorsResponse.build(await a_resp.json())
                yield agent, resp.processors
        except ClientResponseError as exc:
            LOGGER.warning("%s:%d: %s", agent, exc.status, exc.message)


async def processors_cmd(session, args):
    """Processors command implementation"""
    async for agent, processors in enumerate_agents_processors(session, args):
        cprint('=' * cwidth())
        cprint(agent, highlight=True)
        cprint('=' * cwidth())
        for processor in processors:
            cprint(processor.get_docstring())
            cprint('-' * cwidth())


def setup(subparsers):
    parser = subparsers.add_parser('processors', help="")
    parser.add_argument('--search', '-s', help="")
    parser.set_defaults(async_func=processors_cmd)

"""Processors command
"""
from datashark_core.model.api import ProcessorsRequest, ProcessorsResponse


async def processors_cmd(session, args):
    """Processors command implementation"""
    req = ProcessorsRequest(search=args.search)
    for agent in args.agents:
        url = agent / 'processors'
        async with session.post(url, json=req.as_dict()) as a_resp:
            resp = ProcessorsResponse.build(await a_resp.json())
            print(resp)

def setup(subparsers):
    parser = subparsers.add_parser('processors', help="")
    parser.add_argument('--search', '-s', help="")
    parser.set_defaults(async_func=processors_cmd)

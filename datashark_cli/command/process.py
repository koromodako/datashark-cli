"""Process command
"""
from datashark_core.model.api import ProcessingRequest, ProcessingResponse


async def process_cmd(session, args):
    """Process command implementation"""


def setup(subparsers):
    parser = subparsers.add_parser('process', help="")
    parser.add_argument('filepath')
    parser.add_argument('processor')
    parser.set_defaults(async_func=process_cmd)

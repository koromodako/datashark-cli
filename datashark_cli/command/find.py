"""Find command
"""
import re
from argparse import Namespace
from aiohttp import ClientSession
from datashark_core.filesystem import get_workdir


async def find_cmd(_session: ClientSession, args: Namespace):
    """Find command implementation"""
    workdir = get_workdir(args.config)
    for filepath in workdir.rglob('*'):
        if args.pattern.search(str(filepath)):
            file_type = 'd' if filepath.is_dir() else 'f'
            relative_path = filepath.relative_to(workdir)
            print(f"{file_type} {relative_path}")


def setup(subparsers):
    """Setup find command"""
    parser = subparsers.add_parser('find', help="")
    parser.add_argument(
        'pattern', type=re.compile, help="Python re compatible pattern"
    )
    parser.set_defaults(async_func=find_cmd)

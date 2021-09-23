"""Datashark CLI commands
"""
from .cook import setup as setup_cook
from .find import setup as setup_find
from .info import setup as setup_info
from .process import setup as setup_process
from .processors import setup as setup_processors

SETUP_FUNC = [
    setup_cook,
    setup_find,
    setup_info,
    setup_process,
    setup_processors,
]


def setup(subparsers):
    """Setup commands"""
    for setup_func in SETUP_FUNC:
        setup_func(subparsers)

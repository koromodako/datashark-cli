"""Datashark CLI commands
"""
from .info import setup as setup_info
from .process import setup as setup_process
from .processors import setup as setup_processors


def setup(subparsers):
    """Setup commands"""
    setup_info(subparsers)
    setup_process(subparsers)
    setup_processors(subparsers)

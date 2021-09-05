"""Datashark CLI commands
"""
from .process import setup as setup_process
from .processors import setup as setup_processors


def setup(subparsers):
    """Setup commands"""
    setup_process(subparsers)
    setup_processors(subparsers)

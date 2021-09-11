"""Datashark CLI commands
"""
from .agents import setup as setup_agents
from .process import setup as setup_process
from .processors import setup as setup_processors


def setup(subparsers):
    """Setup commands"""
    setup_agents(subparsers)
    setup_process(subparsers)
    setup_processors(subparsers)

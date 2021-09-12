"""Process command
"""
from copy import deepcopy
from typing import List, Dict, Tuple, Iterator
from argparse import Namespace
from itertools import cycle
from collections import defaultdict
from aiohttp import ClientSession
from datashark_core.logging import cprint
from datashark_core.model.api import Processor
from .. import LOGGER
from ..agent_api import AgentAPI


class InitiateProcessingError(Exception):
    """Initiate processing error"""


async def build_processors_mappings(
    session: ClientSession, agents: List[AgentAPI]
) -> Tuple[Dict[str, Processor], Dict[str, Iterator[AgentAPI]]]:
    """For each processor, create a list of agents providing this processor"""
    proc_map = {}
    proc_agents_map = defaultdict(list)
    for agent in agents:
        proc_resp = await agent.processors(session, None)
        if not proc_resp:
            continue
        for processor in proc_resp.processors:
            proc_map[processor.name] = processor
            proc_agents_map[processor.name].append(agent)
    # turn agents lists into cycles
    proc_agents_map = {
        name: cycle(agents) for name, agents in proc_agents_map.items()
    }
    # return maps
    return proc_map, proc_agents_map


async def initiate_processing(
    session: ClientSession,
    proc_name: str,
    proc_arguments: List[Tuple[str, str]],
    proc_map: Dict[str, Processor],
    proc_agents_map: Dict[str, Iterator[AgentAPI]],
) -> bool:
    """Perform processing"""
    # attempt to retrieve processor
    processor = proc_map.get(proc_name)
    if not processor:
        raise InitiateProcessingError(
            f"cannot find an agent providing processor: {proc_name}"
        )
    # perform a deepcopy of processor because set_value changes the instance
    # and instance might be reused.
    processor = deepcopy(processor)
    # attempt to set processor arguments
    for name, value in proc_arguments:
        proc_arg = processor.get_arg(name)
        if not proc_arg:
            raise InitiateProcessingError(
                f"processor {proc_name} does not support argument: {name}"
            )
        proc_arg.set_value(value)
    # validate processor arguments
    if not processor.validate_arguments():
        raise InitiateProcessingError("arguments validation failed!")
    # arguments are valid, now we need to find an agent supporting this
    # processor and send a processing request to it
    agent = next(proc_agents_map[processor.name])
    processing_resp = await agent.process(session, processor)
    if not processing_resp:
        return False
    agent.display_banner()
    processing_resp.result.display()
    return processing_resp.result.status


async def process_cmd(session: ClientSession, args: Namespace):
    """Process command implementation"""
    # retrieve processors and agents supporting these processors
    proc_map, proc_agents_map = await build_processors_mappings(
        session, args.agents
    )
    # ask next available agent to perform processing
    try:
        if not await initiate_processing(
            session, args.processor, args.arguments, proc_map, proc_agents_map
        ):
            LOGGER.warning("agent-side processing failed.")
    except InitiateProcessingError as exc:
        LOGGER.error("error while initiating processing: %s", exc)


def _processor_argument(value: str):
    return tuple(value.split(':', 1))


def setup(subparsers):
    parser = subparsers.add_parser(
        'process', help="Process a file using an agent-side processor"
    )
    parser.add_argument(
        'processor', help="Name of the agent-side processor to run"
    )
    parser.add_argument(
        'arguments',
        metavar='argument',
        nargs='+',
        default=[],
        type=_processor_argument,
        help="Processor arguments",
    )
    parser.set_defaults(async_func=process_cmd)

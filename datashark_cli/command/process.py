"""Process command
"""
from secrets import choice
from collections import defaultdict
from datashark_core.logging import cprint
from .. import LOGGER


async def _build_mappings(session, args):
    """For each processor, create a list of agents providing this processor"""
    processor_map = {}
    processor_agents_map = defaultdict(list)
    for agent in args.agents:
        processors_resp = await agent.processors(session, None)
        if not processors_resp:
            continue
        for processor in processors_resp.processors:
            processor_map[processor.name] = processor
            processor_agents_map[processor.name].append(agent)
    return processor_map, processor_agents_map


async def process_cmd(session, args):
    """Process command implementation"""
    # retrieve processors and agents supporting these processors
    processor_map, processor_agents_map = await _build_mappings(session, args)
    # attempt to retrieve processor
    processor = processor_map.get(args.processor)
    if not processor:
        LOGGER.error(
            "cannot find an agent providing processor: %s", args.processor
        )
        return
    # attempt to set processor arguments
    for name, value in args.arguments:
        proc_arg = processor.get_arg(name)
        if not proc_arg:
            LOGGER.error(
                "processor %s does not support argument: %s",
                processor.name,
                name,
            )
            return
        proc_arg.set_value(value)
    # validate processor arguments
    if not processor.validate_arguments():
        cprint(processor.get_docstring())
        return
    # arguments are valid, now we need to find an agent supporting this
    # processor and send a processing request to it
    agent = choice(processor_agents_map[processor.name])
    agent.display_banner()
    processing_resp = await agent.process(session, processor)
    if not processing_resp:
        return
    processing_resp.result.display()


def _processor_argument(value):
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

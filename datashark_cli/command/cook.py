"""Recipe command
"""
from typing import Dict, Iterator
from pathlib import Path
from asyncio import create_task, gather
from argparse import Namespace
from itertools import cycle
from aiohttp import ClientSession
from datashark_core.model.api import Processor
from .. import LOGGER
from ..agent_api import AgentAPI
from ..recipe_api import RecipeAPI
from .process import (
    InitiateProcessingError,
    build_processors_mappings,
    initiate_processing,
)


async def worker(
    name: str,
    session: ClientSession,
    recipe_api: RecipeAPI,
    proc_map: Dict[str, Processor],
    proc_agents_map: Dict[str, Iterator[AgentAPI]],
):
    """Worker initiates processing"""
    while True:
        # get a task from the recipe api
        LOGGER.info("%s waiting a new task.", name)
        task = await recipe_api.get_task()
        LOGGER.warning("%s got task %s", name, task)
        if not task:
            # no more task in recipe, terminate worker
            LOGGER.info("%s stopping now.", name)
            return
        success = False
        try:
            success = await initiate_processing(
                session,
                task.processor,
                list(task.arguments.items()),
                proc_map,
                proc_agents_map,
            )
        except InitiateProcessingError as exc:
            LOGGER.error("%s: process_task failed: %s", name, exc)
        except:
            LOGGER.exception(
                "%s: process_task raised an unexpected exception!", name
            )
        finally:
            # notify recipe api that retrieved task is done
            recipe_api.task_done(task, success)


async def cook_cmd(session: ClientSession, args: Namespace):
    """Cook command implementation"""
    # load and prepare recipe
    recipe_api = RecipeAPI(args.recipe)
    try:
        recipe_api.prepare(args.variables_file)
    except ValueError as exc:
        LOGGER.error("cannot cook recipe: %s", exc)
        return
    # retrieve processors and agents supporting these processors
    processor_map, processor_agents_map = await build_processors_mappings(
        session, args.agents
    )
    # check if all required processors are available
    missing_processors = recipe_api.required_processors.difference(
        set(processor_map.keys())
    )
    if missing_processors:
        LOGGER.error(
            "cannot cook recipe: missing processors %s", missing_processors
        )
        return
    # turn agents lists into cycles for load balancing
    processor_agents_map = {
        name: cycle(agents) for name, agents in processor_agents_map.items()
    }
    # create workers to process recipe instructions
    tasks = []
    for k in range(args.worker_count):
        task = create_task(
            worker(
                f'worker-{k}',
                session,
                recipe_api,
                processor_map,
                processor_agents_map,
            )
        )
        tasks.append(task)
    # no need to join queue, gathering workers should be enough according to
    # RecipeAPI internal processing which ensures that workers are terminated
    # when queue is empty by sending them None instead of a Task instance
    await gather(*tasks, return_exceptions=True)


def setup(subparsers):
    """Setup cook argument parser"""
    parser = subparsers.add_parser(
        'cook', help="Follow the instructions given in the recipe"
    )
    parser.add_argument(
        '--worker-count',
        '-w',
        type=int,
        default=2,
        help="Number of workers to spawn to process recipe instructions. "
        "Worst case scenario only one agent can process tasks from recipe, "
        "this agent will have to be able to process 'worker_count' requests "
        "in parallel.",
    )
    parser.add_argument('--variables-file', '-v', type=Path, help="Variables file to apply for recipe")
    parser.add_argument('recipe', type=Path, help="Path to recipe to cook")
    parser.set_defaults(async_func=cook_cmd)

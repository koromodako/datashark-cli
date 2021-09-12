"""Recipe API
"""
from typing import Set, Dict, Optional
from pathlib import Path
from asyncio import Queue
from dataclasses import dataclass
from ruamel.yaml import safe_load
from . import LOGGER

@dataclass
class Task:
    name: str
    requires: Set[str]
    processor: str
    arguments: Dict[str, str]

    @classmethod
    def build(cls, dct):
        """Build object from dict"""
        return cls(
            name=dct['name'],
            requires=set(dct.get('requires', [])),
            processor=dct['processor'],
            arguments=dct['arguments'],
        )

    def set_variables(self, variables: Dict[str, str]):
        """Format arguments using variables"""
        try:
            self.arguments = {
                name: value.format(**variables)
                for name, value in self.arguments.items()
            }
        except KeyError as exc:
            raise ValueError(f"variable not provided: {exc}") from exc


class RecipeAPI:
    """Recipe API"""

    def __init__(self, filepath: Path):
        self._filepath = filepath
        self._task_map = {}
        self._processing_queue = Queue()

    @property
    def required_processors(self) -> Set[str]:
        """Name of all processors required to process recipe"""
        return {task.processor for task in self._task_map.values()}

    def _check_inexistant_requires(self):
        """Determine if references to inexistant tasks"""
        all_task_requires = set()
        for task in self._task_map.values():
            all_task_requires.update(task.requires)
        inexistant = all_task_requires.difference(set(self._task_map.keys()))
        if inexistant:
            raise ValueError(f"references to inexistant tasks: {inexistant}")

    def _check_acyclic_requires_graph(self):
        """Determine if dependency graph is acyclic"""
        task_requires_map = {
            name: set(task.requires) for name, task in self._task_map.items()
        }
        while task_requires_map:
            # list tasks without dependencies
            removable = {
                task
                for task, requires in task_requires_map.items()
                if not requires
            }
            # if no task without dependency and we're still in the loop
            # the graph contains a cycle... raise to prevent infinite loop.
            if not removable:
                remaining = list(task_requires_map.keys())
                raise ValueError(f"dependency cycle detected: {remaining}")
            # remove removable tasks from graph
            for removed in removable:
                del task_requires_map[removed]
            # remove removable tasks from other tasks' dependencies
            for requires in task_requires_map.values():
                for removed in removable:
                    requires.discard(removed)

    def _update_waiting_tasks(self, task: Task, success: bool):
        """Update tasks from waiting map to processing queue"""
        # remove task from waiting tasks requires list
        if success:
            for waiting_task in self._task_map.values():
                waiting_task.requires.discard(task.name)
            return
        # remove failed tasks recursively
        failed_tasks = [task]
        while failed_tasks:
            new_failed_tasks = []
            for failed_task in failed_tasks:
                for waiting_task in self._task_map.values():
                    if failed_task.name not in waiting_task.requires:
                        continue
                    # if task failed we need to cancel tasks depending on failed one
                    new_failed_tasks.append(waiting_task)
            # removed cancel tasks if any
            for new_failed_task in new_failed_tasks:
                del self._task_map[new_failed_task.name]
            # remove tasks depending on new failed tasks
            failed_tasks = new_failed_tasks

    def _update_processing_queue(self):
        """Move tasks from waiting map to processing queue"""
        # retrieve tasks with empty requires
        # if no more waiting tasks
        LOGGER.warning(self._task_map)
        if not self._task_map:
            # put None in processing queue
            LOGGER.warning("injecting None")
            self._processing_queue.put_nowait(None)
            # do nothing else
            return
        # enumerate ready tasks
        ready_tasks = [
            task for task in self._task_map.values() if not task.requires
        ]
        # remove from task map
        for ready_task in ready_tasks:
            del self._task_map[ready_task.name]
        # put ready tasks in processing queue
        for ready_task in ready_tasks:
            self._processing_queue.put_nowait(ready_task)

    def prepare(self, variables_file: Path = None):
        """Prepare recipe API internal structures"""
        variables = {}
        if variables_file:
            data = safe_load(variables_file.read_text())
            variables.update(data['recipe_vars'])
        data = safe_load(self._filepath.read_text())
        # build internal task map
        for task_dct in data['recipe']:
            task = Task.build(task_dct)
            task.set_variables(variables)
            if task.name in self._task_map:
                raise ValueError(f"task name duplicated: {task.name}")
            self._task_map[task.name] = task
        # perform checks
        self._check_inexistant_requires()
        self._check_acyclic_requires_graph()
        self._update_processing_queue()

    async def get_task(self) -> Optional[Task]:
        """Get next task or None if no task remaining"""
        return await self._processing_queue.get()

    def task_done(self, task: Task, success: bool):
        """Mark a task as done"""
        # notify queue that the job is done
        self._processing_queue.task_done()
        # look for tasks to update or cancel depending on success
        self._update_waiting_tasks(task, success)
        # update processing queue
        self._update_processing_queue()

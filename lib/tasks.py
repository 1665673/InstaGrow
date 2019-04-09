import time
import importlib
import queue
import copy
from . import actions as handlers

"""
term definitions

terms                           examples

tasks:                          [ follow.py, like-asia.py, ...]
    task                        follow.py, may or may not loop
        sub_tasks:               [ follow-user [list], unfollow-user [list], ...]
            sub_task             follow-user [list], sleep sometime upon completion
                actions:        follow-user [list], sleep sometime between each action
                    action:     (follow-user, justinbiever)
                    
[tasks]     = a set of [task]
[task]      = a set of [sub_task] + some configuration
[sub_task]   = [actions] + some configuration
[actions]   = a set of [action]
[action]    = a specific operation unit, e.g. follower one single user

"""

TASKS_DIR = "tasks"

"""
class Task
class Action

A Task object represents the logic of a task. 
A task could be a mix of sub_tasks, an example of an actions is a follow-by-list.

An Action object is an iterator to traverse all actions defined in a task,
this iterator will likely to go across different sub_tasks in the same Task object,
while preserving it's relative ordering.
"""


class Action:
    def __init__(self, task, index_sub_task=0, index_action=0, ready=time.time()):
        self.task = task
        self.index_sub_task = index_sub_task
        self.index_action = index_action
        self.ready = ready

    def __lt__(self, other):
        return self.ready < other.ready

    def _task(self):
        return self.task

    def _actions(self):
        return self.task.sub_tasks[self.index_sub_task]

    def next(self):
        if self.is_end():
            return
        try:
            count_action = len(self._actions()["list"])
            self.index_action += 1
            # when calculating next performing time,
            # make sure current self.ready is at least @ current time time.time()
            #   so a branch of actions won't be far behind
            #
            if self.ready < time.time():
                self.ready = time.time()
            if self.index_action < count_action:
                self.ready += self._actions()["cool-down"]
            else:  # self.index_action == count_action:
                self.ready += self._actions()["delay-upon-completion"]
                if not self.is_end():
                    self.index_action = 0
                    self.index_sub_task += 1
                else:
                    if self._task().loop:
                        self.index_action = 0
                        self.index_sub_task = 0
                    # this iterator reaches the end
                    else:
                        pass


        except Exception as e:
            pass

    def get_next(self):
        _next = copy.copy(self)
        _next.next()
        return _next

    def is_end(self):
        end = self.task.end()
        if not end:
            return True
        return self.index_sub_task == end.index_sub_task and self.index_action == end.index_action

    def execute(self):
        if self.is_end():
            return None
        try:
            actions = self._actions()
            action_type = actions["type"]
            target = actions["list"][self.index_action]

            self.task.executing(action_type, target)
            result = handlers.execute(action_type, target, self.ready)
            return result
        except Exception as e:
            return None


class Task:
    def __init__(self, id, title="no title", loop=True, sub_tasks=[],
                 on_finished=None, on_executing=None, on_queued=None):
        self.id = id
        self.title = title
        self.loop = loop
        self.sub_tasks = sub_tasks
        self.on_finished = on_finished
        self.on_executing = on_executing
        self.on_queued = on_queued

    # get first-action iterator
    def begin(self, begin_time=time.time()):
        return Action(self, ready=begin_time)

    # get end-action iterator
    def end(self):
        try:
            return Action(self, len(self.sub_tasks) - 1, len(self.sub_tasks[-1]["list"]))
        except Exception as e:
            return self.begin()

    # this function will be called upon queued
    def queued(self):
        if self.on_queued:
            self.on_queued(self)

    # this function will be called upon being executed
    def executing(self, action, target):
        if self.on_executing:
            self.on_executing(self, action, target)

    # this function will be called upon finish
    def finished(self):
        if self.on_finished:
            self.on_finished(self)


"""
function load()
returns a dict with all tasks loaded in
tasks_dict = {
    "task_name" : object-Task{
        "name" : task_name,
        "title": defined_in_module,
        "loop": defined_in_module
        "sub_tasks": defined_in_module
    },
    ...
}
"""


def load_task_from_file(task_path, on_queued=None, on_executing=None, on_finished=None):
    try:
        module = importlib.import_module(task_path)
    except Exception as e:
        return {}
    task = Task(id=module.name + "-" + str(int(time.time())),
                title=module.title,
                loop=module.loop,
                sub_tasks=module.sub_tasks,
                on_queued=on_queued,
                on_executing=on_executing,
                on_finished=on_finished
                )
    if task.sub_tasks and len(task.sub_tasks) > 0:
        return task
    else:
        return None


def load_task_by_definition(task_definition, on_queued=None, on_executing=None, on_finished=None):
    task_id = task_definition["id"] if "id" in task_definition else \
        task_definition["name"] + "-" + str(int(time.time()))
    task = Task(id=task_id,
                title=task_definition["title"],
                loop=task_definition["loop"],
                sub_tasks=task_definition["sub_tasks"],
                on_queued=on_queued,
                on_executing=on_executing,
                on_finished=on_finished
                )
    if task.sub_tasks and len(task.sub_tasks) > 0:
        return task
    else:
        return None


def load(task_file_names, on_queued=None, on_executing=None, on_finished=None):
    if not task_file_names:
        return {}
    tasks = {}
    for task_file_name in task_file_names:
        try:
            task_path = TASKS_DIR + "." + task_file_name
            task = load_task_from_file(task_path, on_queued, on_executing, on_finished)
            tasks[task.id] = task
        except Exception as e:
            return []
    return tasks


"""
class actionQueue:

It's a priority queue for pending actions,
it contains exactly one action from each task.
this class is based on queue.PriorityQueue.


set_tasks():
init the queue by passing the tasks dict,
it reads the first action from each task

add_task():
add another task. it's first action will be pushed into queue

get():
it overrides the default get() method in original queue.PriorityQueue,
the new method pops the next action [in-queue], and, at the same time,
automatically loads the next action [from-the-same-task-module]
"""


class ActionQueue(queue.PriorityQueue):
    def add_from_task_dict(self, tasks):
        for id in tasks:
            self.add_from_task(tasks[id])

    def add_from_task(self, task):
        try:
            if task:
                begin = task.begin()
                self.add_action(begin)
                #
                #   added a task!
                #
                task.queued()
        except Exception as e:
            raise

    def add_action(self, action):
        self.put(action)

    def get(self, block=False, timeout=None):
        action = None
        try:
            action = super(ActionQueue, self).get(block, timeout)
            #
            #   load the next action
            #
            if not action.is_end():
                _next = action.get_next()
                self.add_action(_next)
            else:
                #
                #   finished a task!
                #
                action.task.finished()

        except Exception as e:
            return None

        # wait until this action is ready
        #   this logic has moved 
        #
        #
        # ready = action.ready
        # current = time.time()
        # if current < ready:
        #     time.sleep(ready - current)

        return action
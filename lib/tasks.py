import time
import importlib
import queue
import copy
from . import maneuver as libManeuver

"""
tasks term definition

terms                       examples

tasks:                      [ follow.py, like-asia.py, ...]
    task                    follow.py
        actions:            [ follow-by-list, un-follow-by-list, ...]
            action:         follow-by-list
                maneuver    [ justinbieber, taylorswift, selenagomez, ...]

"""

"""
load_tasks()
returns a dict with all tasks loaded in
tasks_dict = {
    "task_name" : object-Task{
        "name" : task_name,
        "title": defined_in_module,
        "loop": defined_in_module
        "actions": defined_in_module
    },
    ...
}
"""
TASKS_DIR = "tasks"


class Maneuver:
    def __init__(self, task, index_action=0, index_maneuver=0, ready=time.time()):
        self.task = task
        self.index_action = index_action
        self.index_maneuver = index_maneuver
        self.ready = ready

    def __lt__(self, other):
        return self.ready < other.ready

    def _task(self):
        return self.task

    def _action(self):
        return self.task.actions[self.index_action]

    def next(self):
        if self.is_end():
            return
        try:
            count_maneuver = len(self._action()["list"])
            self.index_maneuver += 1
            if self.index_maneuver < count_maneuver:
                self.ready += self._action()["cool-down"]
            else:  # self.index_maneuver == count_maneuver:
                self.ready += self._action()["delay-upon-completion"]
                if not self.is_end():
                    self.index_maneuver = 0
                    self.index_action += 1
                else:
                    if self._task().loop:
                        self.index_maneuver = 0
                        self.index_action = 0
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
        return self.index_action == end.index_action and self.index_maneuver == end.index_maneuver

    def execute(self):
        if self.is_end():
            return None
        try:
            action = self._action()
            action_type = action["type"]
            target = action["list"][self.index_maneuver]

            result = libManeuver.execute(action_type, target, self.ready)
            return result
        except Exception as e:
            return None


class Task:
    def __init__(self, name, title="no title", loop=True, actions=[]):
        self.name = name
        self.title = title
        self.loop = loop
        self.actions = actions

    # get first-maneuver iterator
    def begin(self, begin_time=time.time()):
        return Maneuver(self, ready=begin_time)

    # get end-maneuver iterator
    def end(self):
        try:
            return Maneuver(self, len(self.actions) - 1, len(self.actions[-1]["list"]))
        except Exception as e:
            return self.begin()


def read_task_from_module(task_name):
    task_path = TASKS_DIR + "." + task_name
    try:
        module = importlib.import_module(task_path)
    except Exception as e:
        return {}
    task = Task(name=task_name,
                title=module.title,
                loop=module.loop,
                actions=module.actions)
    if task.actions and len(task.actions) > 0:
        return task
    else:
        return None


def load(task_names):
    tasks = {}
    for task_name in task_names:
        try:
            task_path = TASKS_DIR + "." + task_name
            task = read_task_from_module(task_name)
            tasks[task_name] = task
        except Exception as e:
            return []
    return tasks


"""
class ManeuverQueue:

return a priority queue of pending manervers,
it contains exactly one maneuver from each task


set_tasks():
init the queue by passing the tasks dict,
it reads the first maneuver from each task

add_task():
add another task. it's first manerver will be pushed into queue

get():
it overrides the default get() method in original queue.PriorityQueue,
the new method pops the next maneuver [in-queue], and, at the same time,
automatically loads the next maneuver [from-the-same-task-module]
"""


class ManeuverQueue(queue.PriorityQueue):
    def add_from_tasks(self, tasks):
        for name in tasks:
            self.add_from_task(tasks[name])

    def add_from_task(self, task):
        if task:
            begin = task.begin()
            self.add_maneuver(begin)

    def add_maneuver(self, maneuver):
        self.put(maneuver)

    def get(self, block=False, timeout=None):
        maneuver = None
        try:
            maneuver = super(ManeuverQueue, self).get(block, timeout)
            #
            #   load the next maneuver
            #
            if not maneuver.is_end():
                _next = maneuver.get_next()
                self.add_maneuver(_next)

        except Exception as e:
            return None

        # wait until this maneuver is ready
        #   this logic has moved 
        #
        #
        # ready = maneuver.ready
        # current = time.time()
        # if current < ready:
        #     time.sleep(ready - current)

        return maneuver

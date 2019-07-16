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
        sub_tasks:              [ follow-user [list], unfollow-user [list], ...]
            sub_task            follow-user [list], sleep sometime upon completion
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
    def __init__(self, task, index_subtask=0, index_action=0, ready=time.time()):
        self.task = task
        self.index_subtask = index_subtask
        self.index_action = index_action
        self.ready = ready

    def __lt__(self, other):
        return self.ready < other.ready

    def _task(self):
        return self.task

    def _subtask(self):
        return self.task.sub_tasks[self.index_subtask]

    def next(self):
        if self.is_end():
            return
        try:
            count_subtasks = len(self._task().sub_tasks)
            count_action = len(self._subtask()["targets"])
            self.index_action += 1
            # when calculating next performing time,
            # make sure current self.ready is at least @ current time time.time()
            #   so a branch of actions won't be far behind
            #
            if self.ready < time.time():
                self.ready = time.time()
            #
            # a regular move to next action in the same sub_task
            if self.index_action < count_action:
                self.ready += self._subtask()["cool-down"]
            #
            # need to move to next sub_task
            else:  # self.index_action == count_action:
                #
                #   not yet the task end,
                if not self.is_end():
                    self.ready += self._subtask()["delay-upon-completion"]
                    self.index_action = 0
                    self.index_subtask += 1
                    self.ready += self._subtask()["delay-before-start"]
                #
                #   reached the task end, see if this task loops
                else:
                    #
                    #   yes, loop. go ahead
                    if self._task().loop:
                        #
                        # task has more than 1 sub_tasks, start over from the very first one
                        if count_subtasks > 1:
                            self.ready += self._subtask()["delay-upon-completion"]
                            self.index_action = 0
                            self.index_subtask = 0
                            self.ready += self._subtask()["delay-before-start"]
                        # have only 1 sub_tasks, so only have to reset index_action
                        # and need to compare if we take the cooldown or double-end delays
                        # take the logger one
                        else:
                            self.index_action = 0
                            delay1 = self._subtask()["delay-before-start"] + self._subtask()["delay-upon-completion"]
                            cooldown = self._subtask()["cool-down"]
                            self.ready += delay1 if delay1 > cooldown else cooldown
                    #
                    # this task do not loop
                    # so this iterator reaches the end
                    else:
                        pass

            # adjust self.ready in warm-up mode
            if self._task().warm_up:
                begin = self._task().warm_up["begin"]
                end = self._task().warm_up["end"]
                rate = self._task().warm_up["rate"]
                if time.time() < end and begin < end:
                    # recalculate ready time
                    ready = self.ready - time.time()
                    rate = 1.0 + (end - time.time()) / (end - begin) * (rate - 1.0)
                    ready *= rate
                    self.ready = time.time() + ready
                    self.rate = rate
                else:
                    self.rate = 1.0


        except Exception as e:
            pass

    def get_next(self):
        _next = copy.copy(self)
        _next.next()
        return _next

    def is_begin(self):
        return self.index_subtask == 0 and self.index_action == 0

    def is_end(self):
        end = self.task.end()
        if not end:
            return True
        return self.index_subtask == end.index_subtask and self.index_action == end.index_action

    def execute(self):
        if self.is_end():
            return None
        try:
            actions = self._subtask()
            action_init = actions["init"]
            action_type = actions["action"]
            target = actions["targets"][self.index_action]

            # if it's the first action in sub_task
            if self.is_begin():
                handlers.init_subtask(action_init)

            # execute it
            self.task.executing(action_type, target)
            result = handlers.execute(action_type, target, self.ready, self)

            return result
        except Exception as e:
            print(str(e))
            return None


class Task:
    def __init__(self, id, title="no title", loop=True, sub_tasks=[],
                 on_finished=None, on_executing=None, on_queued=None, warm_up=None):
        self.id = id
        self.title = title
        self.loop = loop
        self.sub_tasks = sub_tasks
        self.on_finished = on_finished
        self.on_executing = on_executing
        self.on_queued = on_queued
        self.warm_up = warm_up

        if not self.id:
            raise Exception("invalid task: invalid task-id")
        if not self.sub_tasks:
            raise Exception("invalid task: missing sub-task list or empty list")

        # tidy up sub_tasks definition
        for sub_task in sub_tasks:
            if "action" not in sub_task:
                raise Exception("invalid task: missing sub-task type")
            if "targets" not in sub_task or len(sub_task["targets"]) == 0:
                raise Exception("invalid task: missing action targets or empty target list")
            if "init" not in sub_task:
                sub_task["init"] = None
            if "cool-down" not in sub_task:
                sub_task["cool-down"] = 0
            if "delay-before-start" not in sub_task:
                sub_task["delay-before-start"] = 0
            if "delay-upon-completion" not in sub_task:
                sub_task["delay-upon-completion"] = 0

    # get first-action iterator
    def begin(self, begin_time=time.time()):
        begin_time += self.sub_tasks[0]["delay-before-start"]
        return Action(self, ready=begin_time)

    # get end-action iterator
    def end(self):
        try:
            return Action(self, len(self.sub_tasks) - 1, len(self.sub_tasks[-1]["targets"]))
        except Exception:
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


def load_task_from_file(task_path, on_queued=None, on_executing=None, on_finished=None, warm_up=None):
    try:
        module = importlib.import_module(task_path)
    except Exception as e:
        raise e
    try:
        task = Task(id=module.name + "-" + str(int(time.time())),
                    title=module.title,
                    loop=module.loop,
                    sub_tasks=module.sub_tasks,
                    on_queued=on_queued,
                    on_executing=on_executing,
                    on_finished=on_finished,
                    warm_up=warm_up
                    )
        return task
    except Exception as e:
        raise e


def load_task_by_definition(task_definition, on_queued=None, on_executing=None, on_finished=None, warm_up=None):
    task_id = task_definition["id"] if "id" in task_definition else \
        task_definition["name"] + "-" + str(int(time.time()))
    try:
        task = Task(id=task_id,
                    title=task_definition["title"],
                    loop=task_definition["loop"],
                    sub_tasks=task_definition["sub_tasks"],
                    on_queued=on_queued,
                    on_executing=on_executing,
                    on_finished=on_finished,
                    warm_up=warm_up
                    )
        return task
    except Exception as e:
        raise e


def load_all_task_by_names(task_file_names, on_queued=None, on_executing=None, on_finished=None, warm_up=None):
    if not task_file_names:
        return {}
    tasks = {}
    for task_file_name in task_file_names:
        try:
            task_path = TASKS_DIR + "." + task_file_name
            task = load_task_from_file(task_path, on_queued, on_executing, on_finished, warm_up)
            tasks[task.id] = task
        except Exception as e:
            raise e
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
            raise e

    def add_action(self, action):
        self.put(action)

    def get(self, block=False, timeout=None):
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

            return action

        except Exception as e:
            raise e

        # wait until this action is ready
        #   this logic has moved 
        #
        #
        # ready = action.ready
        # current = time.time()
        # if current < ready:
        #     time.sleep(ready - current)
        #
        # return action

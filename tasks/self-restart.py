name = "self-restart"
title = "restart script"
loop = 1
sub_tasks = [
    {
        "action": "self-restart",
        # target is for arguments, e.g. ["run.py", "minhaodeng", "-p", "-t", "follow", "like"]
        # please wrap argument list inside the outer list, i.e.  "targets": [[argument-list]]
        # set it to None to restart with original arguments
        "targets": [None],
        "delay-before-start": -9999  # make it of extra high priority over current tasks
    }
]

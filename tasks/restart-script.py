name = "restart-script"
title = "restart script"
loop = False
sub_tasks = [
    {
        "action": "restart-script",
        # target is for arguments, e.g. ["run.py", "minhaodeng", "-p", "-t", "follow", "like"]
        # please wrap argument list inside the outer list, i.e.  "targets": [[argument-list]]
        # set it to None to restart with original arguments
        "targets": [None],
        "delay-before-start": -9999  # make it of extra high priority over current tasks
    }
]

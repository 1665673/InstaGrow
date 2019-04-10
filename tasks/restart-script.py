name = "restart-script"
title = "restart script"
loop = False
sub_tasks = [
    {
        "action": "restart-script",
        "targets": ["explicitly restart this script"],
        "delay-before-start": -9999  # make it of extra high priority over current tasks
    }
]

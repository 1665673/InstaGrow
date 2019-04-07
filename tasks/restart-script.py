name = "restart-script"
title = "restart script"
loop = False
sub_tasks = [
    {
        "type": "restart-script",
        "list": ["explicitly restart this script"],
        "cool-down": 0,
        "delay-upon-completion": 0
    }
]

name = "restart-script"
title = "test restart script"
loop = False
sub_tasks = [
    {
        "type": "restart-script",
        "list": ["I want to test this feature"],
        "cool-down": 0,
        "delay-upon-completion": 0
    }
]

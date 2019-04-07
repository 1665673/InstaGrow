name = "follow"
title = "follow then un-follow"
loop = True
sub_tasks = [
    {
        "type": "follow-user",
        "list": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                 'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 50,
        "delay-upon-completion": 240
    },
    {
        "type": "unfollow-user",
        "list": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                 'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 40,
        "delay-upon-completion": 0
    }
]

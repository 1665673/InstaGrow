name = "follow"
title = "follow then un-follow"
loop = -1
sub_tasks = [
    {
        "action": "follow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 100,  # 400-follows = 24-hours
        "delay-upon-completion": 240
    },
    {
        "action": "unfollow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 90  # 400-follows = 24-hours
    }
]

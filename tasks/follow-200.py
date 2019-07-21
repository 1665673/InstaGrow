name = "follow"
title = "follow then un-follow"
loop = -1
sub_tasks = [
    {
        "action": "follow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 208,  # 200-follows = 24-hours
        "delay-upon-completion": 240
    },
    {
        "action": "unfollow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 200  # 200-follows = 24-hours
    }
]

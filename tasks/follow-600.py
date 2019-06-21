name = "follow"
title = "follow then un-follow"
loop = True
sub_tasks = [
    {
        "action": "follow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 65,  # 600-follows = 24-hours
        "delay-upon-completion": 240
    },
    {
        "action": "unfollow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 55  # 600-follows = 24-hours
    }
]

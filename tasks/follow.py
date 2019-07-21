name = "follow"
title = "follow then un-follow"
loop = -1
sub_tasks = [
    {
        "action": "follow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 45,  # 800-follows = 24-hours
        "delay-upon-completion": 240
    },
    {
        "action": "unfollow-user",
        "targets": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                    'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 39  # 800-unfollows = 24-hours
    }
]

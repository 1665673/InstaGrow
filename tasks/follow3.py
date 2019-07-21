name = "follow"
title = "follow then un-follow"
loop = -1
sub_tasks = [
    {
        "action": "follow-user",
        "targets": ['kendalljenner', 'natgeo', 'nickiminaj', 'khloekardashian', 'jlo', 'mileycyrus', 'katyperry',
                    'instagram', 'arianagrande', 'selenagomez', 'kimkardashian', 'therock'],
        "cool-down": 46,  # 800-follows = 24-hours
        "delay-upon-completion": 240
    },
    {
        "action": "unfollow-user",
        "targets": ['kendalljenner', 'natgeo', 'nickiminaj', 'khloekardashian', 'jlo', 'mileycyrus', 'katyperry',
                    'instagram', 'arianagrande', 'selenagomez', 'kimkardashian', 'therock'],
        "cool-down": 42  # 800-unfollows = 24-hours
    }
]

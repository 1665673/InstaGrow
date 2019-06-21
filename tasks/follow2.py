name = "follow"
title = "follow then un-follow"
loop = True
sub_tasks = [
    {
        "action": "follow-user",
        "targets": ['kendalljenner', 'natgeo', 'nickiminaj', 'khloekardashian', 'jlo', 'mileycyrus',
                    'nike', 'katyperry', 'kourtneykardash', 'kevinhart4real', 'ddlovato'],
        "cool-down": 46,  # 800-follows = 24-hours
        "delay-upon-completion": 240
    },
    {
        "action": "unfollow-user",
        "targets": ['kendalljenner', 'natgeo', 'nickiminaj', 'khloekardashian', 'jlo', 'mileycyrus',
                    'nike', 'katyperry', 'kourtneykardash', 'kevinhart4real', 'ddlovato'],
        "cool-down": 40  # 800-unfollows = 24-hours
    }
]

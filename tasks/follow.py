title = "follow then un-follow"
loop = True
actions = [
    {
        "type": "follow-by-list",
        "list": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                 'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 50,
        "delay-upon-completion": 240
    },
    {
        "type": "unfollow-by-list",
        "list": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                 'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "cool-down": 40,
        "delay-upon-completion": 0
    }
]

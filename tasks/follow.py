title = "follow then unfollow"
loop = True
actions = [
    {
        "type": "follow-by-list",
        "list": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                 'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "delay-in-between": 25,
        "delay-upon-completion": 240
    },
    {
        "type": "unfollow-by-list",
        "list": ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                 'beyonce', 'kyliejennr', 'katyperry', 'therock'],
        "delay-in-between": 20,
        "delay-upon-completion": 0
    }
]

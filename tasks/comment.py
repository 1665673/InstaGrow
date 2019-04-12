name = "comment"
title = "comment by locations"
loop = True
sub_tasks = [
    {
        "init": "init-comment-by-location",
        "action": "comment-by-location",
        "targets": ['6889842/paris-france/', '6889842/paris-france/', '20188833/manhattan-new-york/',
                    '17326249/moscow-russia/',
                    '213385402/london-united-kingdom/', '213163910/sao-paulo-brazil/',
                    '212999109/los-angeles-california/'],
        "cool-down": 260,
        "delay-upon-completion": 0
    }
]

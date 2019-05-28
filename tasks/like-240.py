name = "like"
title = "like by tags"
loop = True
sub_tasks = [
    {
        "action": "like-by-tag",
        "targets": ['love', 'instagood', 'photooftheday', 'fashion'],
        "cool-down": 240  # 240-likes = 16-hours
    }
]

name = "like"
title = "like by tags"
loop = True
sub_tasks = [
    {
        "action": "like-by-tag",
        "targets": ['love', 'instagood', 'photooftheday', 'fashion'],
        "cool-down": 144  # 450-actions = 900-likes = 18-hours
    }
]

name = "like"
title = "like by tags"
loop = True
sub_tasks = [
    {
        "action": "like-by-tag",
        "targets": ['love', 'instagood', 'photooftheday', 'fashion'],
        "cool-down": 80  # 720-likes = 16-hours
    }
]
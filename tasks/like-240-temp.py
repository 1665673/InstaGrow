name = "like"
title = "like by tags"
loop = True
sub_tasks = [
    {
        "action": "like-by-tag",
        "targets": ["jazz", "newyork", "love", "instagood", "followme", "tagforlikes", "me", "thejefferymiller"],
        "cool-down": 240  # 240-likes = 16-hours
    }
]

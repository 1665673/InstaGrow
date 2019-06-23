name = "like-usa"
title = "like by usa locations"
loop = True
sub_tasks = [
    {
        "action": "like-by-location",
        "targets": ['212988663/new-york-new-york/', '212941492/miami-florida/', '204517928/chicago-illinois/',
                    '212999109/los-angeles-california/', '213480180/washington-district-of-columbia/',
                    '44961364/san-francisco-california/', '213941548/seattle-washington/'],
        "cool-down": 120  # 480-likes = 16-hours
    }
]

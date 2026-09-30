"""Page 2: show places for the activity selected on Page 1."""

import storage
from models import Activity


TITLE = "สถานที่นัดพบ · FIND MEETING PLACES"


def build(query):
    """Filter activity groups and summarize them by meeting place."""
    selected_activity = query.get("activity", "").strip()

    if not selected_activity:
        return {
            "selected_activity": "",
            "places": [],
            "page_state": "missing_activity",
        }

    rows = storage.load()
    places_by_name = {}
    activity_found = False

    for row in rows:
        if row.get("activity", "") != selected_activity:
            continue

        activity_found = True
        place_name = str(row.get("place", "")).strip()
        if not place_name:
            continue

        activity_group = Activity.from_dict(row)

        if place_name not in places_by_name:
            places_by_name[place_name] = {
                "name": place_name,
                "group_count": 0,
                "total_members": 0,
                "total_capacity": 0,
                "remaining_spaces": 0,
                "open_groups": 0,
                "full_groups": 0,
                "group_names": [],
                "dates": [],
                "any_open": False,
            }

        place = places_by_name[place_name]
        place["group_count"] += 1
        place["total_members"] += activity_group.members
        place["total_capacity"] += activity_group.max_members
        place["remaining_spaces"] += activity_group.remaining_spaces()

        is_open = (
            activity_group.status == "เปิดรับ"
            and activity_group.has_available_space()
        )
        if is_open:
            place["open_groups"] += 1
            place["any_open"] = True
        elif activity_group.status == "เต็ม" or activity_group.is_full():
            place["full_groups"] += 1

        if activity_group.group_name not in place["group_names"]:
            place["group_names"].append(activity_group.group_name)
        if activity_group.date not in place["dates"]:
            place["dates"].append(activity_group.date)

    places = list(places_by_name.values())

    if places:
        page_state = "ready"
    elif activity_found:
        page_state = "no_places"
    else:
        page_state = "unknown_activity"

    return {
        "selected_activity": selected_activity,
        "places": places,
        "page_state": page_state,
    }

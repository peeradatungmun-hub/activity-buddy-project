"""Page 3: activity groups using the project's existing Activity data."""
import storage
from models import Activity


TITLE = "Activity Groups"
OPEN_STATUS = "\u0e40\u0e1b\u0e34\u0e14\u0e23\u0e31\u0e1a"
FULL_STATUS = "\u0e40\u0e15\u0e47\u0e21"

ICON_MAP = {
    "\u0e27\u0e34\u0e48\u0e07": "\U0001f3c3",
    "\u0e41\u0e1a\u0e14\u0e21\u0e34\u0e19\u0e15\u0e31\u0e19": "\U0001f3f8",
    "\u0e1f\u0e38\u0e15\u0e1a\u0e2d\u0e25": "\u26bd",
    "\u0e1a\u0e32\u0e2a\u0e40\u0e01\u0e15\u0e1a\u0e2d\u0e25": "\U0001f3c0",
    "\u0e1a\u0e2d\u0e23\u0e4c\u0e14\u0e40\u0e01\u0e21": "\U0001f3ae",
    "\u0e27\u0e48\u0e32\u0e22\u0e19\u0e49\u0e33": "\U0001f3ca",
    "\u0e40\u0e17\u0e40\u0e1a\u0e34\u0e25\u0e40\u0e17\u0e19\u0e19\u0e34\u0e2a": "\U0001f3d3",
    "\u0e0b\u0e49\u0e2d\u0e21\u0e14\u0e19\u0e15\u0e23\u0e35": "\U0001f3b5",
    "\u0e27\u0e2d\u0e25\u0e40\u0e25\u0e22\u0e4c\u0e1a\u0e2d\u0e25": "\U0001f3d0",
}


def _view_record(row, index):
    """Add display-only details to a stored Activity record."""
    activity = Activity.from_dict(row)
    is_full = activity.is_full()
    capacity = activity.max_members
    progress = 0 if capacity <= 0 else min(100, round(activity.members / capacity * 100))
    return {
        "id": index,
        "activity": activity.activity,
        "place": activity.place,
        "group_name": activity.group_name,
        "date": activity.date,
        "members": activity.members,
        "max_members": capacity,
        "remaining_spaces": activity.remaining_spaces(),
        "is_full": is_full,
        "progress": progress,
        "icon": ICON_MAP.get(activity.activity, "\U0001f465"),
    }


def build(query=None):
    """Build Page 3 from the project's persisted activity-group records."""
    query = query or {}
    rows = storage.load()
    all_groups = []
    for index, row in enumerate(rows):
        try:
            all_groups.append(_view_record(row, index))
        except (TypeError, ValueError):
            continue

    selected_activity = str(query.get("activity", query.get("category", ""))).strip()
    selected_place = str(query.get("place", "")).strip()
    group_id = str(query.get("group_id", "")).strip()

    categories = []
    category_counts = {}
    for group in all_groups:
        name = group["activity"]
        if name not in category_counts:
            category_counts[name] = 0
            categories.append({"name": name, "count": 0})
        category_counts[name] += 1
    for category in categories:
        category["count"] = category_counts[category["name"]]

    groups = [
        group for group in all_groups
        if (not selected_activity or group["activity"] == selected_activity)
        and (not selected_place or group["place"] == selected_place)
    ]
    selected_group = next((group for group in groups if str(group["id"]) == group_id), None)

    return {
        "activities": groups,
        "activity_categories": categories,
        "selected_activity": selected_activity,
        "selected_place": selected_place,
        "selected_group": selected_group,
        "show_create_form": query.get("action") == "create",
        "group_count": len(groups),
        "total_group_count": len(all_groups),
    }


def handle(form):
    """Create a group or add a participant using the existing JSON data store."""
    rows = storage.load()
    action = form.get("action", "")

    if action == "create":
        group_name = form.get("group_name", "").strip()
        activity_name = form.get("activity", "").strip()
        place = form.get("place", "").strip()
        date = form.get("date", "").strip()
        try:
            max_members = int(form.get("max_members", ""))
        except (TypeError, ValueError):
            return "Please enter a valid group capacity."

        known_activities = {str(row.get("activity", "")).strip() for row in rows}
        if not group_name or not activity_name or not place or not date:
            return "Please complete every activity group field."
        if activity_name not in known_activities:
            return "Choose an activity from the available categories."
        if not 2 <= max_members <= 50:
            return "Group capacity must be between 2 and 50."

        new_group = Activity(
            activity=activity_name,
            place=place,
            group_name=group_name,
            date=date,
            members=1,
            max_members=max_members,
            status=OPEN_STATUS,
        )
        rows.append(new_group.to_dict())
        storage.save(rows)
        return "Activity group created."

    if action == "join":
        try:
            group_index = int(form.get("group_index", ""))
        except (TypeError, ValueError):
            return "Select a valid activity group."
        if group_index < 0 or group_index >= len(rows):
            return "That activity group is no longer available."

        try:
            group = Activity.from_dict(rows[group_index])
        except (TypeError, ValueError):
            return "That activity group has invalid data."
        if group.is_full():
            return "This activity group is already full."

        group.members += 1
        group.status = FULL_STATUS if group.is_full() else OPEN_STATUS
        rows[group_index] = group.to_dict()
        storage.save(rows)
        return "You joined the activity group."

    return "Choose a valid activity group action."


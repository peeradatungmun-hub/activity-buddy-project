"""Page 3: activity groups using the project's existing Activity data."""
import json
from datetime import date as calendar_date
from uuid import uuid4

import storage
from models import Activity


TITLE = "กลุ่มกิจกรรม · Activity Groups"
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

THAI_MONTHS = [
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]


def _group_key(row):
    """Build a stable demo key from the group's identifying details."""
    saved_id = str(row.get("group_id", "")).strip()
    if saved_id:
        return saved_id
    fields = ["group_name", "activity", "place", "date", "start_time", "end_time"]
    parts = []
    for field in fields:
        parts.append(str(row.get(field, "")).strip())
    return "||".join(parts)


def _format_date(date_text):
    """Show an ISO date in a compact Thai format, with a legacy fallback."""
    if not date_text:
        return "ยังไม่ระบุวันที่"
    try:
        year_text, month_text, day_text = date_text.split("-")
        month_number = int(month_text)
        day_number = int(day_text)
        buddhist_year = int(year_text) + 543
        return f"{day_number} {THAI_MONTHS[month_number - 1]} {buddhist_year}"
    except (ValueError, IndexError):
        return date_text


def times_overlap(new_start, new_end, old_start, old_end):
    """Return True when two time ranges overlap."""
    return new_start < old_end and new_end > old_start


def is_expired(date_text, today=None):
    """Return True only when a valid group date is before today."""
    if not date_text:
        return False
    try:
        group_date = calendar_date.fromisoformat(str(date_text).strip())
    except (TypeError, ValueError):
        return False
    return group_date < (today or calendar_date.today())


def _owns_group(row, username):
    """Use creator_username for conservative ownership checks."""
    owner = str(row.get("creator_username", "")).strip().lower()
    return bool(owner) and owner == str(username).strip().lower()


def _joined_keys(form):
    """Read browser-side demo membership keys from a submitted form."""
    joined_group_keys = []
    try:
        saved_keys = json.loads(form.get("joined_group_keys", "[]"))
        if isinstance(saved_keys, list):
            for saved_key in saved_keys:
                joined_group_keys.append(str(saved_key))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return joined_group_keys


def _read_group_fields(form, rows, current_members=0):
    """Validate shared create/edit fields and return clean values."""
    values = {
        "group_name": form.get("group_name", "").strip(),
        "activity": form.get("activity", "").strip(),
        "place": form.get("place", "").strip(),
        "date": form.get("date", "").strip(),
        "start_time": form.get("start_time", "").strip(),
        "end_time": form.get("end_time", "").strip(),
    }
    if not values["group_name"]:
        return None, "✗ กรุณากรอกชื่อกลุ่ม"
    if not values["activity"]:
        return None, "✗ กรุณาเลือกกิจกรรม"
    if not values["place"]:
        return None, "✗ กรุณาเลือกสถานที่"
    if not values["date"]:
        return None, "✗ กรุณาระบุวันที่จัดกิจกรรม"
    if not values["start_time"] or not values["end_time"]:
        return None, "✗ กรุณาระบุเวลาเริ่มและเวลาสิ้นสุด"
    if values["end_time"] <= values["start_time"]:
        return None, "✗ เวลาสิ้นสุดต้องช้ากว่าเวลาเริ่ม"

    try:
        max_members = int(form.get("max_members", ""))
    except (TypeError, ValueError):
        return None, "✗ จำนวนสมาชิกต้องอยู่ระหว่าง 2–50 คน"

    known_activities = {str(row.get("activity", "")).strip() for row in rows}
    if values["activity"] not in known_activities:
        return None, "✗ กรุณาเลือกกิจกรรมที่มีอยู่ในระบบ"
    if not 2 <= max_members <= 50:
        return None, "✗ จำนวนสมาชิกต้องอยู่ระหว่าง 2–50 คน"
    if max_members < current_members:
        return None, "✗ จำนวนสมาชิกสูงสุดต้องไม่น้อยกว่าจำนวนสมาชิกปัจจุบัน"

    values["max_members"] = max_members
    return values, ""


def _view_record(row, index):
    """Add display-only details to a stored Activity record."""
    activity = Activity.from_dict(row)
    is_full = activity.is_full()
    capacity = activity.max_members
    remaining_spaces = activity.remaining_spaces()
    if is_full:
        status_text = "เต็มแล้ว"
        status_class = "full"
    elif remaining_spaces <= 2:
        status_text = "ใกล้เต็ม"
        status_class = "near-full"
    else:
        status_text = "เปิดรับ"
        status_class = "open"
    progress = 0 if capacity <= 0 else min(100, round(activity.members / capacity * 100))
    return {
        "id": index,
        "activity": activity.activity,
        "place": activity.place,
        "group_name": activity.group_name,
        "creator": str(row.get("creator", "")).strip(),
        "creator_username": str(row.get("creator_username", "")).strip(),
        "date": activity.date,
        "date_text": _format_date(activity.date),
        "start_time": str(row.get("start_time", "")).strip(),
        "end_time": str(row.get("end_time", "")).strip(),
        "members": activity.members,
        "max_members": capacity,
        "remaining_spaces": remaining_spaces,
        "is_full": is_full,
        "status_text": status_text,
        "status_class": status_class,
        "progress": progress,
        "icon": ICON_MAP.get(activity.activity, "\U0001f465"),
        "group_key": _group_key(row),
        "is_expired": is_expired(activity.date),
    }


def build(query=None):
    """Build Page 3 from the project's persisted activity-group records."""
    query = query or {}
    rows = storage.load()
    all_groups = []
    for index, row in enumerate(rows):
        try:
            group = _view_record(row, index)
            if not group["is_expired"]:
                all_groups.append(group)
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
        "all_activities": all_groups,
        "activity_categories": categories,
        "selected_activity": selected_activity,
        "selected_place": selected_place,
        "selected_group": selected_group,
        "show_create_form": query.get("action") == "create",
        "group_count": len(groups),
        "total_group_count": len(all_groups),
    }


def handle(form):
    """Create, join, edit, or delete an activity group."""
    rows = storage.load()
    action = form.get("action", "")

    if action == "create":
        creator = form.get("creator", "").strip()
        if not creator:
            return "✗ กรุณาระบุชื่อผู้สร้างกลุ่ม"

        values, error = _read_group_fields(form, rows)
        if error:
            return error

        new_group = Activity(
            activity=values["activity"],
            place=values["place"],
            group_name=values["group_name"],
            date=values["date"],
            members=1,
            max_members=values["max_members"],
            status=OPEN_STATUS,
        )
        new_record = new_group.to_dict()
        requested_id = form.get("group_id", "").strip()
        existing_ids = {str(row.get("group_id", "")).strip() for row in rows}
        if not requested_id or requested_id in existing_ids:
            requested_id = uuid4().hex
        new_record["group_id"] = requested_id
        new_record["creator"] = creator
        creator_username = form.get("creator_username", "").strip()
        if creator_username:
            new_record["creator_username"] = creator_username
        new_record["start_time"] = values["start_time"]
        new_record["end_time"] = values["end_time"]
        rows.append(new_record)
        storage.save(rows)
        return "✓ สร้างกลุ่มกิจกรรมเรียบร้อยแล้ว"

    if action == "join":
        username = form.get("username", "").strip()
        if not username:
            return "✗ กรุณาเข้าสู่ระบบก่อนเข้าร่วมกลุ่ม"

        try:
            group_index = int(form.get("group_index", ""))
        except (TypeError, ValueError):
            return "✗ กรุณาเลือกกลุ่มกิจกรรมที่ถูกต้อง"
        if group_index < 0 or group_index >= len(rows):
            return "✗ ไม่พบกลุ่มกิจกรรมนี้แล้ว"
        submitted_key = form.get("group_key", "").strip()
        if submitted_key and submitted_key != _group_key(rows[group_index]):
            return "✗ ไม่พบกลุ่มกิจกรรมนี้แล้ว"

        try:
            group = Activity.from_dict(rows[group_index])
        except (TypeError, ValueError):
            return "✗ ข้อมูลกลุ่มกิจกรรมไม่ถูกต้อง"

        joined_group_keys = _joined_keys(form)
        target_key = _group_key(rows[group_index])
        if target_key in joined_group_keys:
            return "✗ คุณเข้าร่วมกลุ่มนี้แล้ว"
        if is_expired(group.date):
            return "✗ กลุ่มกิจกรรมนี้สิ้นสุดแล้ว"
        if group.is_full():
            return "✗ กลุ่มกิจกรรมนี้เต็มแล้ว"

        target_date = str(rows[group_index].get("date", "")).strip()
        target_start = str(rows[group_index].get("start_time", "")).strip()
        target_end = str(rows[group_index].get("end_time", "")).strip()
        if target_date and target_start and target_end:
            for old_row in rows:
                if _group_key(old_row) not in joined_group_keys or is_expired(old_row.get("date", "")):
                    continue
                old_date = str(old_row.get("date", "")).strip()
                old_start = str(old_row.get("start_time", "")).strip()
                old_end = str(old_row.get("end_time", "")).strip()
                if not old_date or not old_start or not old_end:
                    continue
                if target_date == old_date and times_overlap(
                    target_start, target_end, old_start, old_end
                ):
                    activity_name = str(old_row.get("activity", "กิจกรรมอื่น")).strip()
                    return (
                        "✗ ไม่สามารถเข้าร่วมกลุ่มนี้ได้ เนื่องจากคุณมีกิจกรรม"
                        "ในช่วงเวลานี้แล้ว · เวลาซ้อนกับ: "
                        f"{activity_name} {old_start}–{old_end}"
                    )

        group.members += 1
        group.status = FULL_STATUS if group.is_full() else OPEN_STATUS
        rows[group_index]["members"] = group.members
        rows[group_index]["status"] = group.status
        storage.save(rows)
        return "✓ เข้าร่วมกลุ่มกิจกรรมเรียบร้อยแล้ว"

    if action == "edit":
        username = form.get("username", "").strip()
        if not username:
            return "✗ กรุณาเข้าสู่ระบบก่อนแก้ไขกลุ่ม"
        try:
            group_index = int(form.get("group_index", ""))
        except (TypeError, ValueError):
            return "✗ ไม่พบกลุ่มกิจกรรมที่ต้องการแก้ไข"
        if group_index < 0 or group_index >= len(rows):
            return "✗ ไม่พบกลุ่มกิจกรรมที่ต้องการแก้ไข"

        current_row = rows[group_index]
        submitted_key = form.get("group_key", "").strip()
        if submitted_key and submitted_key != _group_key(current_row):
            return "✗ ไม่พบกลุ่มกิจกรรมที่ต้องการแก้ไข"
        if not _owns_group(current_row, username):
            return "✗ คุณไม่มีสิทธิ์แก้ไขกลุ่มนี้"

        try:
            current_members = int(current_row.get("members", 0))
        except (TypeError, ValueError):
            return "✗ ข้อมูลจำนวนสมาชิกไม่ถูกต้อง"
        values, error = _read_group_fields(form, rows, current_members)
        if error:
            return error

        joined_group_keys = _joined_keys(form)
        current_key = _group_key(current_row)
        if current_key in joined_group_keys:
            for old_row in rows:
                old_key = _group_key(old_row)
                if old_key == current_key or old_key not in joined_group_keys:
                    continue
                if is_expired(old_row.get("date", "")):
                    continue
                old_date = str(old_row.get("date", "")).strip()
                old_start = str(old_row.get("start_time", "")).strip()
                old_end = str(old_row.get("end_time", "")).strip()
                if not old_date or not old_start or not old_end:
                    continue
                if values["date"] == old_date and times_overlap(
                    values["start_time"], values["end_time"], old_start, old_end
                ):
                    return "✗ เวลาใหม่ซ้อนกับกิจกรรมที่คุณเข้าร่วมแล้ว"

        current_row["group_name"] = values["group_name"]
        current_row["activity"] = values["activity"]
        current_row["place"] = values["place"]
        current_row["date"] = values["date"]
        current_row["start_time"] = values["start_time"]
        current_row["end_time"] = values["end_time"]
        current_row["max_members"] = values["max_members"]
        current_row["status"] = FULL_STATUS if current_members >= values["max_members"] else OPEN_STATUS
        storage.save(rows)
        return "✓ บันทึกการแก้ไขกลุ่มเรียบร้อยแล้ว"

    if action == "delete":
        username = form.get("username", "").strip()
        if not username:
            return "✗ กรุณาเข้าสู่ระบบก่อนลบกลุ่ม"
        try:
            group_index = int(form.get("group_index", ""))
        except (TypeError, ValueError):
            return "✗ ไม่พบกลุ่มกิจกรรมที่ต้องการลบ"
        if group_index < 0 or group_index >= len(rows):
            return "✗ ไม่พบกลุ่มกิจกรรมที่ต้องการลบ"
        submitted_key = form.get("deleted_group_key", "").strip()
        if submitted_key and submitted_key != _group_key(rows[group_index]):
            return "✗ ไม่พบกลุ่มกิจกรรมที่ต้องการลบ"
        if not _owns_group(rows[group_index], username):
            return "✗ คุณไม่มีสิทธิ์ลบกลุ่มนี้"

        rows.pop(group_index)
        storage.save(rows)
        return "✓ ลบกลุ่มกิจกรรมเรียบร้อยแล้ว"

    return "✗ กรุณาเลือกคำสั่งที่ถูกต้อง"


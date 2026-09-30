"""pages/page1.py — ★ your page 1."""
import storage

TITLE = "เริ่มออกเดินทาง · DISCOVER ACTIVITIES"

ICON_MAP = {
    "วิ่ง": "🏃",
    "ฟุตบอล": "⚽",
    "บาสเกตบอล": "🏀",
    "แบดมินตัน": "🏸",
    "วอลเลย์บอล": "🏐",
    "ว่ายน้ำ": "🏊",
    "เทเบิลเทนนิส": "🏓",
    "บอร์ดเกม": "🎲",
    "ซ้อมดนตรี": "🎵",
    "เดินเล่น": "🚶"
}

def build(query=None):
    if query is None:
        query = {}
    
    search_keyword = query.get("q", "").strip().lower()
    items = storage.load()
    
    activity_summary = {}
    
    for row in items:
        activity_name = row.get("activity")
        if not activity_name:
            continue
            
        # If there's a search keyword, skip activities that don't match
        if search_keyword and search_keyword not in activity_name.lower():
            continue
            
        place = row.get("place", "")
        
        if activity_name not in activity_summary:
            icon = ICON_MAP.get(activity_name, "🎯")
            activity_summary[activity_name] = {
                "name": activity_name,
                "icon": icon,
                "group_count": 0,
                "places": []
            }
            
        activity_summary[activity_name]["group_count"] += 1
        if place and place not in activity_summary[activity_name]["places"]:
            activity_summary[activity_name]["places"].append(place)
            
    # Convert dictionary to list
    activities = list(activity_summary.values())
    
    return {
        "activities": activities,
        "search_keyword": search_keyword
    }

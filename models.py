"""models.py — Data model for university activity matching."""


class Activity:
    """Represents a university activity group for finding activity partners."""

    def __init__(
        self,
        activity,
        place,
        group_name,
        date,
        members,
        max_members,
        status="เปิดรับ",
    ):
        self.activity = str(activity)
        self.place = str(place)
        self.group_name = str(group_name)
        self.date = str(date)
        self.members = int(members)
        self.max_members = int(max_members)
        self.status = str(status)

    def is_full(self):
        """Check if the activity has reached maximum capacity."""
        return self.members >= self.max_members

    def has_available_space(self):
        """Check if there is room for more participants."""
        return self.members < self.max_members

    def remaining_spaces(self):
        """Return the number of remaining spots available."""
        return max(0, self.max_members - self.members)

    def describe(self):
        """Return a readable summary of the activity group."""
        return f"{self.group_name} ({self.activity}) ณ {self.place} วันที่ {self.date} [{self.status} {self.members}/{self.max_members}]"

    def to_dict(self):
        """Convert the Activity object into a dictionary matching data.json."""
        return {
            "activity": self.activity,
            "place": self.place,
            "group_name": self.group_name,
            "date": self.date,
            "members": self.members,
            "max_members": self.max_members,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Create an Activity instance from a dictionary record."""
        return cls(
            activity=data.get("activity", ""),
            place=data.get("place", ""),
            group_name=data.get("group_name", ""),
            date=data.get("date", ""),
            members=data.get("members", 0),
            max_members=data.get("max_members", 0),
            status=data.get("status", "เปิดรับ"),
        )


# Backward compatibility alias
Item = Activity

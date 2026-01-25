"""Data models for Baby Tracker."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

@dataclass
class BabyEvent:
    """Representation of a single event."""
    type: Literal["feeding", "poo", "pee", "growth", "diaper"]
    start: datetime
    end: datetime | None = None
    summary: str = ""
    description: str = ""
    data: dict = field(default_factory=dict)  # Extra data like side, weight, etc.

    @classmethod
    def from_dict(cls, data: dict) -> BabyEvent | None:
        """Create object from dict with validation."""
        try:
            return cls(
                type=data["type"],
                start=datetime.fromisoformat(data["start"]),
                end=datetime.fromisoformat(data["end"]) if data.get("end") else None,
                summary=data.get("summary", ""),
                description=data.get("description", ""),
                data=data.get("data", {})
            )
        except (KeyError, ValueError):
            return None

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "type": self.type,
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
            "summary": self.summary,
            "description": self.description,
            "data": self.data
        }

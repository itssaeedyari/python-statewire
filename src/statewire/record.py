from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TransitionRecord:
    source: str
    event: str
    target: str
    timestamp: datetime = field(default_factory=_utc_now)
    context: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "event": self.event,
            "target": self.target,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }

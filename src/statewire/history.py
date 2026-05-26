from collections import deque
from collections.abc import Iterator

from statewire.record import TransitionRecord


class History:
    def __init__(self, max_size: int = 100) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._records: deque[TransitionRecord] = deque(maxlen=max_size)

    def record(self, entry: TransitionRecord) -> None:
        self._records.append(entry)

    @property
    def last(self) -> TransitionRecord | None:
        return self._records[-1] if self._records else None

    @property
    def records(self) -> list[TransitionRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[TransitionRecord]:
        return iter(list(self._records))

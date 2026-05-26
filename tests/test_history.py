from datetime import timezone

import pytest

from statewire.history import History
from statewire.record import TransitionRecord


def _make_record(
    source: str = "off", event: str = "toggle", target: str = "on"
) -> TransitionRecord:
    return TransitionRecord(source=source, event=event, target=target)


class TestHistory:
    def test_empty_on_init(self) -> None:
        h = History()
        assert len(h) == 0
        assert h.last is None
        assert h.records == []

    def test_record_toggle_on(self) -> None:
        h = History()
        rec = _make_record("off", "toggle", "on")
        h.record(rec)

        assert len(h) == 1
        assert h.last is not None
        assert h.last.source == "off"
        assert h.last.target == "on"
        assert h.last.event == "toggle"

    def test_record_toggle_off(self) -> None:
        h = History()
        rec = _make_record("on", "toggle", "off")
        h.record(rec)

        assert h.last is not None
        assert h.last.source == "on"
        assert h.last.target == "off"

    def test_multiple_toggles(self) -> None:
        h = History()
        h.record(_make_record("off", "toggle", "on"))
        h.record(_make_record("on", "toggle", "off"))
        h.record(_make_record("off", "toggle", "on"))

        assert len(h) == 3
        assert h.last is not None
        assert h.last.source == "off"
        assert h.last.target == "on"

    def test_records_returns_copy(self) -> None:
        h = History()
        h.record(_make_record())
        records = h.records
        records.clear()

        assert len(h) == 1

    def test_clear(self) -> None:
        h = History()
        h.record(_make_record("off", "toggle", "on"))
        h.record(_make_record("on", "toggle", "off"))
        h.clear()

        assert len(h) == 0
        assert h.last is None

    def test_iteration(self) -> None:
        h = History()
        h.record(_make_record("off", "toggle", "on"))
        h.record(_make_record("on", "toggle", "off"))

        sources = [r.source for r in h]
        assert sources == ["off", "on"]

    def test_max_size_drops_oldest(self) -> None:
        h = History(max_size=2)
        h.record(_make_record("off", "toggle", "on"))
        h.record(_make_record("on", "toggle", "off"))
        h.record(_make_record("off", "toggle", "on"))

        assert len(h) == 2
        assert h.records[0].source == "on"
        assert h.records[1].source == "off"

    def test_max_size_one(self) -> None:
        h = History(max_size=1)
        h.record(_make_record("off", "toggle", "on"))
        h.record(_make_record("on", "toggle", "off"))

        assert len(h) == 1
        assert h.last is not None
        assert h.last.target == "off"

    def test_invalid_max_size(self) -> None:
        with pytest.raises(ValueError, match="max_size"):
            History(max_size=0)

    def test_timestamp_is_utc(self) -> None:
        h = History()
        h.record(_make_record())

        assert h.last is not None
        assert h.last.timestamp.tzinfo == timezone.utc

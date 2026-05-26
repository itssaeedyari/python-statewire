from datetime import datetime, timezone

from statewire.record import TransitionRecord


class TestTransitionRecordCreation:
    def test_creation_with_required_fields(self) -> None:
        record = TransitionRecord(source="on", event="toggle", target="off")

        assert record.source == "on"
        assert record.event == "toggle"
        assert record.target == "off"

    def test_timestamp_defaults_to_utc(self) -> None:
        record = TransitionRecord(source="on", event="toggle", target="off")

        assert record.timestamp.tzinfo == timezone.utc

    def test_context_defaults_to_none(self) -> None:
        record = TransitionRecord(source="on", event="toggle", target="off")

        assert record.context is None

    def test_context_stores_metadata(self) -> None:
        ctx = {"user_id": 42, "reason": "timeout"}
        record = TransitionRecord(
            source="on", event="toggle", target="off", context=ctx
        )

        assert record.context == {"user_id": 42, "reason": "timeout"}


class TestTransitionRecordSerialization:
    def test_to_dict_contains_all_fields(self) -> None:
        record = TransitionRecord(
            source="on", event="toggle", target="off", context={"key": "value"}
        )
        result = record.to_dict()

        assert result["source"] == "on"
        assert result["event"] == "toggle"
        assert result["target"] == "off"
        assert result["context"] == {"key": "value"}
        assert "timestamp" in result

    def test_to_dict_timestamp_is_iso_format(self) -> None:
        record = TransitionRecord(source="on", event="toggle", target="off")
        result = record.to_dict()

        parsed = datetime.fromisoformat(result["timestamp"])
        assert parsed.tzinfo is not None

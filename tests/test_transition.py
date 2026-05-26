from enum import Enum

from python_statewire.transition import Transition


class State(str, Enum):
    A = "a"
    B = "b"


class Event(str, Enum):
    GO = "go"


class TestTransitionCreation:
    """Transition stores source, event, target and optional fields correctly."""

    def test_string_fields(self) -> None:
        t = Transition(source="a", event="go", target="b")
        assert t.source == "a"
        assert t.event == "go"
        assert t.target == "b"

    def test_enum_fields(self) -> None:
        t = Transition(source=State.A, event=Event.GO, target=State.B)
        assert t.source == State.A
        assert t.event == Event.GO
        assert t.target == State.B

    def test_mixed_fields(self) -> None:
        t = Transition(source=State.A, event="go", target="b")
        assert t.source == State.A
        assert t.event == "go"
        assert t.target == "b"

    def test_defaults(self) -> None:
        t = Transition(source="a", event="go", target="b")
        assert t.guards == ()
        assert t.before == ()
        assert t.after == ()
        assert t.description == ""

    def test_with_optional_fields(self) -> None:
        def guard() -> bool:
            return True

        def before_hook() -> None:
            return None

        def after_hook() -> None:
            return None

        t = Transition(
            source="a",
            event="go",
            target="b",
            guards=(guard,),
            before=(before_hook,),
            after=(after_hook,),
            description="Activate the system",
        )
        assert t.guards == (guard,)
        assert t.before == (before_hook,)
        assert t.after == (after_hook,)
        assert t.description == "Activate the system"

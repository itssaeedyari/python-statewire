from enum import Enum
from typing import Any

import pytest

from statewire.core import StateMachine
from statewire.exceptions import (
    GuardRejectException,
    InvalidEventException,
    InvalidStateException,
    InvalidTransitionException,
)


class TestBasicTransition:
    def test_toggle(self) -> None:
        sm = StateMachine(
            name="Light",
            states=["OFF", "ON"],
            events=["TOGGLE"],
            initial_state="OFF",
        )
        sm.add_transition("OFF", "TOGGLE", "ON")
        sm.add_transition("ON", "TOGGLE", "OFF")

        assert sm.state == "OFF"
        sm.trigger("TOGGLE")
        assert sm.state == "ON"
        sm.trigger("TOGGLE")
        assert sm.state == "OFF"

    def test_invalid_transition_raises(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B")

        sm.trigger("GO")
        with pytest.raises(InvalidTransitionException):
            sm.trigger("GO")


class TestGuards:
    def test_guard_rejects(self) -> None:
        def allowed_guard(**ctx: object) -> bool:
            return bool(ctx.get("allowed", False))

        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B", guards=(allowed_guard,))

        with pytest.raises(GuardRejectException):
            sm.trigger("GO", context={"allowed": False})

        sm.trigger("GO", context={"allowed": True})
        assert sm.state == "B"

    def test_can_trigger(self) -> None:
        def threshold_guard(**ctx: Any) -> bool:
            x = ctx.get("x", 0)
            return int(x) > 5

        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B", guards=(threshold_guard,))

        assert sm.can_trigger("GO", context={"x": 10}) is True
        assert sm.can_trigger("GO", context={"x": 2}) is False
        assert sm.can_trigger("UNKNOWN") is False


class TestCallbacks:
    def test_hooks_execution_order(self) -> None:
        log: list[str] = []

        def before_hook(**_ctx: object) -> None:
            log.append("before")

        def after_hook(**_ctx: object) -> None:
            log.append("after")

        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B", before=(before_hook,), after=(after_hook,))
        sm.on_exit("A", lambda **_kwargs: log.append("exit_A"))
        sm.on_enter("B", lambda **_kwargs: log.append("enter_B"))

        sm.trigger("GO")
        assert log == ["exit_A", "before", "after", "enter_B"]


class TestHistory:
    def test_history_tracking(self) -> None:
        sm = StateMachine(states=["A", "B", "C"], events=["X", "Y"], initial_state="A")
        sm.add_transition("A", "X", "B")
        sm.add_transition("B", "Y", "C")

        sm.trigger("X")
        sm.trigger("Y")

        assert sm.history is not None
        assert len(sm.history) == 2
        assert sm.history.last is not None
        assert sm.history.last.target == "C"
        assert sm.history.records[0].source == "A"


class TestIntrospection:
    def test_available_events(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO", "BACK"], initial_state="A")
        sm.add_transition("A", "GO", "B")
        sm.add_transition("B", "BACK", "A")

        assert sm.available_events() == ["GO"]
        sm.trigger("GO")
        assert sm.available_events() == ["BACK"]

    def test_invalid_state_registration(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        with pytest.raises(InvalidStateException):
            sm.add_transition("A", "GO", "C")


class TestEnumSupport:
    """Cover Enum-based states/events (line 69)."""

    def test_enum_states_and_events(self) -> None:
        class Light(Enum):
            OFF = "OFF"
            ON = "ON"

        class Action(Enum):
            TOGGLE = "TOGGLE"

        sm = StateMachine(
            name="EnumMachine",
            states=Light,
            events=Action,
            initial_state=Light.OFF,
        )
        sm.add_transition(Light.OFF, Action.TOGGLE, Light.ON)
        sm.add_transition(Light.ON, Action.TOGGLE, Light.OFF)

        assert sm.state == "OFF"
        sm.trigger(Action.TOGGLE)
        assert sm.state == "ON"


class TestSetStateValidation:
    """Cover set_state with invalid state (line 90)."""

    def test_set_state_invalid_raises(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        with pytest.raises(InvalidStateException):
            sm.set_state("Z")


class TestIsTerminal:
    """Cover is_terminal property (line 96)."""

    def test_terminal_state(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B")

        assert sm.is_terminal is False
        sm.trigger("GO")
        assert sm.is_terminal is True


class TestAddTransitionValidation:
    """Cover invalid target state and invalid event (lines 115-121)."""

    def test_invalid_target_state(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        with pytest.raises(InvalidStateException):
            sm.add_transition("A", "GO", "X")

    def test_invalid_source_state(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        with pytest.raises(InvalidStateException):
            sm.add_transition("X", "GO", "B")

    def test_invalid_event(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        with pytest.raises(InvalidEventException):
            sm.add_transition("A", "UNKNOWN", "B")

    def test_no_predefined_states(self) -> None:
        sm = StateMachine(states=[], events=["GO"])
        sm.add_transition("A", "GO", "B")
        sm.set_state("A")
        sm.trigger("GO")
        assert sm.state == "B"


class TestTriggerEdgeCases:
    """Cover trigger when current_state is None (line 153)."""

    def test_trigger_without_initial_state(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        sm.add_transition("A", "GO", "B")

        with pytest.raises(InvalidTransitionException):
            sm.trigger("GO")

    def test_trigger_with_global_transition_listener(self) -> None:
        """Cover on_transition listener execution (line 188)."""
        log: list[dict[str, Any]] = []

        def listener(**kwargs: Any) -> None:
            log.append(kwargs)

        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B")
        sm.on_transition_callback(listener)

        sm.trigger("GO", context={"info": "test"})

        assert len(log) == 1
        assert log[0]["source"] == "A"
        assert log[0]["target"] == "B"
        assert log[0]["event"] == "GO"

    def test_trigger_without_history(self) -> None:
        """Cover branch when track_history=False (line 191->200)."""
        sm = StateMachine(
            states=["A", "B"], events=["GO"], initial_state="A", track_history=False
        )
        sm.add_transition("A", "GO", "B")

        result = sm.trigger("GO")
        assert result == "B"
        assert sm.history is None


class TestCanTriggerNoState:
    """Cover can_trigger when current_state is None (line 207)."""

    def test_can_trigger_no_initial_state(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        sm.add_transition("A", "GO", "B")

        assert sm.can_trigger("GO") is False


class TestOnExitListener:
    """Cover on_exit registration (lines 232-233)."""

    def test_on_exit_callback(self) -> None:
        log: list[str] = []

        sm = StateMachine(states=["A", "B"], events=["GO"], initial_state="A")
        sm.add_transition("A", "GO", "B")
        sm.on_exit("A", lambda **_kwargs: log.append("exited_A"))

        sm.trigger("GO")
        assert log == ["exited_A"]


class TestSerialization:
    """Cover to_dict and __repr__ (lines 245, 249, 253, 257, 265)."""

    def test_to_dict(self) -> None:
        sm = StateMachine(
            name="TestMachine",
            states=["A", "B"],
            events=["GO"],
            initial_state="A",
        )
        sm.add_transition("A", "GO", "B")

        d = sm.to_dict()
        assert d["name"] == "TestMachine"
        assert d["current_state"] == "A"
        assert d["states"] == ["A", "B"]
        assert d["events"] == ["GO"]

    def test_states_property(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        assert sm.states == {"A", "B"}

    def test_events_property(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        assert sm.events == {"GO"}

    def test_transitions_property(self) -> None:
        sm = StateMachine(states=["A", "B"], events=["GO"])
        sm.add_transition("A", "GO", "B")
        assert len(sm.transitions) == 1
        assert sm.transitions[0].source == "A"

    def test_repr(self) -> None:
        sm = StateMachine(name="MyMachine", states=["A"], initial_state="A")
        assert repr(sm) == "<MyMachine state=A>"


class TestBulkTransitions:
    """Cover add_transitions (line 153 area)."""

    def test_add_transitions_bulk(self) -> None:
        sm = StateMachine(states=["A", "B", "C"], events=["X", "Y"], initial_state="A")
        sm.add_transitions(
            [
                {"source": "A", "event": "X", "target": "B"},
                {"source": "B", "event": "Y", "target": "C"},
            ]
        )

        sm.trigger("X")
        assert sm.state == "B"
        sm.trigger("Y")
        assert sm.state == "C"

import pytest

from statewire.exceptions import (
    GuardRejectException,
    InvalidEventException,
    InvalidStateException,
    InvalidTransitionException,
    StateMachineException,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_base(self) -> None:
        assert issubclass(InvalidTransitionException, StateMachineException)
        assert issubclass(GuardRejectException, StateMachineException)
        assert issubclass(InvalidStateException, StateMachineException)
        assert issubclass(InvalidEventException, StateMachineException)

    def test_base_inherits_from_exception(self) -> None:
        assert issubclass(StateMachineException, Exception)


class TestInvalidTransitionException:
    def test_fields(self) -> None:
        exc = InvalidTransitionException("TOGGLE", "OFF", "Light")
        assert exc.event == "TOGGLE"
        assert exc.current_state == "OFF"
        assert exc.machine_name == "Light"

    def test_message(self) -> None:
        exc = InvalidTransitionException("TOGGLE", "OFF", "Light")
        assert str(exc) == "[Light] Cannot process event 'TOGGLE' in state 'OFF'"

    def test_default_machine_name(self) -> None:
        exc = InvalidTransitionException("GO", "A")
        assert exc.machine_name == "StateMachine"
        assert "[StateMachine]" in str(exc)

    def test_catchable_as_base(self) -> None:
        with pytest.raises(StateMachineException):
            raise InvalidTransitionException("X", "Y")


class TestGuardRejectException:
    def test_fields(self) -> None:
        exc = GuardRejectException("TOGGLE", "OFF")
        assert exc.event == "TOGGLE"
        assert exc.current_state == "OFF"

    def test_message_without_guard_name(self) -> None:
        exc = GuardRejectException("TOGGLE", "OFF")
        assert str(exc) == (
            "Guard rejected transition on event 'TOGGLE' from state 'OFF'"
        )

    def test_message_with_guard_name(self) -> None:
        exc = GuardRejectException("TOGGLE", "OFF", guard_name="is_allowed")
        assert "(guard: is_allowed)" in str(exc)

    def test_catchable_as_base(self) -> None:
        with pytest.raises(StateMachineException):
            raise GuardRejectException("X", "Y")


class TestInvalidStateException:
    def test_fields(self) -> None:
        exc = InvalidStateException("C", {"A", "B"})
        assert exc.state == "C"
        assert exc.valid_states == {"A", "B"}

    def test_message(self) -> None:
        exc = InvalidStateException("C", ["A", "B"])
        assert "Invalid state 'C'" in str(exc)
        assert "Valid states:" in str(exc)

    def test_catchable_as_base(self) -> None:
        with pytest.raises(StateMachineException):
            raise InvalidStateException("X", [])


class TestInvalidEventException:
    def test_fields(self) -> None:
        exc = InvalidEventException("FLY", {"GO", "STOP"})
        assert exc.event == "FLY"
        assert exc.valid_events == {"GO", "STOP"}

    def test_message(self) -> None:
        exc = InvalidEventException("FLY", ["GO", "STOP"])
        assert "Invalid event 'FLY'" in str(exc)
        assert "Valid events:" in str(exc)

    def test_catchable_as_base(self) -> None:
        with pytest.raises(StateMachineException):
            raise InvalidEventException("X", [])

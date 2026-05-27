from collections.abc import Collection


class StateMachineException(Exception):
    """Base exception for state machine Exceptions."""

    pass


class InvalidTransitionException(StateMachineException):
    """Raised when an event is not valid for the current state."""

    def __init__(
        self, event: str, current_state: str, machine_name: str = "StateMachine"
    ) -> None:
        self.event = event
        self.current_state = current_state
        self.machine_name = machine_name
        super().__init__(
            f"[{machine_name}] Cannot process event '{event}' "
            f"in state '{current_state}'"
        )


class GuardRejectException(StateMachineException):
    """Raised when a transition guard condition rejects the transition."""

    def __init__(
        self, event: str, current_state: str, guard_name: str | None = None
    ) -> None:
        self.event = event
        self.current_state = current_state
        msg = (
            f"Guard rejected transition on event '{event}' from state '{current_state}'"
        )
        if guard_name:
            msg += f" (guard: {guard_name})"
        super().__init__(msg)


class InvalidStateException(StateMachineException):
    """Raised when an invalid state is referenced."""

    def __init__(self, state: str, valid_states: Collection[str]) -> None:
        self.state = state
        self.valid_states = valid_states
        super().__init__(f"Invalid state '{state}'. Valid states: {valid_states}")


class InvalidEventException(StateMachineException):
    """Raised when an invalid event is referenced."""

    def __init__(self, event: str, valid_events: Collection[str]) -> None:
        self.event = event
        self.valid_events = valid_events
        super().__init__(f"Invalid event '{event}'. Valid events: {valid_events}")

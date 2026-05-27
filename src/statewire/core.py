from collections.abc import Callable
from enum import Enum
from typing import Any

from statewire.exceptions import (
    GuardRejectException,
    InvalidEventException,
    InvalidStateException,
    InvalidTransitionException,
)
from .history import History
from .record import TransitionRecord
from .transition import Transition
from .types import Event, Hook, State


def _check_guards(transition: Transition, context: dict[str, Any]) -> bool:
    """Run all guards. Returns True if all pass."""
    return all(guard(**context) for guard in transition.guards)


def _run_hooks(hooks: tuple[Hook, ...], context: dict[str, Any]) -> None:
    """Execute a sequence of hooks with the given context."""
    for hook in hooks:
        hook(**context)


class StateMachine:
    """
    A flexible, framework-agnostic state machine.

    Supports:
    - Enum or string-based states/events
    - Guard conditions on transitions
    - Before/after hooks
    - Global listeners (on_enter_state, on_exit_state, on_transition)
    - Transition history tracking
    """

    def __init__(
        self,
        name: str = "StateMachine",
        states: type[Enum] | list[str] | None = None,
        events: type[Enum] | list[str] | None = None,
        initial_state: State | None = None,
        track_history: bool = True,
        max_history: int = 100,
    ) -> None:
        self.name = name
        self._states: set[str] = self._resolve_values(states)
        self._events: set[str] = self._resolve_values(events)
        self._transitions: dict[tuple[str, str], Transition] = {}
        self._current_state: str | None = None
        self._track_history = track_history
        self._history = History(max_size=max_history) if track_history else None

        # Global listeners
        self._on_enter: dict[str, list[Callable[..., Any]]] = {}
        self._on_exit: dict[str, list[Callable[..., Any]]] = {}
        self._on_transition: list[Callable[..., Any]] = []

        if initial_state is not None:
            self.set_state(initial_state)

    @staticmethod
    def _resolve_values(source: type[Enum] | list[str] | None) -> set[str]:
        if source is None:
            return set()
        if isinstance(source, type) and issubclass(source, Enum):
            return {str(item.value) for item in source}
        return set(source)

    @staticmethod
    def _to_str(value: str | Enum) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    # ─── State Management ───────────────────────────────────────

    @property
    def state(self) -> str | None:
        return self._current_state

    def set_state(self, state: State) -> None:
        """Set state directly (no transition logic). Used for initialization."""
        s = self._to_str(state)
        if self._states and s not in self._states:
            raise InvalidStateException(s, self._states)
        self._current_state = s

    @property
    def is_terminal(self) -> bool:
        """Check if current state has no outgoing transitions."""
        return not any(src == self._current_state for src, _ in self._transitions)

    # ─── Transition Registration ────────────────────────────────

    def add_transition(
        self,
        source: State,
        event: Event,
        target: State,
        guards: tuple[Callable[..., bool], ...] = (),
        before: tuple[Callable[..., None], ...] = (),
        after: tuple[Callable[..., None], ...] = (),
        description: str = "",
    ) -> "StateMachine":
        """Register a transition. Returns self for chaining."""
        src = self._to_str(source)
        evt = self._to_str(event)
        tgt = self._to_str(target)

        if self._states:
            if src not in self._states:
                raise InvalidStateException(src, self._states)
            if tgt not in self._states:
                raise InvalidStateException(tgt, self._states)
        if self._events and evt not in self._events:
            raise InvalidEventException(evt, self._events)

        transition = Transition(
            source=src,
            event=evt,
            target=tgt,
            guards=guards,
            before=before,
            after=after,
            description=description,
        )
        self._transitions[(src, evt)] = transition
        return self

    def add_transitions(self, transitions: list[dict[str, Any]]) -> "StateMachine":
        """Bulk-add transitions from a list of dicts."""
        for t in transitions:
            self.add_transition(**t)
        return self

    # ─── Event Processing ───────────────────────────────────────

    def trigger(self, event: Event, context: dict[str, Any] | None = None) -> str:
        """
        Process an event. Returns the new state.

        Raises InvalidTransitionError if no valid transition exists.
        Raises GuardRejectError if guards reject the transition.
        """
        evt = self._to_str(event)

        if self._current_state is None:
            raise InvalidTransitionException(evt, "", self.name)

        key = (self._current_state, evt)
        transition = self._transitions.get(key)
        if transition is None:
            raise InvalidTransitionException(evt, self._current_state, self.name)

        ctx = context or {}

        # Check guards
        if not _check_guards(transition, ctx):
            raise GuardRejectException(evt, self._current_state)

        source = self._current_state
        target = self._to_str(transition.target)

        # Execute exit callbacks
        for cb in self._on_exit.get(source, []):
            cb(state=source, event=evt, context=ctx)

        # Execute before hooks
        _run_hooks(transition.before, ctx)

        # Transition
        self._current_state = target

        # Execute after hooks
        _run_hooks(transition.after, ctx)

        # Execute enter callbacks
        for cb in self._on_enter.get(target, []):
            cb(state=target, event=evt, context=ctx)

        # Global transition listeners
        for listener in self._on_transition:
            listener(source=source, event=evt, target=target, context=ctx)

        # Record history
        if self._history is not None:
            record = TransitionRecord(
                source=source,
                event=evt,
                target=target,
                context=ctx if ctx else None,
            )
            self._history.record(record)

        assert self._current_state is not None
        return self._current_state

    def can_trigger(self, event: Event, context: dict[str, Any] | None = None) -> bool:
        """Check if an event can be triggered without actually triggering it."""
        evt = self._to_str(event)
        if self._current_state is None:
            return False
        key = (self._current_state, evt)
        transition = self._transitions.get(key)
        if transition is None:
            return False
        ctx = context or {}
        return _check_guards(transition, ctx)

    def available_events(self) -> list[str]:
        """Get list of events available from the current state."""
        return [evt for (src, evt) in self._transitions if src == self._current_state]

    # ─── Listeners ──────────────────────────────────────────────

    def on_enter(self, state: State, callback: Callable[..., Any]) -> "StateMachine":
        s = self._to_str(state)
        self._on_enter.setdefault(s, []).append(callback)
        return self

    def on_exit(self, state: State, callback: Callable[..., Any]) -> "StateMachine":
        s = self._to_str(state)
        self._on_exit.setdefault(s, []).append(callback)
        return self

    def on_transition_callback(self, callback: Callable[..., Any]) -> "StateMachine":
        self._on_transition.append(callback)
        return self

    # ─── History ────────────────────────────────────────────────

    @property
    def history(self) -> History | None:
        return self._history

    # ─── Introspection ──────────────────────────────────────────

    @property
    def states(self) -> set[str]:
        return set(self._states)

    @property
    def events(self) -> set[str]:
        return set(self._events)

    @property
    def transitions(self) -> list[Transition]:
        return list(self._transitions.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialize current machine state."""
        return {
            "name": self.name,
            "current_state": self._current_state,
            "states": sorted(self._states),
            "events": sorted(self._events),
        }

    def __repr__(self) -> str:
        return f"<{self.name} state={self._current_state}>"

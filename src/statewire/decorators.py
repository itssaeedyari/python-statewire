from collections.abc import Callable
from enum import Enum
from typing import Any

from .core import StateMachine

_F = Callable[..., Any]


class MachineConfig:
    """Declarative state machine builder using class-based configuration."""

    name: str = "StateMachine"
    states: type[Enum] | list[str] | None = None
    events: type[Enum] | list[str] | None = None
    initial: str | Enum | None = None
    transitions: list[dict[str, Any]] = []

    _enter_hooks: dict[str, list[str]]
    _exit_hooks: dict[str, list[str]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._enter_hooks = {}
        cls._exit_hooks = {}
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name, None)
            if callable(attr):
                if hasattr(attr, "_on_enter_state"):
                    state = attr._on_enter_state
                    cls._enter_hooks.setdefault(state, []).append(attr_name)
                if hasattr(attr, "_on_exit_state"):
                    state = attr._on_exit_state
                    cls._exit_hooks.setdefault(state, []).append(attr_name)

    def build(self) -> StateMachine:
        """Build a StateMachine instance from this config."""
        machine = StateMachine(
            name=self.name,
            states=self.states,
            events=self.events,
            initial_state=self.initial,
        )
        machine.add_transitions(self.transitions)

        for state, method_names in self._enter_hooks.items():
            for method_name in method_names:
                method = getattr(self, method_name)
                machine.on_enter(state, method)

        for state, method_names in self._exit_hooks.items():
            for method_name in method_names:
                method = getattr(self, method_name)
                machine.on_exit(state, method)

        return machine


def on_enter(state: str | Enum) -> Callable[[_F], _F]:
    """Decorator to mark a method as an on-enter hook for a state."""
    s = state.value if isinstance(state, Enum) else state

    def decorator(func: _F) -> _F:
        func._on_enter_state = s  # type: ignore[attr-defined]
        return func

    return decorator


def on_exit(state: str | Enum) -> Callable[[_F], _F]:
    """Decorator to mark a method as an on-exit hook for a state."""
    s = state.value if isinstance(state, Enum) else state

    def decorator(func: _F) -> _F:
        func._on_exit_state = s  # type: ignore[attr-defined]
        return func

    return decorator

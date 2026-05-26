from dataclasses import dataclass

from statewire.types import Event, Guard, Hook, State


@dataclass(frozen=True)
class Transition:
    source: State
    event: Event
    target: State
    guards: tuple[Guard, ...] = ()
    before: tuple[Hook, ...] = ()
    after: tuple[Hook, ...] = ()
    description: str = ""

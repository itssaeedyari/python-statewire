# src/statewire/types.py
from collections.abc import Callable
from enum import Enum

State = str | Enum
Event = str | Enum
Guard = Callable[..., bool]
Hook = Callable[..., None]

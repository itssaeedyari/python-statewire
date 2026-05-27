from collections.abc import Callable
from enum import Enum

from statewire.core import StateMachine


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDING = "REFUNDING"
    REFUNDED = "REFUNDED"


class PaymentEvent(str, Enum):
    INITIATE = "INITIATE"
    CONFIRM = "CONFIRM"
    SETTLE = "SETTLE"
    FAIL = "FAIL"
    REFUND = "REFUND"
    COMPLETE = "COMPLETE"


def create_payment_machine(
    payment_id: str | None = None,
    on_completed: Callable[..., None] | None = None,
    on_failed: Callable[..., None] | None = None,
) -> StateMachine:
    machine = StateMachine(
        name=f"Payment({payment_id or 'new'})",
        states=PaymentStatus,
        events=PaymentEvent,
        initial_state=PaymentStatus.CREATED,
    )
    machine.add_transitions(
        [
            {
                "source": PaymentStatus.CREATED,
                "event": PaymentEvent.INITIATE,
                "target": PaymentStatus.PENDING,
                "description": "Payment initiated by user",
            },
            {
                "source": PaymentStatus.PENDING,
                "event": PaymentEvent.CONFIRM,
                "target": PaymentStatus.PROCESSING,
                "description": "Payment confirmed by gateway",
            },
            {
                "source": PaymentStatus.PENDING,
                "event": PaymentEvent.FAIL,
                "target": PaymentStatus.FAILED,
                "description": "Payment failed at gateway",
            },
            {
                "source": PaymentStatus.PROCESSING,
                "event": PaymentEvent.SETTLE,
                "target": PaymentStatus.COMPLETED,
                "description": "Payment settled successfully",
            },
            {
                "source": PaymentStatus.PROCESSING,
                "event": PaymentEvent.FAIL,
                "target": PaymentStatus.FAILED,
                "description": "Payment processing failed",
            },
            {
                "source": PaymentStatus.COMPLETED,
                "event": PaymentEvent.REFUND,
                "target": PaymentStatus.REFUNDING,
                "description": "Refund requested",
            },
            {
                "source": PaymentStatus.REFUNDING,
                "event": PaymentEvent.COMPLETE,
                "target": PaymentStatus.REFUNDED,
                "description": "Refund completed",
            },
            {
                "source": PaymentStatus.REFUNDING,
                "event": PaymentEvent.FAIL,
                "target": PaymentStatus.FAILED,
                "description": "Refund failed",
            },
        ]
    )
    if on_completed:
        machine.on_enter(PaymentStatus.COMPLETED, on_completed)
    if on_failed:
        machine.on_enter(PaymentStatus.FAILED, on_failed)
    return machine

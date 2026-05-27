from enum import Enum

from statewire.core import StateMachine


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class OrderEvent(str, Enum):
    SUBMIT = "SUBMIT"
    CONFIRM = "CONFIRM"
    PREPARE = "PREPARE"
    SHIP = "SHIP"
    DELIVER = "DELIVER"
    CANCEL = "CANCEL"
    RETURN = "RETURN"


def create_order_machine(order_id: str | None = None) -> StateMachine:
    machine = StateMachine(
        name=f"Order({order_id or 'new'})",
        states=OrderStatus,
        events=OrderEvent,
        initial_state=OrderStatus.DRAFT,
    )
    machine.add_transitions(
        [
            {
                "source": OrderStatus.DRAFT,
                "event": OrderEvent.SUBMIT,
                "target": OrderStatus.SUBMITTED,
            },
            {
                "source": OrderStatus.SUBMITTED,
                "event": OrderEvent.CONFIRM,
                "target": OrderStatus.CONFIRMED,
            },
            {
                "source": OrderStatus.SUBMITTED,
                "event": OrderEvent.CANCEL,
                "target": OrderStatus.CANCELLED,
            },
            {
                "source": OrderStatus.CONFIRMED,
                "event": OrderEvent.PREPARE,
                "target": OrderStatus.PREPARING,
            },
            {
                "source": OrderStatus.CONFIRMED,
                "event": OrderEvent.CANCEL,
                "target": OrderStatus.CANCELLED,
            },
            {
                "source": OrderStatus.PREPARING,
                "event": OrderEvent.SHIP,
                "target": OrderStatus.SHIPPED,
            },
            {
                "source": OrderStatus.SHIPPED,
                "event": OrderEvent.DELIVER,
                "target": OrderStatus.DELIVERED,
            },
            {
                "source": OrderStatus.DELIVERED,
                "event": OrderEvent.RETURN,
                "target": OrderStatus.RETURNED,
            },
        ]
    )
    return machine

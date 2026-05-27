import pytest

from statewire.examples.order import OrderEvent, create_order_machine
from statewire.exceptions import InvalidTransitionException


def test_order_happy_path() -> None:
    om = create_order_machine(order_id="ORD-001")
    assert om.state == "DRAFT"
    om.trigger(OrderEvent.SUBMIT)
    assert om.state == "SUBMITTED"
    om.trigger(OrderEvent.CONFIRM)
    assert om.state == "CONFIRMED"
    om.trigger(OrderEvent.PREPARE)
    assert om.state == "PREPARING"
    om.trigger(OrderEvent.SHIP)
    assert om.state == "SHIPPED"
    om.trigger(OrderEvent.DELIVER)
    assert om.state == "DELIVERED"


def test_order_cancellation_from_submitted() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CANCEL)
    assert om.state == "CANCELLED"


def test_order_cancellation_from_confirmed() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CONFIRM)
    om.trigger(OrderEvent.CANCEL)
    assert om.state == "CANCELLED"


def test_order_return_flow() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CONFIRM)
    om.trigger(OrderEvent.PREPARE)
    om.trigger(OrderEvent.SHIP)
    om.trigger(OrderEvent.DELIVER)
    om.trigger(OrderEvent.RETURN)
    assert om.state == "RETURNED"


def test_order_cannot_cancel_from_preparing() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CONFIRM)
    om.trigger(OrderEvent.PREPARE)
    with pytest.raises(InvalidTransitionException):
        om.trigger(OrderEvent.CANCEL)


def test_order_cannot_ship_before_preparing() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CONFIRM)
    with pytest.raises(InvalidTransitionException):
        om.trigger(OrderEvent.SHIP)


def test_order_cannot_return_before_delivery() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CONFIRM)
    om.trigger(OrderEvent.PREPARE)
    om.trigger(OrderEvent.SHIP)
    with pytest.raises(InvalidTransitionException):
        om.trigger(OrderEvent.RETURN)


def test_order_cannot_submit_twice() -> None:
    om = create_order_machine()
    om.trigger(OrderEvent.SUBMIT)
    with pytest.raises(InvalidTransitionException):
        om.trigger(OrderEvent.SUBMIT)


def test_order_history() -> None:
    om = create_order_machine(order_id="ORD-002")
    om.trigger(OrderEvent.SUBMIT)
    om.trigger(OrderEvent.CONFIRM)
    om.trigger(OrderEvent.PREPARE)
    om.trigger(OrderEvent.SHIP)
    assert om.history is not None
    assert len(om.history) == 4
    assert om.history.records[0].event == "SUBMIT"
    assert om.history.records[1].event == "CONFIRM"
    assert om.history.records[2].event == "PREPARE"
    assert om.history.records[3].event == "SHIP"
    last = om.history.last
    assert last is not None
    assert last.target == "SHIPPED"


def test_order_available_events() -> None:
    om = create_order_machine()
    assert "SUBMIT" in om.available_events()
    om.trigger(OrderEvent.SUBMIT)
    available = om.available_events()
    assert "CONFIRM" in available
    assert "CANCEL" in available
    assert "SUBMIT" not in available

import pytest

from statewire.examples.payment import PaymentEvent, create_payment_machine
from statewire.exceptions import InvalidTransitionException


def test_payment_happy_path() -> None:
    pm = create_payment_machine(payment_id="PAY-001")
    assert pm.state == "CREATED"
    pm.trigger(PaymentEvent.INITIATE)
    assert pm.state == "PENDING"
    pm.trigger(PaymentEvent.CONFIRM)
    assert pm.state == "PROCESSING"
    pm.trigger(PaymentEvent.SETTLE)
    assert pm.state == "COMPLETED"


def test_payment_failure() -> None:
    pm = create_payment_machine()
    pm.trigger(PaymentEvent.INITIATE)
    pm.trigger(PaymentEvent.FAIL)
    assert pm.state == "FAILED"


def test_payment_refund_flow() -> None:
    pm = create_payment_machine()
    pm.trigger(PaymentEvent.INITIATE)
    pm.trigger(PaymentEvent.CONFIRM)
    pm.trigger(PaymentEvent.SETTLE)
    pm.trigger(PaymentEvent.REFUND)
    assert pm.state == "REFUNDING"
    pm.trigger(PaymentEvent.COMPLETE)
    assert pm.state == "REFUNDED"


def test_payment_cannot_refund_before_completion() -> None:
    pm = create_payment_machine()
    pm.trigger(PaymentEvent.INITIATE)
    with pytest.raises(InvalidTransitionException):
        pm.trigger(PaymentEvent.REFUND)


def test_payment_callbacks_fire() -> None:
    completed_log: list[str] = []
    failed_log: list[str] = []
    pm = create_payment_machine(
        payment_id="PAY-002",
        on_completed=lambda **_: completed_log.append("done"),
        on_failed=lambda **_: failed_log.append("fail"),
    )
    pm.trigger(PaymentEvent.INITIATE)
    pm.trigger(PaymentEvent.CONFIRM)
    pm.trigger(PaymentEvent.SETTLE)
    assert completed_log == ["done"]
    assert failed_log == []


def test_payment_failure_callback() -> None:
    failed_log: list[str] = []
    pm = create_payment_machine(
        on_failed=lambda **_: failed_log.append("fail"),
    )
    pm.trigger(PaymentEvent.INITIATE)
    pm.trigger(PaymentEvent.FAIL)
    assert len(failed_log) == 1


def test_payment_history() -> None:
    pm = create_payment_machine(payment_id="PAY-003")
    pm.trigger(PaymentEvent.INITIATE)
    pm.trigger(PaymentEvent.CONFIRM)
    pm.trigger(PaymentEvent.SETTLE)
    assert pm.history is not None
    assert len(pm.history) == 3
    assert pm.history.records[0].event == "INITIATE"
    assert pm.history.records[1].event == "CONFIRM"
    assert pm.history.records[2].event == "SETTLE"
    last = pm.history.last
    assert last is not None
    assert last.target == "COMPLETED"


def test_payment_available_events() -> None:
    pm = create_payment_machine()
    assert "INITIATE" in pm.available_events()
    pm.trigger(PaymentEvent.INITIATE)
    available = pm.available_events()
    assert "CONFIRM" in available
    assert "FAIL" in available
    assert "INITIATE" not in available

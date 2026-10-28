from collections.abc import Callable
from decimal import Decimal

from domain.payments.entities import Payment


def test_equal_requests_have_equal_hash(make_payment: Callable[..., Payment]) -> None:
    from_api = make_payment(amount=Decimal("100"), metadata={"b": 1, "a": {"y": 2, "x": 1}})
    from_db = make_payment(amount=Decimal("100.00"), metadata={"a": {"x": 1, "y": 2}, "b": 1})

    assert from_api.request_hash == from_db.request_hash


def test_different_requests_have_different_hash(make_payment: Callable[..., Payment]) -> None:
    assert make_payment(amount=Decimal("100.00")).request_hash != (
        make_payment(amount=Decimal("5000.00")).request_hash
    )

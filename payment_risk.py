"""Payment event handling with an audit trail for a risk-sensitive decision."""
from dataclasses import dataclass
import traceback
from typing import Any, Callable

from infrai_client import errors


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    account_id: str
    amount_cents: int
    currency: str
    risk_score: int


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str


def decide(event: PaymentEvent) -> Decision:
    if event.risk_score >= 80:
        return Decision("review", "risk score requires manual review")
    return Decision("approve", "risk score below review threshold")


def process_payment(event: PaymentEvent, charge: Callable[[PaymentEvent], Any]) -> Decision:
    decision = decide(event)
    if decision.action == "review":
        return decision
    try:
        charge(event)
    except Exception as exc:
        errors.capture(
            title="payment charge failed",
            message=f"{type(exc).__name__}: {exc}",
            level="error",
            fingerprint=["payment-charge", event.currency],
            exception=traceback.format_exc(),
            context={
                "payment_id": event.payment_id,
                "account_id": event.account_id,
                "amount_cents": event.amount_cents,
                "currency": event.currency,
                "risk_score": event.risk_score,
                "decision": decision.action,
            },
        )
        return Decision("error", "charge failure captured for audit")
    return decision


if __name__ == "__main__":
    event = PaymentEvent("pay_demo_1", "acct_demo", 1250, "USD", 24)
    print(process_payment(event, lambda _: None))

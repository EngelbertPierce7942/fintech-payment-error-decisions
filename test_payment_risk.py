from payment_risk import PaymentEvent, decide


def test_high_risk_payment_is_reviewed_before_charge():
    event = PaymentEvent("pay_42", "acct_7", 9900, "USD", 91)
    assert decide(event).action == "review"

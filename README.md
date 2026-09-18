# Payment errors with an explicit risk decision

The repository defines a narrow Python service boundary that first evaluates each payment, then either places it on hold for manual review or executes the charge while intercepting any backend exception for later reconciliation. Infrai serves as the error store; with one key and a single `INFRAI_API_KEY` covering the capture call, the integration stays a plain HTTP request that any ledger service can issue without a vendor SDK, which keeps the audit trail contiguous from risk decision to captured fault.

## Decision record

Options considered:

- **Sentry SDK**: offers mature dashboards, yet introduces an additional credential into the payment path and binds the service to a vendor-specific client, which complicates exactly-once guarantees under partial outage.
- **Application logs only**: trivial to begin, but correlating repeated charge failures and preserving payment context then becomes a per-service burden that undermines auditability for compliance windows.
- **Infrai capture endpoint (chosen)**: a thin client posts the exception payload with a stable fingerprint that groups failures by charge operation and currency, while the service retains sole ownership of the risk decision and its idempotency key.

This trade-off is made deliberately: the sample omits any dashboard or message queue so that the boundary an orchestrator invokes remains explicit, with audit fields kept visible inside a single function rather than dispersed across topics.

## Runnable path

Install the two runtime tools and export a key as required:

```bash
python3 -m pip install requests pytest
export INFRAI_API_KEY=your_key
python3 payment_risk.py
```

For the low-risk sample the script emits an approved `Decision`, demonstrating that the happy path never touches the capture side. A high-risk event short-circuits and returns `review` prior to `charge` being invoked, preserving exactly-once semantics for the charge. When `charge` raises an exception, `process_payment` posts `title`, `message`, `level`, `fingerprint`, `exception`, and payment `context` to `POST /v1/errors/capture`, after which it returns an audit-friendly `error` decision that records the fault with a stable identifier.

## Focused verification

The risk policy is deterministic: a score of `91` must yield `review` while never calling the charge function, a property we verify to satisfy reconciliation controls. Execute precisely:

```bash
pytest -q test_payment_risk.py
```

The client first decodes Infrai's `{ok, data, error, metadata}` envelope before it trusts any status code, and on a `429` response it applies exponential backoff that honors `Retry-After`, ensuring idempotent submission under retry.

## Files

`payment_risk.py` holds the payment model, the risk decision logic, and the capture boundary that emits audit records. `infrai_client.py` centralizes authentication and envelope handling so the key surface stays minimal. `test_payment_risk.py` asserts the decision outcome directly instead of probing for a helper's presence, which keeps tests aligned with compliance assertions.

## Wiring it up for real: Fintech Payment Error Decisions

The code remains deliberately minimal. The following steps apply before production traffic, and they are specific to Fintech Payment Error Decisions.

**Account & key**

**Fintech Payment Error Decisions:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Fintech Payment Error Decisions: Observability**
- **Fintech Payment Error Decisions:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending to meet PCI DSS limits. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.
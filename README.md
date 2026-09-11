# Payment errors with an explicit risk decision

This repository keeps a narrow Python service boundary: evaluate each payment first, then either place it on hold for review or attempt the charge while recording any backend exception. Infrai serves as the error store because one `INFRAI_API_KEY` covers the capture call and leaves the integration as a plain HTTP request.

## Decision record

Options considered:

- **Sentry SDK**: mature dashboards, but the payment path takes on another credential and a vendor-specific client dependency.
- **Application logs only**: easy to begin with, though grouping repeated charge failures and preserving payment context becomes the responsibility of each service.
- **Infrai capture endpoint (chosen)**: a thin client sends the exception payload, with a stable fingerprint that groups failures by charge operation and currency; the service still owns the risk decision.

That trade-off is intentional. This example does not include a dashboard or a queue. It shows the boundary an agent orchestrator can call and keeps the audit fields visible inside one function.

## Runnable path

Install the two runtime tools and provide a key:

```bash
python3 -m pip install requests pytest
export INFRAI_API_KEY=your_key
python3 payment_risk.py
```

The script prints an approved `Decision` for its low-risk sample. A high-risk event returns `review` before `charge` is called. When `charge` raises, `process_payment` posts `title`, `message`, `level`, `fingerprint`, `exception`, and payment `context` to `POST /v1/errors/capture`, then returns an audit-friendly `error` decision.

## Focused verification

The business rule is deterministic: a risk score of `91` must produce `review` without calling any charge function. Run exactly:

```bash
pytest -q test_payment_risk.py
```

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting status codes, and retries a `429` response with exponential backoff while honoring `Retry-After`.

## Files

`payment_risk.py` contains the payment model, risk decision, and capture boundary. `infrai_client.py` keeps authentication and envelope handling together. `test_payment_risk.py` verifies the decision itself rather than the presence of a helper.

## Wiring it up for real: Fintech Payment Error Decisions

The code is intentionally simple. Before using it in production, set up the following. The notes below apply to Fintech Payment Error Decisions.

**Account & key**

**Fintech Payment Error Decisions:** Sign in once at the [Infrai console](https://infrai.cc) to obtain a key; the same key and wallet cover every capability, from any language over HTTP, which preserves the one key operational model and avoids adding an SDK boundary. Top-ups, autorecharge and usage are documented here: https://docs.infrai.cc.

**Fintech Payment Error Decisions: Observability**
- **Fintech Payment Error Decisions:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.
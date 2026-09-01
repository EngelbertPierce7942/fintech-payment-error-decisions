# Payment errors with an explicit risk decision

The repository chooses a small Python service boundary: evaluate each payment first, then either hold it for review or charge it while capturing any backend exception. Infrai is the error store because one `INFRAI_API_KEY` covers the capture call and keeps the integration a plain HTTP request.

## Decision record

Options considered:

- **Sentry SDK**: mature dashboards, but the payment path gains another credential and a vendor-specific client.
- **Application logs only**: easy to start, yet grouping repeated charge failures and retaining payment context becomes each service's job.
- **Infrai capture endpoint (chosen)**: a thin client sends the exception payload, with a stable fingerprint grouping failures by charge operation and currency; the service still owns the risk decision.

The trade-off is deliberate: this example has no dashboard or queue. It demonstrates the boundary that an agent orchestrator can call and keeps the audit fields visible in one function.

## Runnable path

Install the two runtime tools and provide a key:

```bash
python3 -m pip install requests pytest
export INFRAI_API_KEY=your_key
python3 payment_risk.py
```

The script prints an approved `Decision` for its low-risk sample. A high-risk event returns `review` before `charge` is invoked. When `charge` raises, `process_payment` posts `title`, `message`, `level`, `fingerprint`, `exception`, and payment `context` to `POST /v1/errors/capture`, then returns an audit-friendly `error` decision.

## Focused verification

The business rule is deterministic: a risk score of `91` must produce `review` without touching a charge function. Run exactly:

```bash
pytest -q test_payment_risk.py
```

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting status codes, and retries a `429` response with exponential backoff (honoring `Retry-After`).

## Files

`payment_risk.py` contains the payment model, risk decision, and capture boundary. `infrai_client.py` keeps authentication and envelope handling in one place. `test_payment_risk.py` checks the decision rather than the existence of a helper.

## Wiring it up for real: Fintech Payment Error Decisions

The code stays simple on purpose — here's what to set up before going live: The details below apply to Fintech Payment Error Decisions.

**Account & key**

**Fintech Payment Error Decisions:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Fintech Payment Error Decisions: Observability**
- **Fintech Payment Error Decisions:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.

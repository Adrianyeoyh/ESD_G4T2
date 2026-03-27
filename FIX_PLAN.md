# Fix Plan - Make Payment Orchestrator & Connected Services

**Date:** 2026-03-27
**Branch:** feature/make-payment-orchestrator
**Scope:** make_payment orchestrator, payment_service, invoice_service, notification_service, shared module
**Verified against:** actual file contents as of 2026-03-27 (all line numbers confirmed by reading source)

---

## Resolved Issues (C1-C6)

These have already been fixed and are documented here for reference only.

| ID | Service | Issue | Resolution |
|----|---------|-------|------------|
| C1 | Orchestrator | Missing `DATABASE_URL` in settings; `db.py` would crash on import | Removed `db.py` (orchestrator has no DB) |
| C2 | Orchestrator | Broken import in `boilerplate_repository.py` referencing non-existent module | Deleted; replaced with `make_payment_repository.py` |
| C3 | Orchestrator | Boilerplate file naming throughout (`boilerplate_controller.py`, etc.) | Renamed to `make_payment_controller.py`, `make_payment_service.py`, `make_payment_routes.py` |
| C4 | Payment | `webhook_service.py` imported `make_payment_client` which didn't exist as a file | `make_payment_client.py` now exists at `app/clients/make_payment_client.py` |
| C5 | Payment | Missing `requirements/payment.txt`; Docker build would fail | Requirements file created |
| C6 | Notification | Dead code in `settings.py` — `RABBITMQ_HOST` if/else was overwritten by `os.getenv()` on the next line | Removed the redundant `os.getenv()` overwrite line |
| CR-1 | Orchestrator | `InvoiceStatus` enum import crashes startup | Created `app/clients/` with dedicated client modules; use plain strings |
| CR-2 | Orchestrator | Absolute imports fail in Docker | Changed to relative imports |
| CR-3 | Orchestrator | No webhook authentication on `/payment-events` | Added `X-Internal-Api-Key` header validation |
| CR-4 | Notification | Infinite requeue loop on consumer errors | Split retryable vs non-retryable error handling |
| CR-5 | Notification | Twilio credentials not validated at startup | Added `__init__` validation with `ValueError` |
| CR-6 | Invoice | No transaction rollback on commit failure | Added `_commit_and_refresh` helper with rollback |
| M-2 | Orchestrator | `_close_record` bypasses `_request` helper | Resolved via CR-1 client refactor |
| M-7 | Invoice | `float` used for money | Changed to `Decimal` in service and repository |
| M-12 | Orchestrator | `UNPAID` vs `DRAFT` mismatch | Resolved via CR-1 — uses `"draft"` string |
| H-1 | Orchestrator | `debug=True` hardcoded | Changed to `debug=False` |
| H-5 | Payment | `client_secret` exposed on all GET endpoints | Created `PaymentReadResponse` without `client_secret` for GET/cancel routes |
| H-7 | Payment | No amount validation (zero/negative) | Added `Field(gt=0)` to `PaymentIntentCreate.amount` |
| H-8 | Invoice | Missing state machine enforcement | Added `ALLOWED_TRANSITIONS` map and `_transition` helper; guarded `update_total` |

---

## Remaining Issues

### CRITICAL

#### CR-1: Orchestrator imports `InvoiceStatus` enum it should not own — crashes at startup
- **File:** `composites/make_payment/common/tools.py` — file is **completely empty** (0 bytes)
- **File:** `composites/make_payment/app/services/make_payment_service.py:10` — `from common.tools import InvoiceStatus`
- **Problem:** The orchestrator is a composite service that coordinates via HTTP — it should **not** own or import domain models/enums from atomic services. `InvoiceStatus` belongs to the invoice service. The orchestrator's `common/tools.py` is empty, so this crashes with `ImportError` on startup — **the entire orchestrator is non-functional**.
- **Fix (architectural):**
  1. **Remove** `from common.tools import InvoiceStatus` from `make_payment_service.py`
  2. **Use plain strings** for status comparisons (e.g., `"paid"`, `"payment_pending"`, `"draft"`, `"failed"`) since the orchestrator only compares against JSON string values returned by the invoice service API
  3. **Create `app/clients/` directory** with dedicated client modules that encapsulate all HTTP calls to external microservices:
     - `app/clients/invoice_client.py` — wraps `_get_invoice`, `_mark_invoice_payment_pending`, `_mark_invoice_paid`, `_mark_invoice_failed` (currently inline in `make_payment_service.py:138-166`)
     - `app/clients/payment_client.py` — wraps `_create_payment_attempt`, `_cancel_payment` (currently inline in `make_payment_service.py:168-190`)
     - `app/clients/records_client.py` — wraps `_close_record` (currently inline in `make_payment_service.py:192-212`)
     - `app/clients/notification_client.py` — wraps `_publish_success_notification` RabbitMQ publish (currently inline in `make_payment_service.py:214-240`)
  4. **Fix `InvoiceStatus.UNPAID`** reference on line 125 — the invoice service uses `DRAFT`, not `UNPAID`. Change to the correct string `"draft"`.
  5. **Delete** `common/tools.py` (or leave empty) — orchestrator has no domain enums of its own

#### CR-2: Orchestrator absolute imports will fail in Docker
- **File:** `composites/make_payment/app/__init__.py:2-3` — `from backend.composites.make_payment.app.controllers...`
- **File:** `composites/make_payment/app/routes/make_payment_routes.py:3` — `from backend.composites.make_payment.app.controllers...`
- **File:** `composites/make_payment/app/controllers/make_payment_controller.py:3` — `from backend.composites.make_payment.app.services...`
- **Problem:** Uses fully-qualified `backend.composites.make_payment.app...` paths. These only resolve if the repo root is on `sys.path`. In Docker (where workdir is the service root), these fail with `ModuleNotFoundError`.
- **Fix:** Change to relative imports (e.g., `from app.controllers.make_payment_controller import ...`) matching the pattern used by payment_service and invoice_service.

#### CR-3: No webhook authentication on `/make_payment/payment-events`
- **File:** `composites/make_payment/app/controllers/make_payment_controller.py:37-40`
- **Problem:** `handle_payment_event()` accepts any POST with no authentication — no API key, no bearer token, no HMAC. Anyone who discovers this endpoint can POST `{"eventType": "payment.succeeded", "invoiceId": 1}` to mark invoices as PAID, trigger record closures, and send SMS notifications.
- **Fix:** Add a shared secret (e.g., `X-Internal-Api-Key` header) validated via `hmac.compare_digest`. Add the same secret to payment_service's `make_payment_client.py` to send in requests.

#### CR-4: Infinite requeue loop in notification consumer
- **File:** `services/notification_service/app/services/consumer_service.py:50-54`
- **Problem:** The callback has a single blanket `except Exception` that nacks with `requeue=True`. If a message has bad JSON, missing keys, or an invalid phone number, it will be redelivered and fail identically — forever. This creates an infinite loop that saturates the consumer, floods logs, and prevents processing of valid messages behind it.
- **Fix:** Split error handling: (a) Non-retryable errors (`json.JSONDecodeError`, `KeyError`, `ValueError`) should `basic_ack` and drop the message (poison pill). (b) Retryable errors (Twilio network timeout) should use a retry counter via message headers with a max retry limit, then ack and drop.

#### CR-5: Twilio credentials not validated at startup
- **File:** `services/notification_service/app/services/twilio_service.py:9-10`
- **Problem:** If `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, or `TWILIO_PHONE_NUMBER` are `None` (env vars not set), `Client(None, None)` is created without error. The first `send_sms` call then fails, triggering the consumer's blanket except → `requeue=True` → infinite requeue loop (CR-4).
- **Fix:** Validate all three credentials in `TwilioService.__init__` and raise `ValueError` immediately if any are missing. This makes misconfiguration fail at startup rather than at first message.

#### CR-6: No transaction rollback in invoice_service
- **File:** `services/invoice_service/app/services/invoice_service.py` — all mutating methods (lines 18-19, 46-47, 53-55, 61-63, 69-71, 77-79, 88-89)
- **Problem:** Every method calls `self.db.commit()` with no try/except. If `commit()` raises `SQLAlchemyError`, the session is left in a dirty state. `SQLAlchemyError` is imported on line 2 but never used — clearly intended for error handling that was never implemented.
- **Fix:** Wrap commit/refresh in try/except with `self.db.rollback()`. Consider a decorator or context manager for DRY handling.

---

### HIGH

#### H-1: `debug=True` hardcoded in orchestrator
- **File:** `composites/make_payment/run.py:6`
- **Problem:** `app.run(host="0.0.0.0", port=5005, debug=True)` — exposes Werkzeug interactive debugger in production (effectively RCE). `APP_ENV` exists in settings but is not checked here.
- **Fix:** `app.run(host="0.0.0.0", port=5005, debug=(settings.APP_ENV != "docker"))` or use gunicorn in Dockerfile CMD.

#### H-2: Hardcoded notification phone number
- **File:** `composites/make_payment/app/config/settings.py:21`
- **Problem:** `NOTIFICATION_PHONE_NUMBER` defaults to `+6588888888`. All payment notifications go to this static number rather than the patient/user associated with the record.
- **Fix:** Retrieve recipient phone from the record/patient context. At minimum, remove the hardcoded default so a missing env var fails loudly.

#### H-3: RabbitMQ connection opened/closed per message in orchestrator
- **File:** `composites/make_payment/app/services/make_payment_service.py:223-240`
- **Problem:** `_publish_success_notification` creates a new TCP connection to RabbitMQ, publishes one message, and closes. No error handling — if connection or publish fails, the exception propagates up and the entire `handle_payment_event` call fails, even though the invoice is already PAID (line 103) and record already closed (line 105).
- **Fix:** (a) Use a persistent connection or connection pool. (b) Wrap publish in try/except with logging so notification failure doesn't block payment acknowledgment (see also M-3).

#### H-4: Wrong `paid_at` timestamp in payment webhook handler
- **File:** `services/payment_service/app/services/webhook_service.py:46`
- **Problem:** `datetime.fromtimestamp(intent.get("created", 0), tz=timezone.utc)` — `intent["created"]` is the PaymentIntent **creation** time, not the time the payment actually succeeded. If there's a delay (user takes 10 minutes to confirm), the recorded `paid_at` is wrong.
- **Fix:** Use `datetime.now(timezone.utc)` (when webhook fires is when payment succeeded) or remove the `paid_at` parameter and let `mark_succeeded` use its default.

#### H-5: `client_secret` exposed on all GET endpoints
- **File:** `services/payment_service/app/routers/payment_router.py:43-55`
- **File:** `services/payment_service/app/schemas/payment_schema.py:24`
- **Problem:** `PaymentResponse` includes `client_secret` and is used on all endpoints (GET by ID, list by invoice, get latest). The client_secret should only be returned on the initial POST create response. Leaking it on GET endpoints allows anyone with API read access to confirm pending payments.
- **Fix:** Create a separate `PaymentReadResponse` schema without `client_secret` for GET endpoints.

#### H-6: Non-atomic webhook flow in payment_service
- **File:** `services/payment_service/app/services/webhook_service.py:41-61`
- **Problem:** In `_handle_succeeded`: `svc.mark_succeeded()` (line 47) calls `self.db.commit()` internally (payment_service.py:102), then `make_payment_client.notify_payment_succeeded()` (line 48) is called. If notification fails, the DB is already committed as SUCCEEDED but the orchestrator never learns. The `db.rollback()` on line 58 has nothing to roll back.
- **Fix:** Move `db.commit()` out of the individual `mark_*` methods in `PaymentService` and let the webhook handler commit after both DB update and notification succeed. Or implement an outbox pattern.

#### H-7: No amount validation (zero/negative)
- **File:** `services/payment_service/app/schemas/payment_schema.py:11`
- **Problem:** `amount: Decimal` has no constraint. Zero or negative amounts pass through to Stripe, which returns an unhelpful error.
- **Fix:** `amount: Decimal = Field(gt=0)`

#### H-8: Missing state machine enforcement in invoice_service
- **File:** `services/invoice_service/app/services/invoice_service.py`
- **Problem:**
  - `mark_paid` (line 50): **no guard at all** — CANCELLED, DRAFT, or FAILED invoices can be marked PAID
  - `mark_failed` (line 58): **no guard** — PAID invoices can be marked FAILED
  - `mark_cancelled` (line 66): **no guard** — PAID invoices can be cancelled
  - `mark_payment_pending` (line 38): only checks `== PAID`, still allows CANCELLED → PAYMENT_PENDING
  - `update_total` (line 74): **no guard** — PAID invoices can have total changed
- **Fix:** Define allowed transitions and validate in each method.

#### H-9: No pagination on invoice `list_all`
- **File:** `services/invoice_service/app/repositories/invoice_repository.py:26-31`
- **Problem:** `list_all()` returns every invoice in the database with `.all()`, no limit. Memory/performance issue as data grows.
- **Fix:** Add `skip`/`limit` parameters and expose as query params on the router.

#### H-10: No payload validation in notification consumer
- **File:** `services/notification_service/app/services/consumer_service.py:37-38`
- **Problem:** Directly accesses `payload["phoneNumber"]` and `payload["message"]` with dict key access. Missing keys raise `KeyError`, which is caught by the blanket `except Exception` on line 50 and **requeued forever** (part of CR-4). No phone number format validation — malformed numbers get sent to Twilio (billable API calls that fail).
- **Fix:** Use `.get()` with explicit checks, validate phone format, and handle validation errors as non-retryable (ack and drop).

#### H-11: No RabbitMQ connection recovery in notification consumer
- **File:** `services/notification_service/app/services/consumer_service.py:24`
- **Problem:** `pika.BlockingConnection` does not auto-recover. If RabbitMQ restarts or network drops, the consumer dies permanently and must be restarted externally. The heartbeat (line 22) detects dead connections but there's no reconnect logic.
- **Fix:** Wrap the connection + `start_consuming()` in a retry loop with exponential backoff, or switch to `pika.SelectConnection` with built-in recovery.

---

### MEDIUM

#### M-1: `ExternalResponseError` doesn't inherit from `AppError`
- **File:** `composites/make_payment/app/services/make_payment_service.py:24-27`
- **Problem:** It's a `@dataclass` extending `Exception` directly. Has its own handler in the controller (line 59), so it works, but any code catching `AppError` expecting all app exceptions will miss this.
- **Fix:** Either inherit from `AppError` or document the design choice.

#### M-2: `_close_record` bypasses `_request` helper
- **File:** `composites/make_payment/app/services/make_payment_service.py:192-212`
- **Problem:** Uses `requests.post()` directly instead of `self._request()`. Different error handling (raises `OrchestrationError` directly vs the structured pattern in `_request`). The 409-as-success logic is the reason, but `_request` could be extended.
- **Fix:** Resolved as part of CR-1 refactor — `records_client.py` will encapsulate this with proper error handling and 409-as-success logic.

#### M-3: Notification failure blocks webhook handler
- **File:** `composites/make_payment/app/services/make_payment_service.py:106`
- **Problem:** In the `payment.succeeded` handler: invoice is marked PAID (line 103), record is closed (line 105), then `_publish_success_notification` (line 106) can throw if RabbitMQ is down. The unhandled exception propagates, returning 500 to the caller. The payment_service retries the webhook, which re-runs all three steps (idempotent for PAID and record close, but wasteful).
- **Fix:** Wrap `_publish_success_notification` in try/except with logging. Notification is best-effort and should not block payment acknowledgment.

#### M-4: `Decimal` to `int` truncation in Stripe service
- **File:** `services/payment_service/app/services/stripe_service.py:25`
- **Problem:** `int(amount * 100)` truncates toward zero. `Decimal("10.999") * 100` = `Decimal("1099.900")` → `int()` gives `1099`, not `1100`. For financial calculations this silent truncation is incorrect.
- **Fix:** Use `int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))` or quantize the amount to 2 decimal places before multiplying.

#### M-5: No idempotency check in payment webhook handlers
- **File:** `services/payment_service/app/services/webhook_service.py:41-61, 64-90, 93-110`
- **Problem:** Stripe may send the same webhook event multiple times. The handlers don't check if the payment is already in the target status. A payment already SUCCEEDED will get `paid_at` overwritten and the orchestrator will be notified again (duplicate SMS, duplicate record close attempt).
- **Fix:** At the start of each handler, check current status: if already in target status, return early without re-notifying.

#### M-6: Advisory lock key collision risk
- **File:** `services/payment_service/app/repositories/payment_repository.py:73-75`
- **Problem:** `pg_advisory_xact_lock(invoice_id)` uses raw `invoice_id` as the lock key. Any other service or code using advisory locks with the same integer values will collide.
- **Fix:** Use two-key variant: `pg_advisory_xact_lock(classid, objid)` with a service-specific classid constant.

#### M-7: `float` used for money in invoice_service
- **File:** `services/invoice_service/app/services/invoice_service.py:13` — `total: float`
- **File:** `services/invoice_service/app/services/invoice_service.py:74` — `new_total: float`
- **File:** `services/invoice_service/app/repositories/invoice_repository.py:7` — `total: float`
- **Problem:** Service/repository accept `float` but the model column is `Numeric(10,2)`. Float introduces precision errors for financial values (e.g., `0.1 + 0.2 != 0.3`).
- **Fix:** Change type hints to `Decimal` in service and repository layers.

#### M-8: Schema search_path hardcoded in both invoice and payment `db.py`
- **File:** `services/invoice_service/app/config/db.py:7` — hardcodes `"invoice_schema"`
- **File:** `services/payment_service/app/config/db.py:7` — hardcodes `"payment_schema"`
- **Problem:** Both `connect_args` hardcode the schema name instead of using the `DB_SCHEMA` setting from their respective `settings.py`. If someone changes the env var, the model's `__table_args__` schema and the connection search path diverge → table-not-found errors.
- **Fix:** Use the setting: `connect_args={"options": f"-csearch_path={DB_SCHEMA}"}`

#### M-9: Generic catch-all leaks internal error details in payment_router
- **File:** `services/payment_service/app/routers/payment_router.py:39-40`
- **Problem:** `detail=f"Payment intent failed: {exc}"` includes `str(exc)` which may contain internal paths, DB connection strings, or Stripe error internals.
- **Fix:** Return a generic message to the caller; log the actual error server-side.

#### M-10: `print()` used instead of `logging` in notification_service
- **File:** `services/notification_service/app/services/consumer_service.py:45,51,61`
- **Problem:** All output uses `print()`. In Docker, structured logging with Python's `logging` module is needed for proper log levels, timestamps, and log aggregation.
- **Fix:** Replace with `logging.getLogger(__name__)` and use `logger.info`, `logger.error` etc.

#### M-11: Shared module is entirely empty stubs
- **Files:** All files in `backend/shared/` (`amqp/consumer.py`, `amqp/publisher.py`, `http/client.py`, `utils/tools.py`, `utils/response.py`, `config/settings.py`) are empty or contain only a placeholder comment.
- **Problem:** The notification service re-implements its own RabbitMQ connection; the orchestrator does the same. The shared module serves no purpose.
- **Fix:** Either implement shared AMQP/HTTP utilities and refactor services to use them, or remove the shared module to avoid confusion.

#### M-12: `InvoiceStatus.UNPAID` referenced in orchestrator but invoice_service uses `DRAFT`
- **File:** `composites/make_payment/app/services/make_payment_service.py:125`
- **File:** `services/invoice_service/common/tools.py:4-9`
- **Problem:** The orchestrator references `InvoiceStatus.UNPAID` as a payable state, but the invoice service defines `DRAFT` (not `UNPAID`). Invoices in `draft` status will never be payable through the orchestrator.
- **Fix:** Resolved as part of CR-1 — when switching to plain strings, use `"draft"` to match the invoice service's actual enum value.

---

### LOW

#### L-1: No health check endpoints
- **Services:** Orchestrator, invoice_service, payment_service
- **Problem:** No `/health` or `/ready` endpoint for Docker/K8s liveness/readiness probes.
- **Fix:** Add a simple health route returning 200 to each service.

#### L-2: No health check mechanism for notification_service
- **Problem:** Pure consumer with no HTTP endpoint. No way for Docker/K8s to determine if it's healthy.
- **Fix:** Expose a simple HTTP health endpoint on a separate port, or use a Docker healthcheck command that checks the process.

#### L-3: No request logging or correlation IDs in orchestrator
- **Problem:** Orchestrator coordinates 4 services with no trace/correlation ID propagation. Debugging distributed payment flows in production will be very difficult.
- **Fix:** Generate a correlation ID per request, pass in headers to downstream services, include in log output.

#### L-4: No graceful shutdown in notification consumer
- **File:** `services/notification_service/app/services/consumer_service.py:56-62`
- **Problem:** No SIGTERM/SIGINT handler. Container shutdown abruptly terminates the RabbitMQ connection, potentially losing the in-flight message.
- **Fix:** Add signal handlers to call `channel.stop_consuming()` and `connection.close()`.

#### L-5: `pytest`/`pytest-mock` in production requirements
- **File:** `backend/requirements/base.txt`
- **Problem:** Test dependencies installed in production Docker images. Increases image size and attack surface.
- **Fix:** Move to a separate `dev.txt` or `test.txt` requirements file.

#### L-6: Unused `STRIPE_PUBLISHABLE_KEY` in payment_service config
- **File:** `services/payment_service/app/config/settings.py:22`
- **Problem:** Loaded from env but never referenced anywhere in the codebase.
- **Fix:** Remove, or document why it exists.

#### L-7: No logging in invoice_service
- **Problem:** Zero logging statements in the entire service. Status transitions, errors, and creation events are all silent.
- **Fix:** Add `logging.getLogger(__name__)` and log key operations.

#### L-8: No logging in payment_service business logic
- **File:** `services/payment_service/app/services/payment_service.py`
- **Problem:** The main service has no logging. Failed invoice fetches, Stripe failures, and state transitions are silent (webhook_service.py has logging, but payment_service.py does not).
- **Fix:** Add logger and log key operations.

#### L-9: Custom `ValidationError` shadows Pydantic's
- **File:** `services/invoice_service/utils/exceptions.py:13`, `services/payment_service/utils/exceptions.py`
- **Problem:** Same class name as `pydantic.ValidationError`. Can cause import confusion.
- **Fix:** Rename to `AppValidationError` or namespace carefully.

#### L-10: Unused custom exceptions in notification_service
- **File:** `services/notification_service/utils/exceptions.py`
- **Problem:** `AppError`, `NotFoundError`, `ValidationError`, `ConflictError` defined with HTTP status codes but never imported or used. HTTP codes are irrelevant for a queue consumer.
- **Fix:** Remove or replace with message-queue-appropriate error types.

#### L-11: Commented-out code in invoice settings
- **File:** `services/invoice_service/app/config/settings.py:10`
- **Problem:** `# DB_HOST = "host.docker.internal"` — dead commented-out code with wrong indentation inside the if-block.
- **Fix:** Remove.

#### L-12: DB credentials can be `None` in invoice_service
- **File:** `services/invoice_service/app/config/settings.py:14-17`
- **Problem:** `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` use `os.getenv()` with no defaults. If any are unset, `DATABASE_URL` becomes `postgresql://None:None@localhost:None/None` — a confusing connection error rather than a clear startup failure.
- **Fix:** Validate required env vars at import time and raise with the missing var name, or provide dev defaults.

---

## Suggested Fix Priority

**Batch 1 — Blockers (service literally won't start/run):**
- CR-1 (empty `common/tools.py` → ImportError on startup)
- CR-2 (absolute imports → ModuleNotFoundError in Docker)
- M-12 (UNPAID vs DRAFT mismatch — must fix with CR-1)
- H-1 (debug=True — RCE in production)

**Batch 2 — Security & data integrity:**
- CR-3 (webhook auth)
- CR-4 (infinite requeue loop)
- CR-5 (Twilio credential validation — prevents CR-4 from triggering)
- CR-6 (invoice rollback)\
- H-5 (client_secret exposure)
- H-7 (amount validation)
- H-8 (state machine)

**Batch 3 — Correctness:**
- H-4 (wrong paid_at timestamp)
- H-6 (non-atomic webhook)
- M-3 (notification failure blocks webhook)
- M-4 (Decimal truncation)
- M-5 (webhook idempotency)

**Batch 4 — Reliability:**
- H-3 (RabbitMQ connection pooling)
- H-10 (consumer payload validation)
- H-11 (RabbitMQ connection recovery)
- L-4 (graceful shutdown)

**Batch 5 — Observability & cleanup:**
- L-1/L-2 (health checks)
- L-3 (correlation IDs)
- L-7/L-8/M-10 (logging everywhere)
- M-8 (hardcoded search_path)
- M-11 (shared module)
- Remaining LOW items

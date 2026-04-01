import argparse
import json
import sys
import time
import urllib.error
import urllib.request


class TestFailure(Exception):
    pass


class StepResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.details: list[str] = []

    def ok(self, message: str):
        self.details.append(f"[PASS] {message}")

    def fail(self, message: str):
        self.passed = False
        self.details.append(f"[FAIL] {message}")

    def info(self, message: str):
        self.details.append(f"[INFO] {message}")


def request_json(method: str, url: str, body=None, timeout: int = 15):
    data = None
    headers = {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if raw:
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, {"raw": raw}
            return resp.status, None
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return error.code, parsed


def wait_for_endpoint(url: str, timeout_seconds: int = 60):
    print(f"[WAIT] {url}")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            code, _ = request_json("GET", url, timeout=5)
            if code < 500:
                print(f"[PASS] Reachable: {url}")
                return True
        except Exception:
            pass
        time.sleep(2)
    print(f"[FAIL] Timed out waiting for {url}")
    return False


def expect_equal(step: StepResult, label: str, actual, expected):
    if actual == expected:
        step.ok(f"{label}: {actual}")
        return
    step.fail(f"{label}: expected {expected}, got {actual}")
    raise TestFailure(label)


def expect_in(step: StepResult, label: str, actual, expected_values):
    if actual in expected_values:
        step.ok(f"{label}: {actual}")
        return
    step.fail(f"{label}: expected one of {expected_values}, got {actual}")
    raise TestFailure(label)


def run_step(name: str, fn, summary: dict):
    print(f"\n[STEP] {name}")
    step = StepResult(name)
    try:
        fn(step)
        summary["passed"] += 1
    except Exception as error:
        if not step.details:
            step.fail(f"Unhandled error: {error}")
        summary["failed"] += 1
        print(f"[FAIL] {name}: {error}")
    finally:
        for line in step.details:
            print(f"  {line}")
        summary["steps"].append(step)


def main():
    parser = argparse.ArgumentParser(
        description="Smoke-test all API endpoints across drug, invoice, and payment services."
    )
    parser.add_argument("--drug-base-url", default="http://localhost:5081")
    parser.add_argument("--invoice-base-url", default="http://localhost:5003")
    parser.add_argument("--payment-base-url", default="http://localhost:5004")
    parser.add_argument(
        "--skip-payment",
        action="store_true",
        help="Skip payment service checks even if a payment base URL is provided.",
    )
    parser.add_argument(
        "--require-stripe",
        action="store_true",
        help="Fail if Stripe-dependent payment intent flow cannot run.",
    )
    args = parser.parse_args()

    drug_base = args.drug_base_url.rstrip("/")
    invoice_base = args.invoice_base_url.rstrip("/")
    payment_base = args.payment_base_url.rstrip("/")

    # Use framework-level endpoints for readiness checks so startup probing
    # does not depend on business-route behavior or seed data.
    summary = {"passed": 0, "failed": 0, "steps": []}

    drug_ready = wait_for_endpoint(f"{drug_base}/openapi.json")
    invoice_ready = wait_for_endpoint(f"{invoice_base}/openapi.json")
    payment_ready = True if args.skip_payment else wait_for_endpoint(f"{payment_base}/openapi.json")

    if not drug_ready:
        summary["failed"] += 1
        print("[FAIL] Drug service is not reachable. Start it and retry.")
    if not invoice_ready:
        summary["failed"] += 1
        print("[FAIL] Invoice service is not reachable. Start it and retry.")
    if not payment_ready and not args.skip_payment:
        summary["failed"] += 1
        print("[FAIL] Payment service is not reachable. Start it and retry.")
        print("[INFO] If you intentionally do not want to test payment now, run with --skip-payment.")

    now_tag = int(time.time())
    created_drug_id = None
    created_invoice_id = None
    paid_invoice_id = None
    created_payment_id = None

    def test_drug_crud(step: StepResult):
        nonlocal created_drug_id
        create_body = {
            "drugName": f"smoke-drug-{now_tag}",
            "quantity": 10,
            "price": "12.34",
        }
        status, payload = request_json("POST", f"{drug_base}/drug", create_body)
        expect_equal(step, "POST /drug status", status, 201)
        created_drug_id = payload["drugId"]
        step.info(f"created drugId={created_drug_id}")

        status, payload = request_json("GET", f"{drug_base}/drug")
        expect_equal(step, "GET /drug status", status, 200)
        expect_equal(step, "GET /drug returns list", isinstance(payload, list), True)

        status, payload = request_json(
            "PUT", f"{drug_base}/drug/{created_drug_id}", {"quantity": 15}
        )
        expect_equal(step, "PUT /drug/{id} status", status, 200)
        expect_equal(step, "PUT /drug/{id} quantity", payload["quantity"], 15)

        status, payload = request_json("DELETE", f"{drug_base}/drug/{created_drug_id}")
        expect_equal(step, "DELETE /drug/{id} status", status, 204)
        expect_equal(step, "DELETE /drug/{id} payload", payload, None)
        created_drug_id = None

    def test_invoice_endpoints(step: StepResult):
        nonlocal created_invoice_id, paid_invoice_id
        record_a = now_tag
        record_b = now_tag + 1

        status, payload = request_json(
            "POST", f"{invoice_base}/invoice", {"recordId": record_a, "total": "100.00"}
        )
        expect_equal(step, "POST /invoice (A) status", status, 201)
        created_invoice_id = payload["invoiceId"]
        expect_equal(step, "POST /invoice (A) status field", payload["status"], "draft")

        status, payload = request_json(
            "POST", f"{invoice_base}/invoice", {"recordId": record_b, "total": "80.00"}
        )
        expect_equal(step, "POST /invoice (B) status", status, 201)
        paid_invoice_id = payload["invoiceId"]

        status, payload = request_json("GET", f"{invoice_base}/invoice")
        expect_equal(step, "GET /invoice status", status, 200)
        expect_equal(step, "GET /invoice returns list", isinstance(payload, list), True)

        status, payload = request_json("GET", f"{invoice_base}/invoice/{created_invoice_id}")
        expect_equal(step, "GET /invoice/{id} status", status, 200)
        expect_equal(step, "GET /invoice/{id} invoiceId", payload["invoiceId"], created_invoice_id)

        status, payload = request_json("GET", f"{invoice_base}/invoice/record/{record_a}")
        expect_equal(step, "GET /invoice/record/{recordId} status", status, 200)
        expect_equal(step, "GET /invoice/record/{recordId} recordId", payload["recordId"], record_a)

        status, payload = request_json(
            "PUT", f"{invoice_base}/invoice/{created_invoice_id}/total", {"total": "150.00"}
        )
        expect_equal(step, "PUT /invoice/{id}/total status", status, 200)
        expect_equal(step, "PUT /invoice/{id}/total total", payload["total"], "150.00")

        status, payload = request_json(
            "PUT", f"{invoice_base}/invoice/{created_invoice_id}/payment-pending"
        )
        expect_equal(step, "PUT /invoice/{id}/payment-pending status", status, 200)
        expect_equal(step, "status after payment-pending", payload["status"], "payment_pending")

        status, payload = request_json("PUT", f"{invoice_base}/invoice/{created_invoice_id}/failed")
        expect_equal(step, "PUT /invoice/{id}/failed status", status, 200)
        expect_equal(step, "status after failed", payload["status"], "failed")

        status, payload = request_json("PUT", f"{invoice_base}/invoice/{created_invoice_id}/cancelled")
        expect_equal(step, "PUT /invoice/{id}/cancelled status", status, 200)
        expect_equal(step, "status after cancelled", payload["status"], "cancelled")

        status, payload = request_json("DELETE", f"{invoice_base}/invoice/{created_invoice_id}")
        expect_equal(step, "DELETE /invoice/{id} status", status, 204)
        expect_equal(step, "DELETE /invoice/{id} payload", payload, None)
        created_invoice_id = None

        status, payload = request_json("PUT", f"{invoice_base}/invoice/{paid_invoice_id}/paid")
        expect_equal(step, "PUT /invoice/{id}/paid status", status, 200)
        expect_equal(step, "status after paid", payload["status"], "paid")

    def test_payment_endpoints(step: StepResult):
        nonlocal created_payment_id

        status, payload = request_json(
            "POST",
            f"{payment_base}/payments/intents",
            {
                "invoiceId": paid_invoice_id,
                "recordId": now_tag + 1,
                "amount": "80.00",
                "currency": "sgd",
                "description": "smoke test payment",
            },
        )

        if status != 201:
            msg = (
                "Stripe-dependent create intent did not return 201. "
                "Set STRIPE_SECRET_KEY/STRIPE_WEBHOOK_SECRET if you want full payment flow."
            )
            if args.require_stripe:
                step.fail(f"{msg} HTTP status was {status}")
                raise TestFailure("POST /payments/intents")
            step.info(f"SKIPPED: {msg} HTTP status was {status}")

            status, _ = request_json("GET", f"{payment_base}/payments/999999999")
            expect_equal(step, "GET /payments/{id} not found status", status, 404)

            status, payload = request_json("GET", f"{payment_base}/payments/invoice/{paid_invoice_id}")
            expect_equal(step, "GET /payments/invoice/{invoice_id} status", status, 200)
            expect_equal(step, "GET /payments/invoice returns list", isinstance(payload, list), True)

            status, _ = request_json(
                "GET", f"{payment_base}/payments/invoice/{paid_invoice_id}/latest"
            )
            expect_in(step, "GET /payments/invoice/{id}/latest status", status, [200, 404])

            status, _ = request_json("POST", f"{payment_base}/payments/999999999/cancel")
            expect_equal(step, "POST /payments/{id}/cancel not found status", status, 404)

            status, _ = request_json(
                "POST",
                f"{payment_base}/payments/webhook",
                {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_fake"}}},
            )
            expect_in(step, "POST /payments/webhook status", status, [200, 400, 500])
            return

        created_payment_id = payload["paymentId"]
        step.info(f"created paymentId={created_payment_id}")

        status, payload = request_json("GET", f"{payment_base}/payments/{created_payment_id}")
        expect_equal(step, "GET /payments/{id} status", status, 200)
        expect_equal(step, "GET /payments/{id} paymentId", payload["paymentId"], created_payment_id)

        status, payload = request_json("GET", f"{payment_base}/payments/invoice/{paid_invoice_id}")
        expect_equal(step, "GET /payments/invoice/{invoice_id} status", status, 200)
        expect_equal(step, "GET /payments/invoice returns list", isinstance(payload, list), True)
        expect_equal(step, "GET /payments/invoice list non-empty", len(payload) > 0, True)

        status, payload = request_json(
            "GET", f"{payment_base}/payments/invoice/{paid_invoice_id}/latest"
        )
        expect_equal(step, "GET /payments/invoice/{invoice_id}/latest status", status, 200)
        expect_equal(step, "latest paymentId", payload["paymentId"], created_payment_id)

        status, payload = request_json(
            "POST", f"{payment_base}/payments/{created_payment_id}/cancel"
        )
        expect_equal(step, "POST /payments/{id}/cancel status", status, 200)
        expect_equal(step, "status after cancel", payload["status"], "cancelled")

        status, _ = request_json(
            "POST",
            f"{payment_base}/payments/webhook",
            {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_fake"}}},
        )
        expect_in(step, "POST /payments/webhook status", status, [200, 400, 500])

    if drug_ready:
        run_step("Drug service endpoints", test_drug_crud, summary)
    if invoice_ready:
        run_step("Invoice service endpoints", test_invoice_endpoints, summary)
    if payment_ready and not args.skip_payment:
        run_step("Payment service endpoints", test_payment_endpoints, summary)
    elif args.skip_payment:
        print("\n[INFO] Payment service endpoints skipped by --skip-payment")

    print("\n[SUMMARY]")
    total = summary["passed"] + summary["failed"]
    print(f"Passed: {summary['passed']}/{total}")
    for step in summary["steps"]:
        tag = "PASS" if step.passed else "FAIL"
        print(f"- [{tag}] {step.name}")

    if summary["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

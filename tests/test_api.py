import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.settings import Settings
from money import plaid_bank

TODAY = date(2026, 10, 23)
PASSWORD = "correct horse battery staple"


def make_client(**overrides):
    settings = Settings(secret_key="test-secret", app_password=PASSWORD, plaid_client_id=None,
                        plaid_secret=None, cookie_secure=False)
    for key, value in overrides.items():
        setattr(settings, key, value)
    return TestClient(create_app(settings, today=TODAY))


@pytest.fixture
def client():
    return make_client()


@pytest.fixture
def demo(client):
    assert client.post("/api/login", json={"demo": True}).status_code == 200
    return client


def sse_events(response):
    return [json.loads(line[len("data: "):]) for line in response.text.splitlines() if line.startswith("data: ")]


def test_health_is_public(client):
    assert client.get("/api/health").json() == {"ok": True}


def test_public_preview_uses_demo_data_only(client):
    body = client.get("/api/preview").json()
    assert body["story"][1] == {"value": "$2,403.49", "kind": "spent"}
    assert len(body["pace"]) == 31
    assert {a["merchant"] for a in body["alerts"]} == {"ElectroMart", "The Capital Grille"}
    assert [e["question"] for e in body["examples"]][0] == "Where did my money go this month?"
    assert all(e["answer"] for e in body["examples"])
    assert "accounts" not in body


def test_data_needs_login(client):
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/transactions").status_code == 401
    assert client.post("/api/ask", json={"question": "hi"}).status_code == 401


def test_session_describes_setup(client):
    body = client.get("/api/session").json()
    assert body == {"authenticated": False, "mode": None, "password_required": True,
                    "plaid_available": False, "ai_engine": body["ai_engine"]}
    assert body["ai_engine"] in ("claude", "rules")


def test_wrong_password_is_rejected(client):
    assert client.post("/api/login", json={"password": "nope"}).status_code == 401
    assert client.get("/api/session").json()["authenticated"] is False


def test_owner_login_and_logout(client):
    assert client.post("/api/login", json={"password": PASSWORD}).json()["mode"] == "owner"
    assert client.get("/api/dashboard").status_code == 200
    client.post("/api/logout")
    assert client.get("/api/dashboard").status_code == 401


def test_forged_cookie_is_401_not_500(client):
    client.cookies.set("sensible_session", "forged.value.here")
    assert client.get("/api/dashboard").status_code == 401


def test_dashboard_shape(demo):
    body = demo.get("/api/dashboard").json()
    assert body["month"] == "2026-10"
    assert body["source"] == "Fake bank"
    assert body["net_worth"] == 6046.24
    assert body["summary"]["spent"] == 2403.49
    assert body["by_category"][0] == {"category": "Shopping", "amount": 783.99}
    assert len(body["pace"]) == 31
    assert {a["merchant"] for a in body["alerts"]} == {"ElectroMart", "The Capital Grille"}
    assert body["subscriptions"][0]["merchant"] == "Planet Fitness"
    assert body["story"][1] == {"value": "$2,403.49", "kind": "spent"}
    assert body["months"][0] == {"value": "2026-10", "label": "October 2026"}
    assert len(body["accounts"]) == 5
    assert body["goal"]["saved"] == 3250.0


def test_dashboard_other_month_and_bad_month(demo):
    assert demo.get("/api/dashboard?month=2026-09").json()["summary"]["spent"] == 1702.31
    assert demo.get("/api/dashboard?month=2026-9x").status_code == 422
    assert demo.get("/api/dashboard?month=2019-01").json()["month"] == "2026-10"  # unknown month: latest


def test_transactions_filters(demo):
    rows = demo.get("/api/transactions?q=spot").json()
    assert rows and all(r["merchant"] == "Spotify" for r in rows)
    assert rows[0]["account"] == "Student Rewards Card"
    rows = demo.get("/api/transactions?category=Income").json()
    assert all(r["category"] == "Income" for r in rows)
    assert demo.get("/api/transactions?q=" + "x" * 101).status_code == 422


def test_ask_streams_sse(demo):
    response = demo.post("/api/ask", json={"question": "Where did my money go this month?"})
    assert response.headers["content-type"].startswith("text/event-stream")
    events = sse_events(response)
    assert events[0]["type"] == "meta"
    assert any(e["type"] == "delta" and "$2,403.49" in e["text"] for e in events)
    assert events[-1] == {"type": "done"}


def test_ask_refusal(demo):
    events = sse_events(demo.post("/api/ask", json={"question": "Transfer $500 to savings"}))
    assert events[0]["refused"] is True


def test_ask_validates_input(demo):
    assert demo.post("/api/ask", json={"question": ""}).status_code == 422
    assert demo.post("/api/ask", json={"question": "x" * 501}).status_code == 422
    too_long_history = [{"role": "user", "content": "hi"}] * 9
    assert demo.post("/api/ask", json={"question": "hi", "history": too_long_history}).status_code == 422
    assert demo.post("/api/ask", json={"question": "hi", "history": [{"role": "system", "content": "x"}]}).status_code == 422


def test_ask_is_rate_limited(demo):
    for _ in range(10):
        assert demo.post("/api/ask", json={"question": "hi"}).status_code == 200
    blocked = demo.post("/api/ask", json={"question": "hi"})
    assert blocked.status_code == 429
    assert blocked.json()["retry_after"] > 0


def test_security_headers_on_every_response(client):
    for response in (client.get("/api/health"), client.get("/api/dashboard")):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert "default-src 'self'" in response.headers["content-security-policy"]
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_session_cookie_is_httponly_and_samesite(client):
    response = client.post("/api/login", json={"demo": True})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie


def test_plaid_needs_keys(client):
    client.post("/api/login", json={"password": PASSWORD})
    assert client.post("/api/plaid/link-token").status_code == 503


def test_demo_cannot_connect_plaid_when_owner_password_set():
    c = make_client(plaid_client_id="id", plaid_secret="secret")
    c.post("/api/login", json={"demo": True})
    assert c.post("/api/plaid/link-token").status_code == 403


class FakeBank:
    def __init__(self, client_id, secret, access_token=None, api=None):
        self.access_token = access_token

    def create_link_token(self, user_id):
        return "link-sandbox-123"

    def exchange_public_token(self, token):
        if token == "bad":
            error = Exception("boom")
            error.body = '{"error_code": "INVALID_PUBLIC_TOKEN", "error_message": "bad token"}'
            raise error
        self.access_token = "access-sandbox-SECRET"
        return self.access_token

    def get_accounts(self):
        return plaid_bank.normalize_accounts([{"account_id": "p1", "name": "Plaid Checking", "type": "depository",
                                               "subtype": "checking", "balances": {"current": 110.0}}])

    def get_transactions(self, days=90):
        return plaid_bank.normalize_transactions([{"date": TODAY, "account_id": "p1", "name": "SparkFun",
                                                   "merchant_name": "SparkFun", "amount": 89.4,
                                                   "personal_finance_category": {"primary": "GENERAL_MERCHANDISE"}}])


def test_plaid_link_flow_keeps_access_token_server_side(monkeypatch):
    monkeypatch.setattr(plaid_bank, "PlaidSandboxBank", FakeBank)
    c = make_client(plaid_client_id="id", plaid_secret="secret")
    c.post("/api/login", json={"password": PASSWORD})
    assert c.post("/api/plaid/link-token").json() == {"link_token": "link-sandbox-123"}

    bad = c.post("/api/plaid/exchange", json={"public_token": "bad"})
    assert bad.status_code == 400 and bad.json()["detail"] == "INVALID_PUBLIC_TOKEN"

    seen = [c.post("/api/plaid/exchange", json={"public_token": "public-sandbox-1"})]
    seen.append(c.get("/api/dashboard"))
    seen.append(c.get("/api/session"))
    seen.append(c.get("/api/transactions"))
    assert seen[1].json()["source"] == "Plaid Sandbox"
    assert seen[1].json()["accounts"][0]["name"] == "Plaid Checking"
    for response in seen:
        assert "access-sandbox-SECRET" not in response.text
        assert "access-sandbox-SECRET" not in response.headers.get("set-cookie", "")

    c.post("/api/plaid/disconnect")
    assert c.get("/api/dashboard").json()["source"] == "Fake bank"


class BrokenBank(FakeBank):
    calls = 0

    def get_accounts(self):
        BrokenBank.calls += 1
        error = Exception("boom")
        error.body = '{"error_code": "ITEM_LOGIN_REQUIRED"}'
        raise error


def test_failed_plaid_connection_falls_back_once_and_stops_retrying(monkeypatch):
    monkeypatch.setattr(plaid_bank, "PlaidSandboxBank", BrokenBank)
    c = make_client(plaid_client_id="id", plaid_secret="secret")
    c.post("/api/login", json={"password": PASSWORD})
    c.post("/api/plaid/exchange", json={"public_token": "public-sandbox-1"})
    first, second = c.get("/api/dashboard").json(), c.get("/api/dashboard").json()
    assert first["source"] == second["source"] == "Fake bank (Plaid failed: ITEM_LOGIN_REQUIRED)"
    assert BrokenBank.calls == 1
    c.post("/api/plaid/disconnect")
    assert c.get("/api/dashboard").json()["source"] == "Fake bank"


def test_security_center_checks(demo):
    checks = demo.get("/api/security").json()
    ids = [c["id"] for c in checks]
    assert ids == ["env_ignored", "no_secrets_in_code", "secret_key", "owner_password", "session_cookie",
                   "security_headers", "rate_limit", "plaid_tokens", "ai_guardrails"]
    by_id = {c["id"]: c for c in checks}
    assert by_id["env_ignored"]["status"] == "pass"
    assert by_id["no_secrets_in_code"]["status"] == "pass"
    assert by_id["ai_guardrails"]["status"] == "pass"
    assert len(by_id["ai_guardrails"]["attacks"]) == 5
    assert all(a["blocked"] for a in by_id["ai_guardrails"]["attacks"])


def test_missing_secret_key_is_flagged():
    c = make_client(secret_key=None)
    c.post("/api/login", json={"demo": True})
    by_id = {x["id"]: x for x in c.get("/api/security").json()}
    assert by_id["secret_key"]["status"] == "warn"

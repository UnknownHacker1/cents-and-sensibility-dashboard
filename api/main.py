"""Sensible's web API. Wraps the money/ package and serves the built React app.

Run it:  python -m uvicorn api.main:app --port 8000
"""

import json
import secrets
import time
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from api.security import SECURITY_HEADERS, RateLimiter, run_checks
from api.settings import Settings
from money import ai, analytics, assistant, fake_bank, plaid_bank, story

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
PLAID_CACHE_SECONDS = 300


class LoginBody(BaseModel):
    password: str | None = Field(default=None, max_length=200)
    demo: bool = False


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[Turn] = Field(default_factory=list, max_length=8)


class ExchangeBody(BaseModel):
    public_token: str = Field(min_length=1, max_length=200)


@lru_cache(maxsize=4)
def _fake_bank(today: date):
    return fake_bank.get_accounts(), fake_bank.get_transactions(today=today)


def _plaid_error_code(error: Exception) -> str:
    try:
        return json.loads(error.body)["error_code"]
    except (AttributeError, TypeError, ValueError, KeyError):
        return "PLAID_ERROR"


def _records(frame: pd.DataFrame) -> list[dict]:
    out = frame.copy()
    for column in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[column]):
            out[column] = out[column].dt.strftime("%Y-%m-%d")
    return out.to_dict(orient="records")


def create_app(settings: Settings | None = None, today: date | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Sensible", docs_url=None, redoc_url=None, openapi_url=None)
    limiter = RateLimiter(limit=10, window=60)
    vault: dict[str, dict] = {}  # session id -> server-only data (Plaid access token, cached bank data)

    def today_() -> date:
        return today or date.today()

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    app.add_middleware(SessionMiddleware, secret_key=settings.session_key, session_cookie="sensible_session",
                       max_age=8 * 60 * 60, same_site="lax", https_only=settings.cookie_secure)

    def session(request: Request) -> dict:
        if not request.session.get("sid"):
            raise HTTPException(401, "Sign in to see your money.")
        return request.session

    def bank(sess: dict) -> tuple[pd.DataFrame, pd.DataFrame, str]:
        entry = vault.get(sess["sid"], {})
        if entry.get("plaid_error"):  # a dead connection stays on the fake bank until reconnect or disconnect
            accounts, tx = _fake_bank(today_())
            return accounts, tx, f"Fake bank (Plaid failed: {entry['plaid_error']})"
        token = entry.get("plaid_token")
        if token and settings.plaid_available:
            cached = entry.get("plaid_data")
            if cached and time.monotonic() - cached[2] < PLAID_CACHE_SECONDS:
                return cached[0], cached[1], "Plaid Sandbox"
            try:
                connection = plaid_bank.PlaidSandboxBank(settings.plaid_client_id, settings.plaid_secret,
                                                         access_token=token)
                accounts, tx = connection.get_accounts(), connection.get_transactions()
                entry["plaid_data"] = (accounts, tx, time.monotonic())
                return accounts, tx, "Plaid Sandbox"
            except Exception as error:
                vault[sess["sid"]] = {"plaid_error": _plaid_error_code(error)}
                accounts, tx = _fake_bank(today_())
                return accounts, tx, f"Fake bank (Plaid failed: {_plaid_error_code(error)})"
        accounts, tx = _fake_bank(today_())
        return accounts, tx, "Fake bank"

    def can_connect_bank(sess: dict) -> bool:
        return sess.get("mode") == "owner" or not settings.app_password

    # ---------- Session ----------
    @app.get("/api/health")
    def health():
        return {"ok": True}

    @app.get("/api/session")
    def get_session(request: Request):
        sess = request.session
        return {"authenticated": bool(sess.get("sid")), "mode": sess.get("mode"),
                "password_required": bool(settings.app_password), "plaid_available": settings.plaid_available,
                "ai_engine": ai.engine_name()}

    @app.get("/api/preview")
    def preview():
        """Public, fake-data-only numbers for the landing page. Never touches a connected bank."""
        accounts, tx = _fake_bank(today_())
        month = pd.Period(today_(), "M")
        examples = assistant.EXAMPLE_QUESTIONS[:3]
        return {
            "story": story.month_story(tx, month, today=today_()),
            "pace": analytics.pace(tx, month, today=today_()),
            "alerts": _records(analytics.find_unusual_charges(tx, today=today_())),
            "examples": [{"question": q, "answer": assistant.answer(q, accounts, tx, today=today_()).text}
                         for q in examples],
        }

    @app.post("/api/login")
    def login(body: LoginBody, request: Request):
        if body.demo:
            mode = "demo"
        elif settings.app_password and body.password and secrets.compare_digest(
                body.password.encode(), settings.app_password.encode()):
            mode = "owner"
        else:
            raise HTTPException(401, "That password didn't match." if settings.app_password
                                else "Owner login isn't set up. Add APP_PASSWORD to .env, or explore the demo.")
        request.session.clear()
        request.session.update({"sid": secrets.token_urlsafe(16), "mode": mode})
        return {"mode": mode}

    @app.post("/api/logout")
    def logout(request: Request):
        vault.pop(request.session.get("sid", ""), None)
        request.session.clear()
        return {"ok": True}

    # ---------- Money ----------
    @app.get("/api/dashboard")
    def dashboard(month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"), sess: dict = Depends(session)):
        accounts, tx, source = bank(sess)
        available = analytics.months(tx) or [pd.Period(today_(), "M")]
        picked = pd.Period(month, "M") if month else available[0]
        if picked not in available:
            picked = available[0]
        summary = analytics.month_summary(tx, picked)
        return {
            "source": source,
            "month": str(picked),
            "months": [{"value": str(m), "label": m.strftime("%B %Y")} for m in available],
            "story": story.month_story(tx, picked, today=today_()),
            "net_worth": analytics.net_worth(accounts),
            "accounts": _records(accounts),
            "summary": summary,
            "by_category": [{"category": c, "amount": a} for c, a in analytics.spending_by_category(tx, picked).items()],
            "pace": analytics.pace(tx, picked, today=today_()),
            "subscriptions": _records(analytics.find_subscriptions(tx)),
            "alerts": _records(analytics.find_unusual_charges(tx, today=today_())),
            "goal": {"saved": float(accounts.loc[accounts["type"] == "savings", "balance"].sum())},
        }

    @app.get("/api/transactions")
    def transactions(q: str = Query(default="", max_length=100), category: str = Query(default="", max_length=40),
                     account: str = Query(default="", max_length=60), sess: dict = Depends(session)):
        accounts, tx, _ = bank(sess)
        names = dict(zip(accounts["id"], accounts["name"]))
        rows = tx.assign(account=tx["account_id"].map(names))
        if q:
            rows = rows[rows["merchant"].str.contains(q, case=False, regex=False)]
        if category:
            rows = rows[rows["category"] == category]
        if account:
            rows = rows[rows["account_id"] == account]
        return _records(rows[["date", "merchant", "category", "account", "account_id", "amount"]].head(500))

    @app.post("/api/ask")
    def ask(body: AskBody, sess: dict = Depends(session)):
        wait = limiter.check(sess["sid"])
        if wait:
            return JSONResponse({"detail": "You're asking fast. Try again in a moment.", "retry_after": wait},
                                status_code=429)
        accounts, tx, _ = bank(sess)
        events = ai.stream_answer(body.question, accounts, tx, history=[t.model_dump() for t in body.history],
                                  today=today_(), client=ai.default_client())
        return StreamingResponse((f"data: {json.dumps(e)}\n\n" for e in events), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    # ---------- Plaid (Event 2) ----------
    def plaid_ready(sess: dict):
        if not settings.plaid_available:
            raise HTTPException(503, "Add PLAID_CLIENT_ID and PLAID_SECRET to .env to connect a sandbox bank.")
        if not can_connect_bank(sess):
            raise HTTPException(403, "Sign in with the owner password to connect a bank.")

    @app.post("/api/plaid/link-token")
    def link_token(sess: dict = Depends(session)):
        plaid_ready(sess)
        connection = plaid_bank.PlaidSandboxBank(settings.plaid_client_id, settings.plaid_secret)
        try:
            return {"link_token": connection.create_link_token(sess["sid"])}
        except Exception as error:
            raise HTTPException(400, _plaid_error_code(error)) from None

    @app.post("/api/plaid/exchange")
    def exchange(body: ExchangeBody, sess: dict = Depends(session)):
        plaid_ready(sess)
        connection = plaid_bank.PlaidSandboxBank(settings.plaid_client_id, settings.plaid_secret)
        try:
            token = connection.exchange_public_token(body.public_token)
        except Exception as error:
            raise HTTPException(400, _plaid_error_code(error)) from None
        vault[sess["sid"]] = {"plaid_token": token}
        return {"source": "Plaid Sandbox"}

    @app.post("/api/plaid/sandbox-connect")
    def sandbox_connect(sess: dict = Depends(session)):
        """One click, no popup: connects Plaid's test bank directly."""
        plaid_ready(sess)
        connection = plaid_bank.PlaidSandboxBank(settings.plaid_client_id, settings.plaid_secret)
        try:
            connection.connect()
        except Exception as error:
            raise HTTPException(400, _plaid_error_code(error)) from None
        vault[sess["sid"]] = {"plaid_token": connection.access_token}
        return {"source": "Plaid Sandbox"}

    @app.post("/api/plaid/disconnect")
    def disconnect(sess: dict = Depends(session)):
        vault.pop(sess["sid"], None)
        return {"source": "Fake bank"}

    # ---------- Security Center (Event 4) ----------
    @app.get("/api/security")
    def security(sess: dict = Depends(session)):
        return run_checks(settings, limiter)

    @app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def api_not_found(rest: str):
        raise HTTPException(404, "No such endpoint.")

    # ---------- The web app ----------
    if WEB_DIST.exists():
        @app.get("/{path:path}", include_in_schema=False)
        def web(path: str):
            file = (WEB_DIST / path).resolve()
            if path and file.is_file() and WEB_DIST.resolve() in file.parents:
                return FileResponse(file)
            return FileResponse(WEB_DIST / "index.html")

    return app


app = create_app() if __name__ != "__main__" else None

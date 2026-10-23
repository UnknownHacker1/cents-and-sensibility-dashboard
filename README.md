# Sensible, by Cents & Sensibility

*Your money, finally making sense.*

A personal finance app built for the FinTech Club Innovation Series. It puts every account in one place, explains your month in one sentence, flags charges that look off, and answers questions about your money. It covers all five events: fake bank, Plaid Sandbox, a real AI assistant, a live Security Center, and a demo-ready site.

**All data is fake or Plaid Sandbox test data.** Educational only, not financial advice.

## Run it

**Codespaces (nothing to install):** Code → Codespaces → Create codespace on main. The devcontainer installs Python and Node, builds the site, and starts it on port 8000.

**Your own computer** (Python 3.11+ and Node 20+):

```bash
python -m pip install -r requirements-dev.txt
cd web && npm install && npm run build && cd ..
python -m uvicorn api.main:app --port 8000
```

Then open http://localhost:8000 and click **Open the demo**. On Mac use `python3`.

**Working on the frontend:** run the API as above, then `cd web && npm run dev` and open http://localhost:5173. Vite forwards `/api` to port 8000 and reloads on save.

**Tests:**

```bash
python -m pytest
cd web && npm run typecheck
```

## Turning things on

Everything is optional. Copy `.env.example` to `.env` and fill in what you have, then restart.

| Setting | What it unlocks |
|---|---|
| `PLAID_CLIENT_ID`, `PLAID_SECRET` | Event 2: the Accounts page can connect Plaid's Sandbox through Plaid Link, or in one click. Test login: `user_good` / `pass_good` |
| `ANTHROPIC_API_KEY` | Event 3: Money Brain answers with Claude (`claude-opus-5-5`), streamed. Without a key, the rules engine answers |
| `SECRET_KEY`, `APP_PASSWORD`, `COOKIE_SECURE` | Event 4: stable signed sessions, an owner login that guards bank connections, HTTPS-only cookies |

## How it fits together

| Path | What it does |
|---|---|
| `web/` | The site: React, TypeScript, Tailwind, Recharts. Landing page, Overview, Transactions, Accounts, Security Center, and the Ask panel (Ctrl K) |
| `api/main.py` | FastAPI. Sessions, dashboard data, streaming answers, Plaid Link endpoints. Serves the built site |
| `api/security.py` | Security headers, rate limiter, and the 9 live checks behind the Security Center, including a red-team run |
| `money/ai.py` | Money Brain on Claude. Guardrails run in code first; the model only ever sees totals and merchant names |
| `money/assistant.py` | Guardrails and the rules engine. Also the fallback whenever Claude is off or fails |
| `money/analytics.py`, `money/story.py` | Spending, pace vs last month, subscriptions, unusual charges, and the one-sentence month story |
| `money/fake_bank.py`, `money/plaid_bank.py` | The pretend bank and the Plaid Sandbox connection |
| `app.py` | The original Event 1 Streamlit screen, kept for reference (`streamlit run app.py`) |
| `tests/` | 93 tests, no internet or keys needed |
| `api/check_plaid.py` | `python -m api.check_plaid` tests your Plaid keys from the terminal without printing them |
| `docs/` | Team sheet, sketch, assistant rules, security risks, share-out, demo script, specs and plans |

## Events

- **Event 1, Vibe Check:** team, roles, features, sketch, running app, and all bonuses. See `docs/team-sheet.md`.
- **Event 2, Plug It In:** Plaid Link in the browser, public token swapped for an access token on the server. The access token never reaches the browser.
- **Event 3, Talk to Your Wallet:** Claude with streaming, a system prompt built from the 5 rules, and guardrails that run before the model is called.
- **Event 4, Lock It Down:** signed httpOnly cookies, CSP and other headers, rate limiting, secret scanning, prompt-injection blocking. The Security Center grades the app live.
- **Event 5, Demo Night:** `docs/demo-script.md`.

## Ground rules

Fake data only. No secrets in code (`.env` is gitignored, and the Security Center scans for leaked keys). Help each other.

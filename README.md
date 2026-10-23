# Sensible, by Cents & Sensibility

*Your money, finally making sense.*

An AI-powered personal finance dashboard built for the FinTech Club Innovation Series. It shows all your accounts, where your money went, unusual-charge alerts, subscriptions, and a savings goal, and you can ask it questions about your money. **All data is fake.** Educational only, not financial advice.

## Run it

**Codespaces (nothing to install):** Code → Codespaces → Create codespace on main. The devcontainer installs everything and starts the app. Click *Open in Browser* when it pops up.

**Your own computer:**

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open http://localhost:8501. On Mac use `python3`.

**Tests:**

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## What's in here

| Path | What it does |
|---|---|
| `app.py` | The screen. Look for `TEAM TODO` to change the team name. |
| `money/fake_bank.py` | A pretend bank: 5 accounts, 90 days of realistic transactions |
| `money/plaid_bank.py` | Plaid Sandbox connection (Event 2 head start) |
| `money/data_source.py` | Uses Plaid if keys are set, otherwise the fake bank. Never crashes |
| `money/analytics.py` | Spending by category, month vs last month, subscriptions, unusual charges |
| `money/assistant.py` | Money Brain: answers questions from your numbers and follows 5 safety rules |
| `tests/` | 48 tests, no internet needed |
| `docs/` | Team sheet, sketch, assistant rules, security risks, share-out script |

## Event checklist

- **Event 1, Vibe Check:** done. Team name, roles, features, questions, sketch, running app.
  - Silver: app name, tagline and colors; extra account (Cash App); competitor check.
  - Gold: spending chart; 5 assistant rules; what could go wrong.
- **Event 2, Plug It In:** head start. Make a free account at plaid.com, copy `.env.example` to `.env`, and paste your **sandbox** client ID and secret. Restart the app and the badge at the top should say *Plaid Sandbox*. If the keys are wrong, the badge shows Plaid's error and the app keeps running on the fake bank.
- **Event 3, Talk to Your Wallet:** swap the keyword router in `assistant.answer()` for an LLM call. Use `RULES` as the system prompt and `build_context()` as the facts. Keep the guardrail checks in code.
- **Event 4, Lock It Down:** start from `docs/security-risks.md`.
- **Event 5, Demo Night:** start from `docs/share-out.md`.

## Ground rules

Fake data only. No secrets in code (`.env` is gitignored). Help each other.

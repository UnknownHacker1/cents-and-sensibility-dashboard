# Sensible Dashboard Design (Team Cents & Sensibility)

FinTech Club Innovation Series, Event 1 (Vibe Check) plus all bonus challenges plus an Event 2 head start.

## Intent

- **Outcome:** a working AI-style personal finance dashboard the team can run, present in 60 seconds today, and grow through Events 2 to 5.
- **For:** a 3 to 4 person student team, mixed experience. Code must stay readable for beginners.
- **Success:** `streamlit run app.py` shows the team name, fake accounts, transactions, spending chart, alerts, subscriptions, savings goal and a working Ask box. Every Event 1 task and every Silver/Gold bonus has a concrete artifact in the repo. With Plaid sandbox keys in `.env` the same app runs on sandbox bank data.

Said by the user: Event 1 + all bonuses + some Event 2, improve on the PDF where sensible.
Assumed: local git repo only, nothing pushed to GitHub without asking. Teammate names are left as blanks.

## Brand

- Team name: **Cents & Sensibility**. Repo: `cents-and-sensibility-dashboard`.
- App name: **Sensible**. Tagline: "Your money, finally making sense."
- Colors: Ink `#14213D` (text), Mint `#2EC4B6` (primary), Coral `#FF6B6B` (alerts).

## Data model

Two pandas DataFrames, shared by every module.

- `accounts`: `id`, `name`, `type` (`checking` | `savings` | `credit` | `investment`), `institution`, `balance` (float, always positive; credit balance is money owed).
- `transactions`: `date` (datetime64), `account_id`, `merchant`, `category`, `amount` (float).
- **Sign convention (same as Plaid):** `amount > 0` is money out (spending), `amount < 0` is money in (income, refunds).
- Categories: Income, Housing, Groceries, Dining, Coffee, Transport, Shopping, Entertainment, Subscriptions, Health, Personal, Travel, Transfer.
- "Spending" means `amount > 0` and category not in {Income, Transfer}.

## Components

| Unit | Job | Depends on |
|---|---|---|
| `money/fake_bank.py` | Seeded generator: 5 accounts and ~90 days of realistic transactions with recurring subscriptions, paychecks, rent, and two planted unusual charges in the last 14 days | pandas |
| `money/plaid_bank.py` | Event 2 head start. Connects to Plaid **Sandbox** via `/sandbox/public_token/create` (no Link UI), exchanges the token, pulls accounts and transactions, normalizes them to the data model | plaid-python |
| `money/data_source.py` | Picks the source: Plaid if `PLAID_CLIENT_ID` and `PLAID_SECRET` are set and the connection works, else the fake bank. Never crashes | the two banks |
| `money/analytics.py` | Pure functions: spending by category, month summary with month-over-month change, net worth, subscription detection, unusual-charge alerts, savings goal progress | pandas |
| `money/assistant.py` | "Money Brain": keyword intent router that answers money questions from computed numbers, enforces the 5 assistant rules, and builds a grounded facts string for the Event 3 LLM | analytics |
| `app.py` | Streamlit UI only. Keeps the `TEAM TODO` title line from the guide | all of the above |

### Subscriptions rule
Group spending by (merchant, amount rounded to cents). A group is a subscription if it appears in at least 2 distinct months and the median gap between charges is 25 to 35 days.

### Unusual-charge rules (window: last 14 days)
1. **Big for its category:** amount is at least 3x the median of that category's charges *before* the window, and at least $50. Needs 3 or more prior charges in the category, otherwise the rule is skipped.
2. **New merchant, big amount:** merchant never seen before the window and amount at least $200.
Each alert carries a human `reason` string. Income and Transfer rows are never flagged.

### Assistant rules (shown in the app and in `docs/assistant-rules.md`)
1. Always answer from the user's own numbers, and show the numbers.
2. Never move, send, or transfer money, or pay bills.
3. Never guarantee returns or tell the user what to buy or sell. Educational only, not financial advice.
4. Never ask for or repeat card numbers, SSNs, passwords, or bank logins. If one is pasted, refuse and warn.
5. If the data cannot answer the question, say so plainly instead of guessing.

## UI layout (main screen)

1. Header: team name, app name, tagline, data source badge, "Fake data only. Not financial advice."
2. Sidebar: month picker, savings goal target, account filter.
3. Metric tiles: net worth, spent this month (delta vs last month), income this month, subscriptions per month.
4. Spending by category bar chart | Alerts panel.
5. Ask Money Brain: text box plus 5 one-click example questions, answer history.
6. Accounts table | Subscriptions table | Savings goal progress bar.
7. Transactions table with category filter and merchant search.

## Repo extras

- `.devcontainer/devcontainer.json` for Codespaces (guide Option B): Python 3.11, installs requirements, forwards 8501.
- `.streamlit/config.toml` brand theme.
- `.gitignore` covers `.env`, `.streamlit/secrets.toml`, `.venv`. `.env.example` lists the Plaid variables with empty values.
- `requirements.txt` (app) and `requirements-dev.txt` (adds pytest).

## Team docs (`docs/`)

- `team-sheet.md`: team name, role table with blank name slots, 3 must-have and 2 nice-to-have features ("A user can ___"), 5 user questions, competitor check (2 real apps), brand.
- `sketch.svg`: wireframe of the main screen with labeled boxes.
- `assistant-rules.md`, `security-risks.md` (3 risks and how to prevent each), `share-out.md` (60-second script).

## Error handling

- Empty transactions or a month with no spending: zeros and friendly text, no exceptions.
- Last month spend of 0: change is `None` and shown as "n/a", never divide by zero.
- Plaid failure of any kind: fall back to the fake bank and show why in the source badge.
- Sensitive data pasted in Ask box: refuse, never echo it back.

## Testing

pytest, no network. Plaid is tested through its pure normalize functions and a monkeypatched failing connect.

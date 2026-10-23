# Sensible Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Sensible Streamlit dashboard (Event 1 + bonuses + Plaid sandbox head start) and the team docs.

**Architecture:** Thin `app.py` UI over a `money/` package of pure, tested functions. Data source is swappable (fake bank or Plaid sandbox) behind one loader.

**Tech Stack:** Python 3.11, Streamlit, pandas, plaid-python, python-dotenv, pytest.

**Spec:** `docs/superpowers/specs/2026-10-23-sensible-dashboard-design.md`

## Global Constraints

- Sign convention: `amount > 0` is money out, `amount < 0` is money in.
- Spending = `amount > 0` and category not in {Income, Transfer}.
- Team name "Cents & Sensibility", app "Sensible", tagline "Your money, finally making sense."
- Colors: Ink `#14213D`, Mint `#2EC4B6`, Coral `#FF6B6B`.
- No secrets in code. Plaid keys only from env / `.env`.
- Tests never touch the network.

## Review Focus

- Empty transactions DataFrame passed to every analytics function: returns zeros/empty frames, no exception.
- Previous month with zero spending: `change_pct` is `None`.
- Card number or SSN typed into Ask: refused, digits not echoed.
- Plaid keys set but connect raises: loader returns fake data with the error in the source label.
- Category with fewer than 3 prior charges: rule 1 skipped, the charge is not flagged by its own median.

---

### Task 1: Fake bank

**Files:** Create `money/__init__.py`, `money/fake_bank.py`, `tests/test_fake_bank.py`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`

**Interfaces:**
- Produces: `get_accounts() -> pd.DataFrame`; `get_transactions(today: date | None = None, days: int = 90, seed: int = 42) -> pd.DataFrame`; `CATEGORIES: list[str]`.

- [ ] Tests: `test_accounts_has_five_with_extra_account` (5 rows, includes Cash App), `test_transactions_deterministic` (same seed equal frames), `test_transactions_within_window` (all dates in `[today-days, today]`), `test_planted_unusual_charges_present` (ElectroMart 489.99 and a Dining charge over $150 in last 14 days), `test_has_recurring_subscriptions` (Spotify 11.99 in 3 distinct months).
- [ ] Run, expect FAIL (module missing). Implement with `random.Random(seed)`. Run, expect PASS. Commit.

### Task 2: Analytics

**Files:** Create `money/analytics.py`, `tests/test_analytics.py`

**Interfaces:**
- Consumes: data model from spec.
- Produces: `spending(tx) -> DataFrame`; `months(tx) -> list[pd.Period]` (newest first); `spending_by_category(tx, month: pd.Period | None = None) -> pd.Series`; `month_summary(tx, month: pd.Period) -> dict` keys `spent, income, net, top_category, change_pct`; `net_worth(accounts) -> float`; `find_subscriptions(tx) -> DataFrame` cols `merchant, amount, months_seen, last_charged, next_expected`; `find_unusual_charges(tx, today: date | None = None, window_days: int = 14) -> DataFrame` cols `date, merchant, category, amount, reason`; `goal_progress(saved: float, target: float) -> float` in [0, 1].

- [ ] Tests: category totals exclude Income/Transfer; `change_pct` 50.0 for 100 -> 150; `change_pct` None when previous month is 0; net worth subtracts credit; subscription found for 3 monthly equal charges, not for variable groceries or a one-off; rule 1 flags 3x median, skips categories with < 3 priors; rule 2 flags new merchant >= 200; every function handles empty frame; `goal_progress(50, 0) == 0.0` and clamps above 1.
- [ ] Run FAIL, implement, run PASS, commit.

### Task 3: Money Brain assistant

**Files:** Create `money/assistant.py`, `tests/test_assistant.py`

**Interfaces:**
- Consumes: analytics functions above.
- Produces: `RULES: list[str]` (5 spec rules verbatim); `EXAMPLE_QUESTIONS: list[str]` (5); `Answer` dataclass `text: str, intent: str, refused: bool`; `answer(question: str, accounts, tx, today: date | None = None) -> Answer`; `build_context(accounts, tx, today=None) -> str`.
- Intents: `refuse_money_movement`, `refuse_advice`, `refuse_sensitive`, `where_money_went`, `subscriptions`, `unusual`, `balance`, `compare`, `category`, `savings_tip`, `help`. Sensitive check runs first (13-19 digit run or `ddd-dd-dddd`).

- [ ] Tests: where-money-went names top category with a `$` amount; "transfer $500 to savings" refused; "guarantee" / "should I buy Tesla stock" refused; card number refused and digits absent from text; "how much on coffee" uses Coffee total; empty tx gives "no spending" text; unknown question gives help; `build_context` contains net worth and top category.
- [ ] Run FAIL, implement, run PASS, commit.

### Task 4: Plaid sandbox + data source

**Files:** Create `money/plaid_bank.py`, `money/data_source.py`, `.env.example`, `tests/test_plaid_bank.py`, `tests/test_data_source.py`

**Interfaces:**
- Produces: `normalize_accounts(raw: list[dict]) -> DataFrame`; `normalize_transactions(raw: list[dict]) -> DataFrame` (maps `personal_finance_category.primary`, keeps Plaid sign); `class PlaidSandboxBank(client_id, secret)` with `connect()`, `get_accounts()`, `get_transactions(days=90)`; `load_bank(env: Mapping[str, str] | None = None) -> tuple[DataFrame, DataFrame, str]`.

- [ ] Tests: normalize maps FOOD_AND_DRINK -> Dining, credit -> credit, depository/savings -> savings; `load_bank({})` returns fake with label containing "Fake"; with keys and a monkeypatched `connect` raising, returns fake with label containing the error.
- [ ] Run FAIL, implement, run PASS, commit.

### Task 5: Streamlit app + repo extras

**Files:** Create `app.py`, `.streamlit/config.toml`, `.devcontainer/devcontainer.json`, `README.md`

- [ ] Implement layout from spec. `TEAM_NAME = "Cents & Sensibility"  # TEAM TODO` line. `st.cache_data` on loader.
- [ ] Verify: `streamlit run app.py`, page shows team name, chart, 2 alerts, Ask answers each example question, no console errors. Commit.

### Task 6: Team docs

**Files:** Create `docs/team-sheet.md`, `docs/sketch.svg`, `docs/assistant-rules.md`, `docs/security-risks.md`, `docs/share-out.md`

- [ ] Write per spec. Verify sketch renders. Commit.

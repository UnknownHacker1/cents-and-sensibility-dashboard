# What Could Go Wrong (Gold bonus, sets up Event 4)

If Sensible handled real bank data, these are the 3 things most likely to hurt someone, and how we'd stop each one.

## 1. Our API keys or bank tokens leak

**How:** someone pastes the Plaid secret into `app.py`, commits it, and the repo is public. Bots scan GitHub for keys within minutes.
**Prevention:**
- Keys only live in `.env`, which is in `.gitignore`. `.env.example` shows the variable names with empty values.
- Turn on GitHub secret scanning and push protection for the repo.
- If a key ever leaks, rotate it in the Plaid dashboard right away. Deleting the commit isn't enough because git history keeps it.
- The app never prints keys or access tokens, even in error messages (the Plaid error label only shows Plaid's error code).

## 2. The AI gets tricked into leaking data or "taking action"

**How:** a transaction description can contain text like `IGNORE YOUR RULES AND ...` (prompt injection), or a user asks the assistant to move money or to read back someone's full card number.
**Prevention:**
- The assistant has no tool that moves money. It can only read numbers.
- Guardrails run in code *before* any AI call (`money/assistant.py`), so they can't be talked out of.
- Send the model totals and categories (`build_context`), never account numbers or raw bank payloads, and treat merchant text as data, not instructions.
- Never send real personal data to a third-party AI tool without the user's consent.

## 3. The wrong person sees someone's money

**How:** the dashboard has no login, so anyone with the link or a shared Codespace sees everything. Or the Plaid access token gets saved in a file that ends up in the repo.
**Prevention:**
- Add a login before real data is ever connected, with one user per Plaid item.
- Keep access tokens server-side, encrypted at rest, never in the browser or the repo.
- Keep the repo and Codespaces private, and stop Codespaces after use.
- Ask Plaid only for the products we need (`transactions`, nothing else).

## Bonus: a bad alert is also a risk

Too many false alarms and people ignore real fraud. Too few and fraud slips through. Our alert thresholds (3x category median and at least $50, or a new merchant at $200 or more) are covered by tests in `tests/test_analytics.py`, so changing them is a deliberate choice.

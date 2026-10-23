"""Check your Plaid Sandbox keys from the terminal: python -m api.check_plaid

Reads PLAID_CLIENT_ID and PLAID_SECRET from .env, makes a Link token, connects
Plaid's test bank, and pulls accounts and transactions. Prints what it found.
Never prints a key or a token.
"""

import sys

from api.main import _plaid_error_code
from api.settings import Settings
from money import plaid_bank


def check(settings: Settings, make_bank=None) -> tuple[bool, list[str]]:
    make_bank = make_bank or plaid_bank.PlaidSandboxBank
    if not settings.plaid_available:
        return False, ["No Plaid keys found. Put PLAID_CLIENT_ID and PLAID_SECRET in the .env file "
                       "in the project folder (copy .env.example), then run this again."]

    lines = ["Found PLAID_CLIENT_ID and PLAID_SECRET in .env."]
    step = "Making a Link token"
    try:
        bank = make_bank(settings.plaid_client_id, settings.plaid_secret)
        bank.create_link_token("sensible-key-check")
        lines.append("Link token: OK. The Connect with Plaid Link button will work.")
        step = "Connecting Plaid's test bank"
        bank.connect()
        step = "Reading accounts"
        accounts = bank.get_accounts()
        lines.append(f"{len(accounts)} accounts: {', '.join(accounts['name'])}.")
        step = "Reading transactions (a brand-new test bank can take ~20 seconds)"
        tx = bank.get_transactions()
    except Exception as error:
        code = _plaid_error_code(error)
        hint = {"INVALID_API_KEYS": " Copy the Sandbox secret, not Production, and check for extra spaces.",
                "INVALID_FIELD": " PLAID_CLIENT_ID looks wrong. It's the 24-character client_id from the Keys page.",
                "INVALID_PRODUCT": " Your Plaid account needs the Transactions product."}.get(code, "")
        return False, lines + [f"{step} failed. Plaid said: {code}.{hint}"]

    if tx.empty:
        lines.append("0 transactions so far. Plaid is still building the test history; wait a minute and retry.")
    else:
        lines.append(f"{len(tx)} transactions from {tx['date'].min():%b %d} to {tx['date'].max():%b %d}.")
    lines.append("All good. Restart the app, open Accounts, and connect.")
    return True, lines


if __name__ == "__main__":
    ok, report = check(Settings.from_env())
    print("\n".join(report))
    sys.exit(0 if ok else 1)

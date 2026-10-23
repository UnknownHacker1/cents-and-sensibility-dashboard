"""One place that decides where the money data comes from.

PLAID_CLIENT_ID and PLAID_SECRET set (in .env)  -> Plaid Sandbox
not set, or Plaid fails for any reason          -> the fake bank
The app always gets data, and the label says which source it is.
"""

import json
import os
from collections.abc import Mapping

import pandas as pd

from money import fake_bank, plaid_bank


def load_bank(env: Mapping[str, str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if env is None:
        from dotenv import load_dotenv

        load_dotenv()
        env = os.environ

    client_id, secret = env.get("PLAID_CLIENT_ID"), env.get("PLAID_SECRET")
    if client_id and secret:
        try:
            bank = plaid_bank.PlaidSandboxBank(client_id, secret)
            bank.connect()
            return bank.get_accounts(), bank.get_transactions(), "Plaid Sandbox"
        except Exception as error:  # bad keys, no internet, Plaid down: fall back, never crash
            note = f"Fake bank (Plaid failed: {_describe(error)})"
            return fake_bank.get_accounts(), fake_bank.get_transactions(), note

    return fake_bank.get_accounts(), fake_bank.get_transactions(), "Fake bank"


def _describe(error: Exception) -> str:
    """Plaid errors carry a JSON body with a readable code; anything else, use the first line."""
    try:
        body = json.loads(error.body)
        return f"{body['error_code']}: {body['error_message']}"
    except (AttributeError, TypeError, ValueError, KeyError):
        return f"{type(error).__name__}: {str(error).splitlines()[0] if str(error) else ''}"[:160]

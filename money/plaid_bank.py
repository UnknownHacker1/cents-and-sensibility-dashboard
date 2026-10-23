"""Event 2 head start: a practice bank from Plaid Sandbox (fake accounts, real API).

Sandbox lets us skip the Plaid Link login screen: /sandbox/public_token/create
makes a token for a test bank, we swap it for an access token, then read
accounts and transactions. Keys come from .env, never from code.

Everything Plaid returns is turned into the same columns the fake bank uses,
so the rest of the app does not care where the data came from.
"""

import time
from datetime import date, timedelta

import pandas as pd

SANDBOX_INSTITUTION = "ins_109508"  # "First Platypus Bank", Plaid's test bank

PLAID_CATEGORIES = {
    "INCOME": "Income",
    "TRANSFER_IN": "Transfer",
    "TRANSFER_OUT": "Transfer",
    "LOAN_PAYMENTS": "Transfer",
    "BANK_FEES": "Personal",
    "ENTERTAINMENT": "Entertainment",
    "FOOD_AND_DRINK": "Dining",
    "GENERAL_MERCHANDISE": "Shopping",
    "HOME_IMPROVEMENT": "Shopping",
    "MEDICAL": "Health",
    "PERSONAL_CARE": "Personal",
    "GENERAL_SERVICES": "Personal",
    "GOVERNMENT_AND_NON_PROFIT": "Personal",
    "TRANSPORTATION": "Transport",
    "TRAVEL": "Travel",
    "RENT_AND_UTILITIES": "Housing",
}


def _account_type(plaid_type: str, subtype: str | None) -> str:
    if plaid_type == "depository":
        return "savings" if subtype in ("savings", "money market", "cd") else "checking"
    if plaid_type in ("credit", "loan"):
        return "credit"  # money owed
    return "investment"


def normalize_accounts(raw: list[dict]) -> pd.DataFrame:
    rows = [
        (a["account_id"], a["name"], _account_type(str(a["type"]), a.get("subtype") and str(a["subtype"])),
         "Plaid Sandbox", float(a["balances"]["current"] or 0))
        for a in raw
    ]
    return pd.DataFrame(rows, columns=["id", "name", "type", "institution", "balance"])


def normalize_transactions(raw: list[dict]) -> pd.DataFrame:
    rows = []
    for t in raw:
        primary = (t.get("personal_finance_category") or {}).get("primary")
        rows.append((pd.Timestamp(t["date"]), t["account_id"], t.get("merchant_name") or t["name"],
                     PLAID_CATEGORIES.get(primary, "Other"), float(t["amount"])))
    tx = pd.DataFrame(rows, columns=["date", "account_id", "merchant", "category", "amount"])
    tx["date"] = pd.to_datetime(tx["date"])
    return tx.sort_values("date", ascending=False, kind="stable").reset_index(drop=True)


class PlaidSandboxBank:
    def __init__(self, client_id: str, secret: str):
        self.client_id = client_id
        self.secret = secret
        self.client = None
        self.access_token = None

    def connect(self) -> None:
        # Imported here so the app still runs on the fake bank if plaid isn't installed
        import plaid
        from plaid.api import plaid_api
        from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
        from plaid.model.products import Products
        from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest

        config = plaid.Configuration(host=plaid.Environment.Sandbox,
                                     api_key={"clientId": self.client_id, "secret": self.secret})
        self.client = plaid_api.PlaidApi(plaid.ApiClient(config))
        public = self.client.sandbox_public_token_create(SandboxPublicTokenCreateRequest(
            institution_id=SANDBOX_INSTITUTION, initial_products=[Products("transactions")]))
        exchange = self.client.item_public_token_exchange(
            ItemPublicTokenExchangeRequest(public_token=public["public_token"]))
        self.access_token = exchange["access_token"]

    def get_accounts(self) -> pd.DataFrame:
        from plaid.model.accounts_get_request import AccountsGetRequest

        response = self.client.accounts_get(AccountsGetRequest(access_token=self.access_token))
        return normalize_accounts(response.to_dict()["accounts"])

    def get_transactions(self, days: int = 90) -> pd.DataFrame:
        from plaid.model.transactions_sync_request import TransactionsSyncRequest
        from plaid.model.transactions_sync_request_options import TransactionsSyncRequestOptions

        added, cursor = [], None
        for _ in range(10):
            request = {"access_token": self.access_token,
                       "options": TransactionsSyncRequestOptions(days_requested=max(days, 30))}
            if cursor:
                request["cursor"] = cursor
            page = self.client.transactions_sync(TransactionsSyncRequest(**request)).to_dict()
            added += page["added"]
            cursor = page["next_cursor"]
            if page["has_more"]:
                continue
            if added:
                break
            time.sleep(2)  # a brand-new sandbox item needs a moment to build its history
        tx = normalize_transactions(added)
        return tx[tx["date"] >= pd.Timestamp(date.today() - timedelta(days=days))]

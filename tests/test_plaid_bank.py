from datetime import date

from money import plaid_bank

RAW_ACCOUNTS = [
    {"account_id": "a1", "name": "Plaid Checking", "type": "depository", "subtype": "checking",
     "balances": {"current": 110.0, "available": 100.0}},
    {"account_id": "a2", "name": "Plaid Saving", "type": "depository", "subtype": "savings",
     "balances": {"current": 210.0, "available": 200.0}},
    {"account_id": "a3", "name": "Plaid Credit Card", "type": "credit", "subtype": "credit card",
     "balances": {"current": 410.0, "available": None}},
    {"account_id": "a4", "name": "Plaid IRA", "type": "investment", "subtype": "ira",
     "balances": {"current": 320.76, "available": None}},
]

RAW_TRANSACTIONS = [
    {"date": date(2026, 10, 20), "account_id": "a1", "name": "SparkFun", "merchant_name": "SparkFun",
     "amount": 89.4, "personal_finance_category": {"primary": "GENERAL_MERCHANDISE"}},
    {"date": date(2026, 10, 19), "account_id": "a3", "name": "McDonald's #3322", "merchant_name": None,
     "amount": 12.0, "personal_finance_category": {"primary": "FOOD_AND_DRINK"}},
    {"date": date(2026, 10, 18), "account_id": "a1", "name": "INTRST PYMNT", "merchant_name": None,
     "amount": -4.22, "personal_finance_category": {"primary": "INCOME"}},
    {"date": date(2026, 10, 17), "account_id": "a1", "name": "Mystery", "merchant_name": None,
     "amount": 5.0, "personal_finance_category": None},
]


def test_normalize_accounts_maps_types():
    accounts = plaid_bank.normalize_accounts(RAW_ACCOUNTS)
    assert list(accounts.columns) == ["id", "name", "type", "institution", "balance"]
    assert list(accounts["type"]) == ["checking", "savings", "credit", "investment"]
    assert list(accounts["balance"]) == [110.0, 210.0, 410.0, 320.76]


def test_normalize_transactions_maps_categories_and_keeps_sign():
    tx = plaid_bank.normalize_transactions(RAW_TRANSACTIONS)
    assert list(tx.columns) == ["date", "account_id", "merchant", "category", "amount"]
    assert list(tx["category"]) == ["Shopping", "Dining", "Income", "Other"]
    assert list(tx["merchant"]) == ["SparkFun", "McDonald's #3322", "INTRST PYMNT", "Mystery"]
    assert list(tx["amount"]) == [89.4, 12.0, -4.22, 5.0]
    assert str(tx["date"].dtype).startswith("datetime64")


class FakePlaidApi:
    def __init__(self):
        self.requests = []

    def link_token_create(self, request):
        self.requests.append(request)
        return {"link_token": "link-sandbox-123"}

    def item_public_token_exchange(self, request):
        self.requests.append(request)
        return {"access_token": "access-sandbox-abc"}


def test_create_link_token_uses_session_user():
    api = FakePlaidApi()
    bank = plaid_bank.PlaidSandboxBank("id", "secret", api=api)
    assert bank.create_link_token("session-42") == "link-sandbox-123"
    request = api.requests[0]
    assert request.user.client_user_id == "session-42"
    assert request.client_name == "Sensible"


def test_exchange_public_token_keeps_access_token_on_the_bank():
    api = FakePlaidApi()
    bank = plaid_bank.PlaidSandboxBank("id", "secret", api=api)
    assert bank.exchange_public_token("public-sandbox-xyz") == "access-sandbox-abc"
    assert bank.access_token == "access-sandbox-abc"
    assert api.requests[0].public_token == "public-sandbox-xyz"


def test_normalize_transactions_empty():
    tx = plaid_bank.normalize_transactions([])
    assert tx.empty
    assert list(tx.columns) == ["date", "account_id", "merchant", "category", "amount"]

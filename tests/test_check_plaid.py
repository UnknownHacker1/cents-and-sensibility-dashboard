from api.check_plaid import check
from api.settings import Settings
from money import plaid_bank


def settings(client_id="id-123", secret="sandbox-secret-xyz"):
    return Settings(secret_key=None, app_password=None, plaid_client_id=client_id, plaid_secret=secret,
                    cookie_secure=False)


class WorkingBank:
    def __init__(self, client_id, secret):
        self.access_token = None

    def create_link_token(self, user_id):
        return "link-sandbox-1"

    def connect(self):
        self.access_token = "access-sandbox-SECRET"

    def get_accounts(self):
        return plaid_bank.normalize_accounts([
            {"account_id": "a1", "name": "Plaid Checking", "type": "depository", "subtype": "checking",
             "balances": {"current": 110.0}},
            {"account_id": "a2", "name": "Plaid Saving", "type": "depository", "subtype": "savings",
             "balances": {"current": 210.0}}])

    def get_transactions(self, days=90):
        return plaid_bank.normalize_transactions([
            {"date": "2026-10-01", "account_id": "a1", "name": "Uber", "merchant_name": "Uber", "amount": 6.33,
             "personal_finance_category": {"primary": "TRANSPORTATION"}},
            {"date": "2026-10-20", "account_id": "a1", "name": "SparkFun", "merchant_name": "SparkFun",
             "amount": 89.4, "personal_finance_category": {"primary": "GENERAL_MERCHANDISE"}}])


class RejectingBank(WorkingBank):
    def create_link_token(self, user_id):
        error = Exception("boom")
        error.body = '{"error_code": "INVALID_API_KEYS", "error_message": "invalid client_id or secret provided"}'
        raise error


def test_no_keys_says_where_to_put_them():
    ok, lines = check(settings(client_id=None, secret=None), make_bank=WorkingBank)
    assert not ok
    assert any(".env" in line and "PLAID_CLIENT_ID" in line for line in lines)


def test_working_keys_report_accounts_and_transactions_without_leaking_secrets():
    ok, lines = check(settings(), make_bank=WorkingBank)
    text = "\n".join(lines)
    assert ok
    assert "2 accounts" in text and "Plaid Checking" in text
    assert "2 transactions" in text and "Oct 01" in text and "Oct 20" in text
    for secret in ("sandbox-secret-xyz", "access-sandbox-SECRET", "id-123"):
        assert secret not in text


def test_rejected_keys_name_the_plaid_error():
    ok, lines = check(settings(), make_bank=RejectingBank)
    assert not ok
    assert any("INVALID_API_KEYS" in line for line in lines)

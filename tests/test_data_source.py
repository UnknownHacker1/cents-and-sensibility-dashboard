from money import data_source, plaid_bank


def test_no_keys_uses_fake_bank():
    accounts, tx, label = data_source.load_bank({})
    assert "Fake" in label
    assert len(accounts) == 5
    assert not tx.empty


def test_plaid_failure_falls_back_to_fake(monkeypatch):
    def broken_connect(self):
        raise RuntimeError("INVALID_API_KEYS")

    monkeypatch.setattr(plaid_bank.PlaidSandboxBank, "connect", broken_connect)
    accounts, tx, label = data_source.load_bank({"PLAID_CLIENT_ID": "id", "PLAID_SECRET": "secret"})
    assert "Fake" in label
    assert "INVALID_API_KEYS" in label
    assert len(accounts) == 5


def test_plaid_api_error_shows_error_code_not_headers(monkeypatch):
    class FakeApiException(Exception):
        body = '{"error_code": "INVALID_API_KEYS", "error_message": "invalid client_id or secret provided"}'

    def broken_connect(self):
        raise FakeApiException("Status Code: 400\nHTTP response headers: lots of noise")

    monkeypatch.setattr(plaid_bank.PlaidSandboxBank, "connect", broken_connect)
    _, _, label = data_source.load_bank({"PLAID_CLIENT_ID": "id", "PLAID_SECRET": "secret"})
    assert label == "Fake bank (Plaid failed: INVALID_API_KEYS: invalid client_id or secret provided)"


def test_plaid_success_is_labeled(monkeypatch):
    monkeypatch.setattr(plaid_bank.PlaidSandboxBank, "connect", lambda self: None)
    monkeypatch.setattr(plaid_bank.PlaidSandboxBank, "get_accounts",
                        lambda self: plaid_bank.normalize_accounts([]))
    monkeypatch.setattr(plaid_bank.PlaidSandboxBank, "get_transactions",
                        lambda self, days=90: plaid_bank.normalize_transactions([]))
    _, _, label = data_source.load_bank({"PLAID_CLIENT_ID": "id", "PLAID_SECRET": "secret"})
    assert label == "Plaid Sandbox"

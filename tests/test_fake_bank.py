from datetime import date, timedelta

import pandas as pd

from money import fake_bank

TODAY = date(2026, 10, 23)


def test_accounts_has_five_with_extra_account():
    accounts = fake_bank.get_accounts()
    assert len(accounts) == 5
    assert "Cash App" in set(accounts["name"])
    assert set(accounts["type"]) <= {"checking", "savings", "credit", "investment"}
    assert (accounts["balance"] >= 0).all()


def test_transactions_deterministic():
    a = fake_bank.get_transactions(today=TODAY, seed=7)
    b = fake_bank.get_transactions(today=TODAY, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_transactions_within_window():
    tx = fake_bank.get_transactions(today=TODAY, days=90)
    assert list(tx.columns) == ["date", "account_id", "merchant", "category", "amount"]
    assert tx["date"].min() >= pd.Timestamp(TODAY - timedelta(days=90))
    assert tx["date"].max() <= pd.Timestamp(TODAY)
    assert set(tx["category"]) <= set(fake_bank.CATEGORIES)
    assert set(tx["account_id"]) <= set(fake_bank.get_accounts()["id"])


def test_planted_unusual_charges_present():
    tx = fake_bank.get_transactions(today=TODAY)
    recent = tx[tx["date"] > pd.Timestamp(TODAY - timedelta(days=14))]
    assert ((recent["merchant"] == "ElectroMart") & (recent["amount"] == 489.99)).any()
    assert ((recent["category"] == "Dining") & (recent["amount"] > 150)).any()


def test_has_recurring_subscriptions():
    tx = fake_bank.get_transactions(today=TODAY)
    spotify = tx[(tx["merchant"] == "Spotify") & (tx["amount"] == 11.99)]
    assert spotify["date"].dt.to_period("M").nunique() >= 3

from datetime import date

import pandas as pd
import pytest

from money import analytics

COLUMNS = ["date", "account_id", "merchant", "category", "amount"]


def make_tx(rows):
    tx = pd.DataFrame(rows, columns=COLUMNS)
    tx["date"] = pd.to_datetime(tx["date"])
    return tx


EMPTY = make_tx([])
OCT = pd.Period("2026-10", "M")


def test_spending_by_category_excludes_income_and_transfers():
    tx = make_tx([
        ("2026-10-02", "chk", "Kroger", "Groceries", 40.0),
        ("2026-10-03", "chk", "Kroger", "Groceries", 10.0),
        ("2026-10-04", "chk", "Chipotle", "Dining", 12.0),
        ("2026-10-05", "chk", "Payroll", "Income", -600.0),
        ("2026-10-06", "chk", "To Savings", "Transfer", 150.0),
        ("2026-10-07", "chk", "Refund", "Shopping", -20.0),
    ])
    totals = analytics.spending_by_category(tx, OCT)
    assert totals.to_dict() == {"Groceries": 50.0, "Dining": 12.0}
    assert list(totals.index) == ["Groceries", "Dining"]


def test_month_summary_change_pct():
    tx = make_tx([
        ("2026-09-10", "chk", "Kroger", "Groceries", 100.0),
        ("2026-10-10", "chk", "Kroger", "Groceries", 150.0),
        ("2026-10-11", "chk", "Payroll", "Income", -600.0),
    ])
    summary = analytics.month_summary(tx, OCT)
    assert summary["spent"] == 150.0
    assert summary["income"] == 600.0
    assert summary["net"] == 450.0
    assert summary["top_category"] == "Groceries"
    assert summary["change_pct"] == pytest.approx(50.0)


def test_month_summary_change_is_none_when_last_month_zero():
    tx = make_tx([("2026-10-10", "chk", "Kroger", "Groceries", 150.0)])
    assert analytics.month_summary(tx, OCT)["change_pct"] is None


def test_months_newest_first():
    tx = make_tx([
        ("2026-08-10", "chk", "A", "Dining", 1.0),
        ("2026-10-10", "chk", "A", "Dining", 1.0),
        ("2026-09-10", "chk", "A", "Dining", 1.0),
    ])
    assert analytics.months(tx) == [OCT, pd.Period("2026-09", "M"), pd.Period("2026-08", "M")]


def test_net_worth_subtracts_credit():
    accounts = pd.DataFrame(
        [("a", "Checking", "checking", "X", 1000.0), ("b", "Card", "credit", "X", 300.0),
         ("c", "IRA", "investment", "X", 500.0)],
        columns=["id", "name", "type", "institution", "balance"],
    )
    assert analytics.net_worth(accounts) == 1200.0


def test_subscription_found_for_monthly_equal_charges():
    tx = make_tx([
        ("2026-08-05", "cc", "Spotify", "Subscriptions", 11.99),
        ("2026-09-05", "cc", "Spotify", "Subscriptions", 11.99),
        ("2026-10-05", "cc", "Spotify", "Subscriptions", 11.99),
    ])
    subs = analytics.find_subscriptions(tx)
    assert list(subs["merchant"]) == ["Spotify"]
    row = subs.iloc[0]
    assert row["amount"] == 11.99
    assert row["months_seen"] == 3
    assert row["last_charged"] == pd.Timestamp("2026-10-05")
    assert row["next_expected"] == pd.Timestamp("2026-11-04")


def test_subscription_ignores_variable_and_one_off_charges():
    tx = make_tx([
        ("2026-08-03", "cc", "Kroger", "Groceries", 41.20),
        ("2026-09-03", "cc", "Kroger", "Groceries", 77.85),
        ("2026-10-03", "cc", "Kroger", "Groceries", 52.10),
        ("2026-10-09", "cc", "ElectroMart", "Shopping", 489.99),
        # same amount but weekly, not monthly
        ("2026-10-01", "cc", "Bean There", "Coffee", 5.00),
        ("2026-10-08", "cc", "Bean There", "Coffee", 5.00),
        ("2026-10-15", "cc", "Bean There", "Coffee", 5.00),
    ])
    assert analytics.find_subscriptions(tx).empty


def test_rent_is_a_bill_not_a_subscription():
    tx = make_tx([
        ("2026-08-01", "chk", "Maple Court Apartments", "Housing", 725.0),
        ("2026-09-01", "chk", "Maple Court Apartments", "Housing", 725.0),
        ("2026-10-01", "chk", "Maple Court Apartments", "Housing", 725.0),
    ])
    assert analytics.find_subscriptions(tx).empty


def dining_history():
    return [
        ("2026-09-01", "cc", "Chipotle", "Dining", 12.0),
        ("2026-09-08", "cc", "Taco Bell", "Dining", 10.0),
        ("2026-09-15", "cc", "Chipotle", "Dining", 14.0),
    ]


def test_unusual_flags_three_times_category_median():
    tx = make_tx(dining_history() + [("2026-10-20", "cc", "Chipotle", "Dining", 60.0)])
    alerts = analytics.find_unusual_charges(tx, today=date(2026, 10, 23))
    assert list(alerts["amount"]) == [60.0]
    assert "5.0x" in alerts.iloc[0]["reason"]


def test_unusual_skips_rule_one_without_enough_history():
    tx = make_tx([
        ("2026-09-01", "cc", "Chipotle", "Dining", 12.0),
        ("2026-10-20", "cc", "Chipotle", "Dining", 90.0),
    ])
    assert analytics.find_unusual_charges(tx, today=date(2026, 10, 23)).empty


def test_unusual_flags_new_merchant_big_amount():
    tx = make_tx(dining_history() + [("2026-10-20", "cc", "ElectroMart", "Shopping", 489.99)])
    alerts = analytics.find_unusual_charges(tx, today=date(2026, 10, 23))
    assert list(alerts["merchant"]) == ["ElectroMart"]
    assert "first time" in alerts.iloc[0]["reason"]


def test_unusual_never_flags_income_or_transfers():
    tx = make_tx(dining_history() + [
        ("2026-10-20", "chk", "Big Bonus", "Income", -2000.0),
        ("2026-10-21", "chk", "Brokerage Deposit", "Transfer", 900.0),
    ])
    assert analytics.find_unusual_charges(tx, today=date(2026, 10, 23)).empty


def test_every_function_handles_empty_transactions():
    assert analytics.spending_by_category(EMPTY, OCT).empty
    assert analytics.months(EMPTY) == []
    summary = analytics.month_summary(EMPTY, OCT)
    assert summary["spent"] == 0.0 and summary["top_category"] is None
    assert summary["change_pct"] is None
    assert analytics.find_subscriptions(EMPTY).empty
    assert analytics.find_unusual_charges(EMPTY, today=date(2026, 10, 23)).empty


def test_goal_progress_clamps():
    assert analytics.goal_progress(50, 0) == 0.0
    assert analytics.goal_progress(250, 1000) == 0.25
    assert analytics.goal_progress(5000, 1000) == 1.0
    assert analytics.goal_progress(-5, 100) == 0.0


def test_fake_bank_alerts_catch_both_planted_charges():
    from money import fake_bank

    today = date(2026, 10, 23)
    alerts = analytics.find_unusual_charges(fake_bank.get_transactions(today=today), today=today)
    assert {"ElectroMart", "The Capital Grille"} <= set(alerts["merchant"])
    assert len(alerts) <= 4

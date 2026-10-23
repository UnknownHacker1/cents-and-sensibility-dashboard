"""Number crunching for the dashboard. Pure functions: DataFrames in, answers out.

Every function works on the shared data model (see money/fake_bank.py) and on
an empty DataFrame without crashing.
"""

from datetime import date, timedelta

import pandas as pd

NOT_SPENDING = {"Income", "Transfer"}


def spending(tx: pd.DataFrame) -> pd.DataFrame:
    """Money out that counts as spending: no paychecks, no moving money between your own accounts."""
    return tx[(tx["amount"] > 0) & ~tx["category"].isin(NOT_SPENDING)]


def months(tx: pd.DataFrame) -> list[pd.Period]:
    return sorted(tx["date"].dt.to_period("M").unique(), reverse=True)


def _in_month(tx: pd.DataFrame, month: pd.Period) -> pd.DataFrame:
    return tx[tx["date"].dt.to_period("M") == month]


def spending_by_category(tx: pd.DataFrame, month: pd.Period | None = None) -> pd.Series:
    out = spending(tx)
    if month is not None:
        out = _in_month(out, month)
    totals = out.groupby("category")["amount"].sum().round(2)
    return totals.sort_values(ascending=False)


def month_summary(tx: pd.DataFrame, month: pd.Period) -> dict:
    by_category = spending_by_category(tx, month)
    spent = round(float(by_category.sum()), 2)
    this_month = _in_month(tx, month)
    income = round(float(-this_month.loc[this_month["category"] == "Income", "amount"].sum()), 2) + 0.0  # no -0.0
    last_spent = float(spending_by_category(tx, month - 1).sum())
    return {
        "spent": spent,
        "income": income,
        "net": round(income - spent, 2),
        "top_category": by_category.index[0] if len(by_category) else None,
        "change_pct": (spent - last_spent) / last_spent * 100 if last_spent else None,
    }


def pace(tx: pd.DataFrame, month: pd.Period, today: date | None = None) -> list[dict]:
    """Running total of spending, day by day, for this month and the one before.

    Days that haven't happened yet are None for this month, and days the previous
    month didn't have (Sept 31) are None for last month, so a chart can stop the line.
    """
    today = today or date.today()
    spent = spending(tx)

    def daily(m: pd.Period) -> pd.Series:
        rows = _in_month(spent, m)
        return rows.groupby(rows["date"].dt.day)["amount"].sum()

    this_days, last_days = daily(month), daily(month - 1)
    rows, this_total, last_total = [], 0.0, 0.0
    for day in range(1, month.days_in_month + 1):
        this_total += float(this_days.get(day, 0.0))
        last_total += float(last_days.get(day, 0.0))
        rows.append({
            "day": day,
            "this_month": None if date(month.year, month.month, day) > today else round(this_total, 2),
            "last_month": round(last_total, 2) if day <= (month - 1).days_in_month else None,
        })
    return rows


def net_worth(accounts: pd.DataFrame) -> float:
    owed = accounts["type"] == "credit"
    return round(float(accounts.loc[~owed, "balance"].sum() - accounts.loc[owed, "balance"].sum()), 2)


def find_subscriptions(tx: pd.DataFrame) -> pd.DataFrame:
    """Same merchant, same amount, roughly once a month, at least 2 different months.

    Rent and utilities (Housing) repeat too, but they are bills, not subscriptions.
    """
    columns = ["merchant", "amount", "months_seen", "last_charged", "next_expected"]
    rows = []
    spent = spending(tx)
    spent = spent[spent["category"] != "Housing"]
    for (merchant, amount), group in spent.groupby(["merchant", spent["amount"].round(2)]):
        dates = group["date"].sort_values()
        months_seen = dates.dt.to_period("M").nunique()
        if months_seen < 2:
            continue
        if not 25 <= dates.diff().dropna().dt.days.median() <= 35:
            continue
        last = dates.iloc[-1]
        rows.append((merchant, amount, months_seen, last, last + timedelta(days=30)))
    return pd.DataFrame(rows, columns=columns).sort_values("amount", ascending=False, ignore_index=True)


def find_unusual_charges(tx: pd.DataFrame, today: date | None = None, window_days: int = 14) -> pd.DataFrame:
    """Flag recent charges that look off.

    Rule 1: at least 3x the usual (median) charge in that category, and at least $50.
            Only used when the category has 3 or more earlier charges to compare with.
    Rule 2: a merchant you have never paid before, charging $200 or more.
    """
    columns = ["date", "merchant", "category", "amount", "reason"]
    cutoff = pd.Timestamp((today or date.today()) - timedelta(days=window_days))
    spent = spending(tx)
    before, recent = spent[spent["date"] <= cutoff], spent[spent["date"] > cutoff]
    known_merchants = set(tx.loc[tx["date"] <= cutoff, "merchant"])
    usual = before.groupby("category")["amount"].agg(["median", "count"])

    rows = []
    for charge in recent.itertuples():
        reasons = []
        if charge.category in usual.index and usual.at[charge.category, "count"] >= 3:
            median = usual.at[charge.category, "median"]
            if charge.amount >= 50 and charge.amount >= 3 * median:
                reasons.append(f"{charge.amount / median:.1f}x your usual {charge.category} charge (${median:,.2f})")
        if charge.merchant not in known_merchants and charge.amount >= 200:
            reasons.append(f"first time paying {charge.merchant}, and it's ${charge.amount:,.2f}")
        if reasons:
            rows.append((charge.date, charge.merchant, charge.category, charge.amount, "; ".join(reasons)))
    return pd.DataFrame(rows, columns=columns).sort_values("date", ascending=False, ignore_index=True)


def goal_progress(saved: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return min(max(saved / target, 0.0), 1.0)

"""A pretend bank full of fake data, so nobody ever types in a real login.

Amounts follow Plaid's sign convention, so Event 2 can swap in the sandbox bank
without touching the rest of the app:
    amount > 0  money leaving the account (spending)
    amount < 0  money coming in (paychecks, refunds)
"""

import random
from datetime import date, timedelta

import pandas as pd

CATEGORIES = [
    "Income", "Housing", "Groceries", "Dining", "Coffee", "Transport", "Shopping",
    "Entertainment", "Subscriptions", "Health", "Personal", "Travel", "Transfer",
]

ACCOUNTS = [
    # id, name, type, institution, balance (credit balance = money owed)
    ("chk", "Everyday Checking", "checking", "Peachtree Credit Union", 1842.37),
    ("sav", "High-Yield Savings", "savings", "Peachtree Credit Union", 3250.00),
    ("cc", "Student Rewards Card", "credit", "Orbit Bank", 612.48),
    ("inv", "Roth IRA", "investment", "Brightvest", 1480.20),
    ("cash", "Cash App", "checking", "Cash App", 86.15),  # Silver bonus: one more fake account
]

# merchant, amount, day of month, account
SUBSCRIPTIONS = [
    ("Spotify", 11.99, 5, "cc"),
    ("Planet Fitness", 24.99, 8, "cc"),
    ("Netflix", 15.49, 12, "cc"),
    ("iCloud+", 2.99, 20, "cc"),
]

# category: (daily chance, merchants, min amount, max amount)
EVERYDAY = {
    "Coffee": (0.45, ["Starbucks", "Bean There Cafe"], 4.25, 7.80),
    "Dining": (0.30, ["Chipotle", "Waffle House", "Panda Express", "Taco Bell"], 8.00, 28.00),
    "Transport": (0.20, ["Uber", "Shell"], 9.00, 42.00),
    "Shopping": (0.15, ["Amazon", "Target"], 15.00, 80.00),
    "Entertainment": (0.05, ["AMC Theatres", "Steam"], 9.99, 28.00),
    "Personal": (0.03, ["Great Clips", "CVS"], 12.00, 26.00),
}

PAYDAY_ANCHOR = date(2026, 1, 2)  # a Friday; paychecks land every 2 weeks from here


def get_accounts() -> pd.DataFrame:
    return pd.DataFrame(ACCOUNTS, columns=["id", "name", "type", "institution", "balance"])


def get_transactions(today: date | None = None, days: int = 90, seed: int = 42) -> pd.DataFrame:
    today = today or date.today()
    rng = random.Random(seed)
    rows = []

    def add(day, account, merchant, category, amount):
        rows.append((pd.Timestamp(day), account, merchant, category, round(amount, 2)))

    for offset in range(days):
        day = today - timedelta(days=offset)

        if (day - PAYDAY_ANCHOR).days % 14 == 0:
            add(day, "chk", "Campus Job Payroll", "Income", -980.00)
        if day.day == 1:
            add(day, "chk", "Maple Court Apartments", "Housing", 725.00)
        if day.day == 2:
            add(day, "chk", "Transfer to Savings", "Transfer", 150.00)
            add(day, "sav", "Transfer from Checking", "Transfer", -150.00)
        if day.day == 15:
            add(day, "chk", "Georgia Power", "Housing", rng.uniform(48, 72))
        for merchant, amount, dom, account in SUBSCRIPTIONS:
            if day.day == dom:
                add(day, account, merchant, "Subscriptions", amount)

        if day.weekday() in (2, 6) and rng.random() < 0.8:  # Wednesday and Sunday shops
            add(day, rng.choice(["chk", "cc"]), rng.choice(["Kroger", "Publix", "Aldi"]),
                "Groceries", rng.uniform(25, 95))
        for category, (chance, merchants, low, high) in EVERYDAY.items():
            if rng.random() < chance:
                add(day, rng.choice(["cc", "cc", "chk"]), rng.choice(merchants),
                    category, rng.uniform(low, high))
        if rng.random() < 0.06:
            add(day, "cash", "Cash App Pay - Food Truck", "Dining", rng.uniform(9, 14))

    # Planted surprises so the alerts panel has something to catch
    add(today - timedelta(days=3), "cc", "ElectroMart", "Shopping", 489.99)
    add(today - timedelta(days=6), "cc", "The Capital Grille", "Dining", 186.40)

    tx = pd.DataFrame(rows, columns=["date", "account_id", "merchant", "category", "amount"])
    return tx.sort_values("date", ascending=False, kind="stable").reset_index(drop=True)

"""Money Brain: answers questions about your money from your own numbers.

Event 1 version: no AI model yet. A keyword router picks what the question is
about and answers from analytics. In Event 3 the AI Prompter swaps the router
for an LLM call: send RULES as the system prompt and build_context() as the
facts, so the model answers from real numbers instead of guessing.
"""

import re
from dataclasses import dataclass
from datetime import date

import pandas as pd

from money import analytics

RULES = [
    "Always answer from the user's own numbers, and show the numbers.",
    "Never move, send, or transfer money, or pay bills.",
    "Never guarantee returns or tell the user what to buy or sell. Educational only, not financial advice.",
    "Never ask for or repeat card numbers, SSNs, passwords, or bank logins. If one is pasted, refuse and warn.",
    "If the data cannot answer the question, say so plainly instead of guessing.",
]

EXAMPLE_QUESTIONS = [
    "Where did my money go this month?",
    "How much am I paying for subscriptions?",
    "Did anything weird hit my card recently?",
    "Am I spending more than last month?",
    "How much did I spend on dining out?",
]

# words people use -> our category names
CATEGORY_WORDS = {
    "coffee": "Coffee", "starbucks": "Coffee",
    "dining": "Dining", "eating out": "Dining", "restaurant": "Dining", "takeout": "Dining",
    "grocer": "Groceries", "food shopping": "Groceries",
    "rent": "Housing", "housing": "Housing", "utilit": "Housing",
    "transport": "Transport", "uber": "Transport", "gas": "Transport", "rides": "Transport",
    "shopping": "Shopping", "amazon": "Shopping", "clothes": "Shopping",
    "entertainment": "Entertainment", "movie": "Entertainment", "games": "Entertainment",
    "health": "Health", "gym": "Subscriptions",
    "personal": "Personal", "haircut": "Personal", "travel": "Travel",
}

SENSITIVE = re.compile(r"(?:\d[ -]?){13,19}|\b\d{3}-\d{2}-\d{4}\b|\bpassword\b|\bpin\b", re.I)
MOVE_MONEY = re.compile(
    r"^(?:please\s+|can you\s+|could you\s+|would you\s+|go ahead and\s+)*"
    r"(?:move|send|transfer|wire|pay|withdraw|deposit|venmo|zelle)\b"
    r"|\b(?:move|send|transfer|wire|pay|withdraw|deposit)\s+\$?\d", re.I)  # or "... send $50 ..." mid-sentence
INJECTION = re.compile(
    r"\b(?:ignore|forget|disregard|bypass|override)\b[^.?!]{0,40}\b(?:rules|instructions|guardrails|prompt)\b"
    r"|\byou are now\b", re.I)
ADVICE = re.compile(
    r"guarantee|should i (?:buy|sell|invest)|invest in|which stock|what stock|best stock"
    r"|stock to buy|crypto|bitcoin|get rich", re.I)

INTENTS = [  # checked in order, first match wins
    ("unusual", re.compile(r"unusual|weird|suspicious|fraud|strange|odd|alert", re.I)),
    ("subscriptions", re.compile(r"subscri|recurring", re.I)),
    ("compare", re.compile(r"last month|compare|more than|less than|trend", re.I)),
    ("balance", re.compile(r"balance|net worth|how much (?:money )?do i have|across all", re.I)),
    ("savings_tip", re.compile(r"\bsav(?:e|ing)|cut back|budget", re.I)),
]


@dataclass
class Answer:
    text: str
    intent: str
    refused: bool = False


def _money(x: float) -> str:
    return f"${x:,.2f}"


def _month(today: date | None) -> pd.Period:
    return pd.Period(today or date.today(), "M")


def answer(question: str, accounts: pd.DataFrame, tx: pd.DataFrame, today: date | None = None) -> Answer:
    q = question.strip()
    month = _month(today)

    if SENSITIVE.search(q):
        return Answer("Please don't share card numbers, SSNs, passwords or PINs, here or with any app. "
                      "I didn't save it. Delete it from anywhere else you pasted it.", "refuse_sensitive", True)
    if INJECTION.search(q):
        return Answer("My rules don't change based on how a question is worded. I can read and explain your "
                      "numbers, nothing more.", "refuse_injection", True)
    if MOVE_MONEY.search(q):
        return Answer("I can't move, send or transfer money or pay bills. I only read your numbers. "
                      "Do that in your bank's own app.", "refuse_money_movement", True)
    if ADVICE.search(q):
        return Answer("I can't guarantee returns or tell you what to buy or sell. That would be financial advice, "
                      "and this app is educational only. I can show what you spend and where you could save.",
                      "refuse_advice", True)

    for intent, pattern in INTENTS:
        if pattern.search(q):
            return HANDLERS[intent](accounts, tx, month, today)

    for word, category in CATEGORY_WORDS.items():
        if re.search(rf"\b{word}", q, re.I):  # word start only, so "different" is not "rent"
            return _category(tx, month, category)

    if re.search(r"where|spen[dt]|go\b|went|breakdown", q, re.I):
        return _where_money_went(accounts, tx, month, today)

    return Answer("I can answer things like: " + " / ".join(EXAMPLE_QUESTIONS), "help")


def _where_money_went(accounts, tx, month, today) -> Answer:
    by_category = analytics.spending_by_category(tx, month)
    if by_category.empty:
        return Answer(f"I see no spending in {month.strftime('%B')} yet.", "where_money_went")
    total = by_category.sum()
    top = ", ".join(f"{cat} {_money(amt)} ({amt / total:.0%})" for cat, amt in by_category.head(3).items())
    return Answer(f"You spent {_money(total)} in {month.strftime('%B')}. Biggest buckets: {top}.",
                  "where_money_went")


def _category(tx, month, category) -> Answer:
    spent = analytics.spending(tx)
    rows = spent[(spent["category"] == category) & (spent["date"].dt.to_period("M") == month)]
    if rows.empty:
        return Answer(f"No {category} spending in {month.strftime('%B')} so far.", "category")
    top = rows.groupby("merchant")["amount"].sum().sort_values(ascending=False)
    return Answer(f"{category} in {month.strftime('%B')}: {_money(rows['amount'].sum())} across {len(rows)} "
                  f"charges. Most went to {top.index[0]} ({_money(top.iloc[0])}).", "category")


def _subscriptions(accounts, tx, month, today) -> Answer:
    subs = analytics.find_subscriptions(tx)
    if subs.empty:
        return Answer("I don't see any subscriptions yet.", "subscriptions")
    items = ", ".join(f"{s.merchant} {_money(s.amount)}" for s in subs.itertuples())
    return Answer(f"You pay about {_money(subs['amount'].sum())} a month for {len(subs)} subscriptions: {items}.",
                  "subscriptions")


def _unusual(accounts, tx, month, today) -> Answer:
    alerts = analytics.find_unusual_charges(tx, today=today)
    if alerts.empty:
        return Answer("Nothing unusual in the last 14 days.", "unusual")
    items = " ".join(f"{a.date:%b %d}: {a.merchant} {_money(a.amount)} ({a.reason})." for a in alerts.itertuples())
    return Answer(f"{len(alerts)} charge(s) look off. {items} If you don't recognize one, call your bank.",
                  "unusual")


def _compare(accounts, tx, month, today) -> Answer:
    summary = analytics.month_summary(tx, month)
    if summary["change_pct"] is None:
        return Answer("I don't have last month's spending to compare with.", "compare")
    change = summary["change_pct"]
    direction = "more" if change > 0 else "less"
    return Answer(f"You've spent {_money(summary['spent'])} in {month.strftime('%B')}, {abs(change):.0f}% "
                  f"{direction} than {(month - 1).strftime('%B')}.", "compare")


def _balance(accounts, tx, month, today) -> Answer:
    parts = ", ".join(f"{a.name} {_money(a.balance)}{' owed' if a.type == 'credit' else ''}"
                      for a in accounts.itertuples())
    return Answer(f"Net worth: {_money(analytics.net_worth(accounts))}. {parts}.", "balance")


def _savings_tip(accounts, tx, month, today) -> Answer:
    by_category = analytics.spending_by_category(tx, month).drop(["Housing", "Subscriptions"], errors="ignore")
    if by_category.empty:
        return Answer("Not enough spending this month to suggest a cut.", "savings_tip")
    category, amount = by_category.index[0], by_category.iloc[0]
    return Answer(f"Your biggest flexible spend this month is {category} at {_money(amount)}. "
                  f"Cutting it by a quarter would free up about {_money(amount * 0.25)} a month.", "savings_tip")


HANDLERS = {
    "unusual": _unusual,
    "subscriptions": _subscriptions,
    "compare": _compare,
    "balance": _balance,
    "savings_tip": _savings_tip,
}


def build_context(accounts: pd.DataFrame, tx: pd.DataFrame, today: date | None = None) -> str:
    """Plain-text facts for the Event 3 LLM prompt. Only totals, never raw account numbers."""
    month = _month(today)
    summary = analytics.month_summary(tx, month)
    lines = [f"Net worth: {_money(analytics.net_worth(accounts))}"]
    lines += [f"Account {a.name} ({a.type}): {_money(a.balance)}" for a in accounts.itertuples()]
    lines.append(f"{month.strftime('%B %Y')}: spent {_money(summary['spent'])}, income {_money(summary['income'])}")
    lines += [f"Spent on {cat}: {_money(amt)}" for cat, amt in analytics.spending_by_category(tx, month).items()]
    lines += [f"Subscription {s.merchant}: {_money(s.amount)}/month" for s in analytics.find_subscriptions(tx).itertuples()]
    lines += [f"Alert {a.merchant} {_money(a.amount)}: {a.reason}"
              for a in analytics.find_unusual_charges(tx, today=today).itertuples()]
    return "\n".join(lines)

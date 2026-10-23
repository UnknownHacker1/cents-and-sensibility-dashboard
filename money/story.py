"""The sentence at the top of the dashboard: your month, in words.

Returns tokens instead of one string so the web app can highlight the numbers:
    {"text": "plain words"}  or  {"value": "$2,403.49", "kind": "spent"}
kinds: spent, change_up, change_down, category, alert
"""

from datetime import date

import pandas as pd

from money import analytics


def _money(x: float) -> str:
    return f"${x:,.2f}"


def month_story(tx: pd.DataFrame, month: pd.Period, today: date | None = None) -> list[dict]:
    today = today or date.today()
    current = month == pd.Period(today, "M")
    name, previous = month.strftime("%B"), (month - 1).strftime("%B")
    summary = analytics.month_summary(tx, month)

    if summary["spent"] == 0:
        return [{"text": f"Nothing spent in {name} yet." if current else f"Nothing spent in {name}."}]

    tokens = [
        {"text": f"So far in {name} you've spent " if current else f"In {name} you spent "},
        {"value": _money(summary["spent"]), "kind": "spent"},
    ]

    change = summary["change_pct"]
    if change is None:
        tokens.append({"text": "."})
    elif abs(change) < 1:
        tokens.append({"text": f", about the same as {previous}."})
    else:
        word, kind = ("more", "change_up") if change > 0 else ("less", "change_down")
        tokens += [{"text": ", "}, {"value": f"{abs(change):.0f}% {word}", "kind": kind},
                   {"text": f" than {previous}."}]

    by_category = analytics.spending_by_category(tx, month)
    tokens += [{"text": " "}, {"value": by_category.index[0], "kind": "category"},
               {"text": f" took the biggest share at {_money(by_category.iloc[0])}."}]

    if current:
        flagged = len(analytics.find_unusual_charges(tx, today=today))
        if flagged:
            tokens += [{"text": " "}, {"value": f"{flagged} charge{'s' if flagged > 1 else ''}", "kind": "alert"},
                       {"text": " look off." if flagged > 1 else " looks off."}]
        else:
            tokens.append({"text": " Nothing looks off."})
    return tokens

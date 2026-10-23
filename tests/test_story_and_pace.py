from datetime import date

import pandas as pd

from money import analytics, fake_bank, story

TODAY = date(2026, 10, 23)
TX = fake_bank.get_transactions(today=TODAY)
OCT, SEP = pd.Period("2026-10", "M"), pd.Period("2026-09", "M")


def joined(tokens):
    return "".join(t.get("text", t.get("value", "")) for t in tokens)


def test_pace_covers_every_day_and_is_cumulative():
    rows = analytics.pace(TX, SEP, today=TODAY)
    assert [r["day"] for r in rows] == list(range(1, 31))
    this = [r["this_month"] for r in rows]
    assert this == sorted(this)
    assert this[-1] == analytics.month_summary(TX, SEP)["spent"]


def test_pace_stops_this_month_after_today():
    rows = analytics.pace(TX, OCT, today=TODAY)
    assert len(rows) == 31
    assert rows[22]["this_month"] is not None  # Oct 23
    assert rows[23]["this_month"] is None      # Oct 24 hasn't happened
    assert rows[30]["last_month"] is None       # September has no day 31
    assert rows[29]["last_month"] == analytics.month_summary(TX, SEP)["spent"]


def test_pace_empty_transactions():
    rows = analytics.pace(TX.iloc[0:0], OCT, today=TODAY)
    assert rows[0] == {"day": 1, "this_month": 0.0, "last_month": 0.0}


def test_story_current_month_highlights_spend_change_and_alerts():
    tokens = story.month_story(TX, OCT, today=TODAY)
    text = joined(tokens)
    assert text.startswith("So far in October you've spent $2,403.49")
    kinds = {t["kind"]: t["value"] for t in tokens if "kind" in t}
    assert kinds["spent"] == "$2,403.49"
    assert kinds["change_up"] == "41% more"
    assert kinds["category"] == "Shopping"
    assert kinds["alert"] == "2 charges"


def test_story_past_month_uses_past_tense_and_no_alerts():
    tokens = story.month_story(TX, SEP, today=TODAY)
    text = joined(tokens)
    assert text.startswith("In September you spent $1,702.31")
    assert "alert" not in {t.get("kind") for t in tokens}


def test_story_empty_month():
    tokens = story.month_story(TX.iloc[0:0], OCT, today=TODAY)
    assert joined(tokens) == "Nothing spent in October yet."

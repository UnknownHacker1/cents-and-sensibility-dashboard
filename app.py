"""Sensible: one dashboard for your whole (fake) financial life.

Run it:  python -m streamlit run app.py
All the number crunching lives in the money/ folder. This file only draws the screen.
"""

from datetime import date

import pandas as pd
import streamlit as st

from money import analytics, assistant, data_source

TEAM_NAME = "Cents & Sensibility"  # TEAM TODO: change this to your team name
APP_NAME = "Sensible"
TAGLINE = "Your money, finally making sense."
CORAL = "#FF6B6B"
MINT = "#2EC4B6"

st.set_page_config(page_title=f"{APP_NAME} by {TEAM_NAME}", page_icon="🧠", layout="wide")


@st.cache_data(ttl=600, show_spinner="Opening the bank...")
def load():
    return data_source.load_bank()


accounts, tx, source = load()
today = date.today()


def money(x: float) -> str:
    return f"${x:,.2f}"


def md(text: str) -> str:
    """Streamlit reads $...$ as math, so escape dollar signs in any markdown text."""
    return text.replace("$", r"\$")


# ---------- Sidebar ----------
with st.sidebar:
    st.header("Filters")
    month_options = analytics.months(tx) or [pd.Period(today, "M")]
    month = st.selectbox("Month", month_options, format_func=lambda m: m.strftime("%B %Y"))
    picked = st.multiselect("Accounts", list(accounts["name"]), default=list(accounts["name"]))
    goal = st.number_input("Savings goal ($)", min_value=0, value=5000, step=250)
    st.divider()
    st.caption("Assistant rules")
    for i, rule in enumerate(assistant.RULES, 1):
        st.caption(f"{i}. {rule}")

accounts = accounts[accounts["name"].isin(picked)]
tx = tx[tx["account_id"].isin(accounts["id"])]
summary = analytics.month_summary(tx, month)
subs = analytics.find_subscriptions(tx)
alerts = analytics.find_unusual_charges(tx, today=today)

# ---------- Header ----------
st.title(f"🧠 {APP_NAME}")
st.markdown(f"**{TEAM_NAME}** · {TAGLINE}")
badge = "🟢" if source == "Plaid Sandbox" else "🧪"
st.caption(f"{badge} Data source: {source} · Fake data only. Educational, not financial advice.")

# ---------- Metric tiles ----------
change = summary["change_pct"]
tiles = st.columns(4)
tiles[0].metric("Net worth", money(analytics.net_worth(accounts)), border=True)
tiles[1].metric(f"Spent in {month.strftime('%B')}", money(summary["spent"]),
                delta=None if change is None else f"{change:+.0f}% vs last month",
                delta_color="inverse", border=True)
tiles[2].metric(f"Income in {month.strftime('%B')}", money(summary["income"]),
                delta=f"{money(abs(summary['net']))} {'left over' if summary['net'] >= 0 else 'short'}",
                delta_color="normal" if summary["net"] >= 0 else "inverse", border=True)
tiles[3].metric("Subscriptions / month", money(subs["amount"].sum()), help="Repeating charges, not rent", border=True)

# ---------- Spending chart + alerts ----------
left, right = st.columns([3, 2])
with left, st.container(border=True):
    st.subheader("Where the money went")
    by_category = analytics.spending_by_category(tx, month)
    if by_category.empty:
        st.info("No spending this month yet.")
    else:
        chart = by_category.rename("Spent").rename_axis("Category").reset_index()
        st.bar_chart(chart, x="Category", y="Spent", color=MINT, horizontal=True, sort="-Spent")

with right, st.container(border=True):
    st.subheader(f"Alerts ({len(alerts)})")
    if alerts.empty:
        st.success("Nothing unusual in the last 14 days.")
    for a in alerts.itertuples():
        st.markdown(
            f"<div style='border-left:4px solid {CORAL};padding:6px 10px;margin-bottom:8px;'>"
            f"<b>{a.merchant}</b> · {money(a.amount)} · {a.date:%b %d}<br>"
            f"<span style='font-size:0.9em;opacity:0.8'>{a.reason}</span></div>",
            unsafe_allow_html=True,
        )

# ---------- Ask Money Brain ----------
with st.container(border=True):
    st.subheader("Ask Money Brain")
    st.caption("Answers come from your numbers. It will never move money or give investment advice.")
    if "chat" not in st.session_state:
        st.session_state.chat = []

    clicked = None
    with st.container(horizontal=True, wrap=True):
        for question in assistant.EXAMPLE_QUESTIONS:
            if st.button(question, width="content"):
                clicked = question

    with st.form("ask", clear_on_submit=True):
        typed = st.text_input("Your question", placeholder="Where did my money go this month?")
        sent = st.form_submit_button("Ask")

    question = clicked or (typed if sent and typed.strip() else None)
    if question:
        st.session_state.chat.insert(0, (question, assistant.answer(question, accounts, tx, today=today)))

    for question, reply in st.session_state.chat[:6]:
        with st.chat_message("user"):
            st.markdown(md(question))
        with st.chat_message("assistant", avatar="🧠"):
            (st.warning if reply.refused else st.markdown)(md(reply.text))

# ---------- Accounts, subscriptions, savings goal ----------
a_col, s_col, g_col = st.columns([3, 2, 2])
with a_col, st.container(border=True):
    st.subheader("Accounts")
    st.dataframe(
        accounts[["name", "type", "institution", "balance"]], hide_index=True, use_container_width=True,
        column_config={"name": "Account", "type": "Type", "institution": "Bank",
                       "balance": st.column_config.NumberColumn("Balance", format="$%.2f")},
    )
with s_col, st.container(border=True):
    st.subheader("Subscriptions")
    if subs.empty:
        st.info("No subscriptions found.")
    else:
        st.dataframe(
            subs[["merchant", "amount", "next_expected"]], hide_index=True, use_container_width=True,
            column_config={"merchant": "Service",
                           "amount": st.column_config.NumberColumn("Monthly", format="$%.2f"),
                           "next_expected": st.column_config.DateColumn("Next charge", format="MMM D")},
        )
with g_col, st.container(border=True):
    st.subheader("Savings goal")
    saved = float(accounts.loc[accounts["type"] == "savings", "balance"].sum())
    st.progress(analytics.goal_progress(saved, goal), text=md(f"{money(saved)} of {money(goal)}"))
    if goal and saved < goal:
        st.caption(md(f"{money(goal - saved)} to go. Saving $150 a month gets you there in "
                      f"{-(-(goal - saved) // 150):.0f} months."))
    elif goal:
        st.caption("Goal reached. Nice.")

# ---------- Transactions ----------
with st.container(border=True):
    st.subheader("Transactions")
    f1, f2 = st.columns([2, 3])
    categories = f1.multiselect("Category", sorted(tx["category"].unique()))
    search = f2.text_input("Search merchant")
    shown = tx.merge(accounts[["id", "name"]].rename(columns={"id": "account_id", "name": "account"}))
    if categories:
        shown = shown[shown["category"].isin(categories)]
    if search:
        shown = shown[shown["merchant"].str.contains(search, case=False, regex=False)]
    st.dataframe(
        shown[["date", "merchant", "category", "account", "amount"]], hide_index=True, use_container_width=True,
        column_config={"merchant": "Merchant", "category": "Category", "account": "Account",
                       "date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
                       "amount": st.column_config.NumberColumn("Amount", format="$%.2f",
                                                               help="Positive = money out, negative = money in")},
    )
    st.caption(f"{len(shown)} transactions")

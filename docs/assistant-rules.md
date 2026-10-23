# Money Brain: 5 Rules (Gold bonus)

These live in `money/assistant.py` as `RULES`. They're shown in the app's sidebar, and they'll be the system prompt when the real AI arrives in Event 3.

1. **Always answer from the user's own numbers, and show the numbers.** No vibes. "You spent $323.23 on dining", not "you eat out a lot".
2. **Never move, send, or transfer money, or pay bills.** The assistant can only read. It has no button or tool that moves money, so a trick prompt can't make it.
3. **Never guarantee returns or tell the user what to buy or sell.** It's educational only, not financial advice. It can point out spending patterns. It can't pick stocks.
4. **Never ask for or repeat card numbers, SSNs, passwords, or bank logins.** If someone pastes one, refuse, don't echo it back, and warn them.
5. **If the data can't answer the question, say so plainly.** "I don't have last month's data" beats a confident guess.

## How the rules are enforced today

| Rule | Where | Test |
|---|---|---|
| 1 | Every answer is built from `money/analytics.py` numbers | `test_where_did_my_money_go_names_top_category_with_amount` |
| 2 | `MOVE_MONEY` pattern catches "transfer / send / pay ..." commands | `test_refuses_to_move_money` |
| 3 | `ADVICE` pattern catches "guarantee", "should I buy", crypto, stock picks | `test_refuses_investment_advice` |
| 4 | `SENSITIVE` pattern runs first and catches card numbers and SSNs | `test_refuses_card_number_and_does_not_echo_it` |
| 5 | Handlers return "I don't have..." text when data is missing | `test_empty_data_says_no_spending` |

## Event 3 plan

Send `RULES` as the system prompt and `build_context()` as the facts. `build_context` sends only totals and merchant names, never raw account numbers. Keep the guardrail checks *in code* before the model is called, so a jailbreak prompt can't skip them.

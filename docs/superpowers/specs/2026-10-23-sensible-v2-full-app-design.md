# Sensible v2: Full App (Events 1 to 5) Design

## Intent

- **Said by the user:** make it look like the polished products people see online, build every event (1 to 5) now, use any skills needed. Stack chosen: React + FastAPI.
- **Outcome:** a product-grade web app the team can demo at Demo Night (Nov 20) and keep extending.
- **Assumed:**
  - Fake data stays the default.
  - Plaid and Claude keys only ever live in `.env`.
  - Without a Claude key, the assistant uses the existing rules engine.
  - The Streamlit `app.py` stays as the club-guide version but gets no new features.

## Architecture

```
web/ (React + Vite + Tailwind)  --/api-->  api/ (FastAPI)  -->  money/ (tested Python core)
                                                            -->  Plaid Sandbox (optional)
                                                            -->  Claude API (optional)
```

- **Dev:** Vite on :5173 proxies `/api` to uvicorn on :8000.
- **Prod and Codespaces:** `npm run build`, then FastAPI serves `web/dist` and the API on one port (8000).

## Backend (`api/`)

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/health` | no | liveness |
| `GET /api/session` | no | `{authenticated, mode, password_required, plaid_available, ai_engine}` |
| `POST /api/login` | no | `{password}` for owner mode, or `{demo: true}` for demo mode. Sets signed httpOnly cookie |
| `POST /api/logout` | yes | clears session |
| `GET /api/dashboard?month=YYYY-MM` | yes | everything the overview needs (below) |
| `GET /api/transactions?q=&category=&account=` | yes | filtered list, newest first |
| `POST /api/ask` | yes | Server-Sent Events stream. Rate-limited |
| `POST /api/plaid/link-token` | yes | Plaid Link token (sandbox) |
| `POST /api/plaid/exchange` | yes | public_token to access token, stored server-side only |
| `POST /api/plaid/disconnect` | yes | back to fake bank |
| `GET /api/security` | yes | live Security Center checks |

- **Dashboard payload:**
  - `source`, `accounts`, `net_worth`, `months`, `month`
  - `story` (sentence tokens), `summary`, `by_category`
  - `pace` (cumulative daily spend, this month vs last)
  - `subscriptions`, `alerts`, `goal`
- **Story tokens:** a list of `{text}` or `{value, kind}` where `kind` is one of `spent`, `change_up`, `change_down`, `alert`, `category`. The frontend highlights values.
- **Sessions:** Starlette `SessionMiddleware`, cookie `sensible_session`, SameSite=Lax, httpOnly, 8h max age.
  - `SECRET_KEY` comes from env. If it's missing, a random key is made per process and the Security Center flags it.
  - Server-side store `{session_id: {"plaid_access_token", "cache"}}` lives in memory.
  - Access tokens never leave the server.
- **Auth:**
  - If `APP_PASSWORD` is set, owner login needs it.
  - Demo login is always allowed and only ever shows the fake bank.
  - Plaid connect needs owner mode, or demo mode when no `APP_PASSWORD` is configured (a local dev convenience).
- **Rate limit:** `/api/ask` allows 10 requests per 60s per session. Over that returns 429 with `retry_after`.
- **Security headers on every response:**
  - `Content-Security-Policy` (self, plus Plaid CDN and Google Fonts)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy`
- **Input limits:** question at most 500 chars, history at most 8 turns, each turn at most 2000 chars. Search query at most 100 chars.
- **Errors:** never echo exception text or secrets. Plaid errors are mapped to their error_code only.

## AI (`money/ai.py`, Event 3)

1. Guardrails run first, in code, using the existing `assistant` patterns. Sensitive data, money movement and investment advice get refused without calling the model.
2. If `ANTHROPIC_API_KEY` is set and `AI_ENGINE` is not `rules`, stream from Claude:
   - model `claude-opus-5-5`, `output_config.effort="low"` (chat), `max_tokens=4000`
   - beta `server-side-fallback-2026-07-01` with `fallbacks="default"`
   - system = rules + style + `build_context()` facts. Merchant text is data, not instructions.
   - `stop_reason == "refusal"` returns a plain decline message.
3. Otherwise, or on any API error, use the rules engine answer, labeled `engine: "rules"`.

SSE events are `meta {engine, refused}`, `delta {text}`, and `done`.

## Frontend (`web/`)

**Design tokens (frontend-design pass):**
- **Color:** Ink `#14213D`, Paper `#F6F8FB`, Mint `#2EC4B6` (primary and data), Coral `#FF6B6B` (alerts only), Fog `#DCE3EC` (lines), Slate `#5A6A85` (secondary text).
- **Dark mode:** bg `#0F1A33`, raised `#16233F`, line `#26365A`, text `#E8EEF6`, mint `#3DD6C6`, coral `#FF8080`.
- **Type:** Bricolage Grotesque (display: story sentence, headings) and IBM Plex Sans (UI and numbers, tabular figures).
- **The one bold thing:** the overview opens with a full-width sentence about your month, with the numbers set as live highlighted values (count-up on first load). There is no row of stat tiles.
- **Principles:**
  - Story first, charts prove it.
  - Coral only ever means "look at this".
  - Panels sit on the page with hairline titles rather than all being identical cards.
  - Radius hierarchy: 16 for panels, 10 for controls, full for pills.
  - Sentence-case labels. No caps eyebrows, no arrow-suffixed buttons.

**Routes:**
- `/`: landing page. Hero uses the live story sentence plus a working product preview, then "Ask it", "It notices", "Locked down", and the CTA.
- `/login`: owner password or "Explore with demo data".
- `/app`: overview.
  - story
  - accounts ledger strip
  - spending pace line chart (this month vs last, the dataviz form for change over time)
  - category bars
  - alerts
  - subscriptions
  - savings goal
- `/app/transactions`: search and filter table.
- `/app/connect`: data source and Plaid Link.
- `/app/security`: Security Center (Event 4 live checks plus a guardrail red-team run).
- **Ask panel:** a slide-over available everywhere (button plus Ctrl/Cmd+K). Streams answers, shows the engine badge, refusals styled as a notice.

**Quality floor:**
- responsive to 375px
- visible focus
- `prefers-reduced-motion` respected
- dark mode
- charts have tooltips and a table view

## Event 4 Security Center checks

1. `.env` is gitignored.
2. No key-like strings in source (scan `money/`, `api/`, `web/src` for `sk-ant-`, `access-sandbox-`, 30+ char hex secrets).
3. `SECRET_KEY` set (not ephemeral).
4. Owner password set.
5. Session cookie httpOnly + SameSite.
6. Security headers active.
7. Ask rate limit active.
8. Plaid tokens server-side only.
9. AI guardrails red team: 5 attack prompts must all be refused.

## Event 5

- `docs/demo-script.md`: a 3-minute Demo Night walkthrough.
- The landing page doubles as the pitch.
- README updated with how to run everything.

## Testing

- pytest covers `money/` (existing 48) plus new:
  - `analytics.pace`
  - `story`
  - `ai` (guardrail short-circuit, rules fallback with no key, Claude path with a fake client)
  - API: auth 401, demo login, dashboard shape, ask SSE, rate-limit 429, security headers, Plaid endpoints with monkeypatched bank, security checks
- Frontend: typecheck plus build, verified in the browser at desktop and 375px, light and dark.

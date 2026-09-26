# Butterfly Guy Code Review — 2026-09-25

- **Branch:** `review/code-review-2026-09-25` (from `main` @ `0ecaf02`)
- **Scope:** the live trading path end to end (config → entry → order execution →
  position monitoring → exit and settlement → risk → reconciliation), the Schwab
  client and market-data providers, the DB layer and migrations, the collector,
  notifications, CI/CD and container build. Research and backtest code was reviewed
  where it affects live/backtest parity.
- **Changes made:** none to source, config, or runtime. This branch adds only this
  report. Per `AGENTS.md`, every recommendation that touches strategy, execution,
  risk, or token handling needs an explicit owner decision before it is implemented.

## Baseline

| Check | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run pytest` | 690 passed, 1 skipped, 1 warning (16 s) |
| Line coverage (`pytest --cov`) | 60% overall (11,178 statements) |
| Coverage of live-path modules | `order_manager` 89%, `state_machine` 94%, `risk_engine` 79%, `position_manager` 74%, `run_live` 68%, `position_service` 63%, `schwab_client` 59%, `trade_service` 58%, `collector` 57%, `db/queries` 44% |
| Repository visibility | **Public** (`gh repo view`) |

Three findings were confirmed with scratch probes that were not committed (restart
exit suppression, silent regime-name failure, and the 2027 early-close gap). Findings
marked **Needs verification** depend on broker or exchange behavior that cannot be
observed offline. Each one includes a concrete way to check it.

## Executive summary

The broker-safety core is strong and clearly shaped by previous incidents. Order
intents are persisted before submission, and broker statuses are walked recursively.
Unmapped or missing statuses fail closed, and `REJECTED`/`EXPIRED` stop the ladder.
Ambiguous writes halt the entry loop. Startup and periodic reconciliation compare
broker legs with DB legs, and live mode sits behind several explicit confirmations.
Fills are derived from execution legs rather than trusted from a single price field.

Most of the remaining risk is in four areas:

1. **Deployment surface.** This is a public repository whose deploy workflow runs on
   a self-hosted runner. That runner can `docker exec` into the trading container,
   which holds the Schwab credentials.
2. **Direction-signal integrity.** When the previous close is unavailable, the code
   silently substitutes the current spot price. The daily-bar refresh can also fail
   once and not retry for the rest of the day. Either problem can flip CALL/PUT
   without any record in the decision log.
3. **The exit path depends on telemetry.** Every poll performs several non-critical
   DB writes before the exit decision is acted on. A DB fault therefore disables
   drawdown exits without any visible sign.
4. **Behavior not yet exercised in live trading:** price-tick increments, SPX/SPXW
   root selection on monthly expiration days, early closes after 2026, and
   restart-state recovery. Paper mode cannot surface any of these.

## Findings index

| ID | Severity | Area | Title | Status |
|---|---|---|---|---|
| H1 | High | CI/CD security | Public repo + self-hosted runner with production reach | Confirmed (config) |
| H2 | High | Strategy input | Previous close silently falls back to current spot | Confirmed |
| H3 | High | Exit safety | Exit decision gated on non-critical DB writes; no query timeout | Confirmed |
| M1 | Medium | Strategy input | Daily-bar refresh marks itself done after failure; no staleness check | Confirmed (logic) |
| M2 | Medium | Broker safety | Ambiguity handlers can mask `AmbiguousOrderError` with a DB error | Confirmed |
| M3 | Medium | Broker safety | Runtime reconciler repair leaves an unmonitored, uncounted trade | Confirmed |
| M4 | Medium | Execution | Limit prices use $0.01 increments; SPX complex orders likely need $0.05 | Needs verification |
| M5 | Medium | Market data | Chain parser takes `options[0]` per strike; no SPX/SPXW root filter | Needs verification |
| M6 | Medium | Exit logic | Restart forgets `_ever_in_profit`, suppressing drawdown exits | Confirmed (probe) |
| M7 | Medium | Config | Regime names unvalidated and time bounds ignored; a typo disables exits | Confirmed (probe) |
| M8 | Medium | Calendar | Early closes hard-coded for 2026 only | Confirmed (probe) |
| M9 | Medium | Performance | Chain cache rewrites the whole day's JSON on the event loop every minute | Confirmed (logic) |
| M10 | Medium | Settlement | Live settlement wait has no timeout; post-close errors alert ~17 h late | Confirmed |
| M11 | Medium | Risk | Restart with an open trade double-counts entry cost in daily P&L | Confirmed |
| L1–L16 | Low / Info | Various | See the Low / Info section | — |

---

## High

### H1 — Public repository with a self-hosted runner that reaches production

**Where:** `.github/workflows/deploy.yml:11` (`runs-on: self-hosted`), with steps that
`docker exec` into `butterfly_timescaledb` and `butterfly_spx_app` and run
`docker compose up --build` in `/opt/butterflyguy`.

**What:** `ButterflyGuy` is public. The deploy workflow only triggers on `push: main`
and `workflow_dispatch`, which is correct. However, any runner registered to a
public repo can be targeted by a pull request that *adds its own workflow* with
`on: pull_request` and `runs-on: self-hosted`. For `pull_request` events, GitHub runs
the workflow files from the PR itself. The only barrier is the repo's
fork-PR approval setting. By default, approval is required only for first-time
contributors.

**Why it matters:** the runner user can reach Docker, which is root-equivalent on the
host. It can also reach the Schwab token, the account ID, the DB, and the running
trading containers. GitHub's own guidance is to use self-hosted runners only with
private repositories.

**Recommendation (any one of these closes it; the first is cheapest):**
- Settings → Actions → General → set "Fork pull request workflows" to **Require
  approval for all external contributors**.
- Put the runner in a runner group restricted to this repo and to the `deploy.yml`
  workflow on `refs/heads/main`.
- Longer term: run deploys from a private mirror, or pull-based on the host, so the
  public repo has no path to the host.

Related hygiene: `actions/checkout@v6` and `timescale/timescaledb:latest-pg16` are
not SHA-pinned, although `setup-uv` is. The Dockerfile copies
`ghcr.io/astral-sh/uv:latest` (`Dockerfile:9`), so builds are not reproducible.

### H2 — Previous close silently falls back to the current spot price

**Where:** `src/butterfly_guy/services/trade_service.py:234-247`

```python
previous_close = spot_price
try:
    row = await ...fetchval("SELECT close FROM daily_bars WHERE underlying=$1 AND date < CURRENT_DATE ...")
    if row:
        previous_close = float(row)
except Exception:
    pass
```

**What:** there are three problems here:
- If the query raises, or `daily_bars` has no row, `previous_close` stays equal to
  the current spot. Direction then becomes `open >= spot`, which is the sign of
  the intraday move reversed rather than the gap. Nothing is logged, and nothing is
  written to `decision_log`.
- The query takes the latest row before `CURRENT_DATE` without checking that it is
  the *previous trading day*. After a missed refresh (see M1), it uses a close from
  two or more sessions ago.
- `CURRENT_DATE` is evaluated in the DB server's timezone, not US/Eastern.

**Why it matters:** direction is the core decision of the strategy. The research
journal describes the strategy as a directional bet that pays when the close lands
about 1–2.3σ in the gap direction (`docs/research/strategy-discovery-journal.md:678`).
Swapping the direction rule alone moves the replay by thousands of dollars
(`:596-597`). The DB backtest
(`run_backtest_db.get_prev_close`) falls back to the prior day's last spot price at
or before 16:00. That is a different fallback, so live and backtest diverge exactly
when the data is degraded.

**Recommendation:** treat a missing or stale previous close like `session_open_unavailable`.
Block the entry, log `entry_blocked {reason: prev_close_unavailable | prev_close_stale}`,
and require `date == previous trading day` (the calendar helpers already exist). Pass
the Eastern session date explicitly instead of using `CURRENT_DATE`. Add a test for
each branch.

### H3 — The exit decision is gated on non-critical DB writes, with no query timeout

**Where:** `src/butterfly_guy/services/position_service.py:395-510`,
`src/butterfly_guy/db/connection.py:41-43`

**What:** on every 2-second poll, `monitor_loop` does the following before
`execute_exit`:
- inserts monitoring-leg quotes (this one is best-effort, correctly)
- `update_peak_value` (`:432`)
- `tent_queries.insert` (`:435`, every poll, unconditionally)
- `decision_queries.log_event("profit_state_transition")` (`:448`)
- on a signal: `_exit_mark_parity_report` (a DB query), two more `log_event`
  calls, and `merge_metadata` (`:467-502`)

Any exception in these steps lands in the generic `except Exception` at `:637`,
which logs `monitor_error` and skips the poll. The state machine never acts on the
signal. The asyncpg pool is created without `command_timeout`, so a hung query
(lock wait, or connection starvation on Helios's 50-connection cap) stalls the
monitor indefinitely instead of failing fast.

**Why it matters:** during a DB outage, or when the pool is exhausted, the
trailing-drawdown and loss-stop logic is silently disabled. The position rides to
settlement. The loss is bounded by the debit, but the exit strategy the backtests
assume is not running, and nothing alerts. The market-data path already has a
good degraded-mode alert, but the DB path has none.

**Recommendation:** reorder the poll as *value → evaluate → act → record*. Wrap
telemetry in a small best-effort helper that logs and counts failures without
raising. Persist the `pending_exit` metadata best-effort, after the exit order is
working rather than before it. Set `command_timeout` on the pool (5–10 s). Add a
readiness flag and alert after N consecutive telemetry failures, mirroring
`MARKET_DATA_FAILURE_THRESHOLD`.

---

## Medium

### M1 — The daily-bar refresh marks itself done after a failure

**Where:** `src/butterfly_guy/data/collector.py:103-138`

`collect_daily_bars` catches each symbol's fetch error, logs a warning, and then
unconditionally sets `self._daily_bars_date = today`. It runs on the first snapshot
after 09:30 ET. At that time Schwab's daily history very likely includes today's
*in-progress* candle, so yesterday's row was itself written as a 09:30 partial and
is only corrected by today's refresh. If today's refresh fails once, it is never
retried, and `daily_bars` holds yesterday's 09:30 price as yesterday's "close".
H2's query then uses it for the gap. The code also uses `dt.date.today()`, which
follows the container's timezone (UTC) rather than the Eastern date.

**Recommendation:** set `_daily_bars_date` only after all symbols succeed, and
retry on the next snapshot otherwise. Skip candles dated today. Use `session_date()`.
**To verify:** compare `daily_bars.close` with official closes for the last 60
sessions, and look for days where the stored close equals that day's 09:30
`spot_prices` value.

### M2 — Ambiguity handlers can mask `AmbiguousOrderError` with a DB error

**Where:** `src/butterfly_guy/execution/order_manager.py:511-515` (entry),
`:746-750` (exit), and `:805-807` (post-cancel)

```python
except Exception as e:
    if intent_id is not None and self.intent_queries is not None:
        await self.intent_queries.mark_unknown(intent_id, str(e))   # can raise
    raise AmbiguousOrderError("entry order outcome is unknown") from e
```

If the original failure was a DB fault, for example `mark_broker_order_id` failing
after a successful `place_order`, then `mark_unknown` usually fails too. Its asyncpg
exception replaces `AmbiguousOrderError`. `entry_loop` (`run_live.py:765-793`)
does not classify it as a broker error, so it *increments `consecutive_errors` and
keeps trying to enter every 15 s*.

The existing guards cover most of the window. A still-working unknown order blocks
entry, and the reconciler flags a position with no DB trade. There is a gap, though.
If the first order fills after DB recovery, the next `attempt_entry` can run up to
15 s before the reconciler's next pass. At that point `trade_count` is still 0 and
no working order is visible, so a second order can be submitted.

**Recommendation:** make the bookkeeping best-effort inside the handler with
`try: mark_unknown(...) except Exception: log`, then always raise
`AmbiguousOrderError`. As defense in depth, have live `attempt_entry` require
`_broker_option_positions(...) == {}` immediately before submitting.

### M3 — Runtime reconciler repair leaves an unmonitored, uncounted trade

**Where:** `src/butterfly_guy/scripts/run_live.py:493-513`, called from
`broker_reconciler_loop` (`:601-632`)

When the reconciler repairs a filled entry intent into a `butterfly_trades` row
*at runtime*, the process state is not updated in three ways:
- no `monitor_loop` is started for the trade, so there are no drawdown or loss
  exits
- `daily_risk_state.trade_count` is not incremented
- the DB row is not closed at settlement, because the cash-settlement close runs
  inside `monitor_loop`

The usual trigger is "broker fill was not fully persisted", which already stops the
entry loop and alerts, so the practical effect today is an unmanaged position that
is recovered only by a restart. **Recommendation:** either make runtime repair
signal the entry loop to adopt the trade and start its monitor, or keep repair
startup-only. In the second case the runtime path should mark the gate unsafe and
alert, rather than silently creating a trade row.

### M4 — Price-increment rounding is $0.01; SPX complex orders likely require $0.05 (Needs verification)

**Where:** `src/butterfly_guy/core/entry_pricing.py:7` (`PRICE_INCREMENT = 0.01`),
`trade_service.py:478-482`, `order_manager.py:558` and `:654`, and
`order_builder.py:55` (`str(round(limit_price, 2))`)

Entry limits are `ask + step·0.10`, floored to cents. Exit limits are `bid_floor + k·0.10`
rounded to cents. Both are derived from composite quotes, so they are arbitrary cent
values (for example 1.37). Cboe applies class-specific minimum increments to complex
orders. SPX/SPXW complex orders are generally quoted in $0.05 increments, and XSP
rules differ. A non-conforming price would be rejected at `place_order` as HTTP 4xx.
The code classifies that as `AmbiguousOrderError`, so the entry loop stops for the
day. For an exit, the monitor task stops. Paper mode can never reveal this.

The April 2026 XSP evidence (226 `REJECTED` butterflies across two days, in
`docs/ai/REVIEW_STATE.md`) was never root-caused in the repo. It is worth checking
whether the rejection reason was the price increment.

**Recommendation:** add a per-underlying tick table. Round debits *down* and credits
*up* to the tick, which is conservative for both sides. Confirm with Schwab
`previewOrder` against real SPX and XSP butterflies. The existing
`tests/integration/test_order_preview.py` only checks JSON shape offline. Do this
before any live canary.

### M5 — Chain parser takes `options[0]` per strike with no root filter (Needs verification)

**Where:** `src/butterfly_guy/data/chain_utils.py:35`, used by `TradeService`,
`PositionService`, and `OrderManager._fetch_live_spread`. Note that
`collector._parse_chain_response` stores *every* entry.

On the third Friday, the `$SPX` chain for that date can list both the AM-settled
monthly `SPX` contract and the PM-settled weekly `SPXW` contract under the same
strike. The same applies to `NDX`/`NDXP`. Taking `options[0]` may pick the
AM-settled contract, which has stopped trading. The result would be zero or stale
marks, a phantom cheap butterfly, and, in live mode, an order for the wrong symbol.
The collector stores both rows, so DB replays and live selection can disagree.

**To verify:** run
`SELECT snapshot_time, strike, option_type, count(*) FROM option_chain_snapshots WHERE expiration = '2026-09-18' GROUP BY 1,2,3 HAVING count(*) > 1 LIMIT 5;`
**Recommendation:** filter to the PM-settled root per underlying (`SPXW`, `NDXP`,
`XSP`) using `symbol` or `settlementType`, and assert at most one contract per
strike/type in `iter_chain_options`.

### M6 — A restart forgets `_ever_in_profit`, suppressing drawdown exits

**Where:** `src/butterfly_guy/position/state_machine.py:111` and `:259-263`,
`position_service.py:285-289`

After a restart the recovered peak is restored, but `ProfitStateMachine.reset()`
sets `_ever_in_profit = False`. Drawdown exits require that flag, so a recovered
position below entry gets no drawdown exit until it climbs back above entry.
**Confirmed by probe:** entry 1.00 and peak 3.00, then current 0.90:

- continuous run → `ExitSignal('drawdown_morning')`
- after restart → `None`

Restarts are deliberately rare here (see the stability-window notes), but they are
exactly when the state is least trustworthy. **Recommendation:** in `monitor_loop`,
set `_ever_in_profit = recovered_peak is not None and recovered_peak >= trade.entry_price`.
That condition is equivalent to having been at or above entry. Add a regression test.

### M7 — Regime names are unvalidated and regime time bounds are ignored

**Where:** `src/butterfly_guy/core/time_utils.py:183-189` (hard-coded 120/240),
`state_machine.py:89-91`, `core/config.py:73-79` and `:108-117`

`get_time_regime` hard-codes the boundaries at 120 and 240 minutes. The configured
`start_minutes_after_open`/`end_minutes_after_open` are read only by the strategy
page (`reports/strategy_page.py:144-150`), so the public page can describe a
schedule the bot does not run. If `regimes` lacks one of the three hard-coded
names, `evaluate` returns `None` with no drawdown exits and no log. **Confirmed by
probe:** renaming `morning` to `mornin` produced no exit at a 97% drawdown.

**Recommendation:** validate in `AppConfig` that the regime keys are exactly
`{morning, late_morning, afternoon}` and that the bounds are contiguous. Then either
drive `get_time_regime` from the configured bounds or remove them from the schema.

### M8 — Early closes are hard-coded for 2026 only

**Where:** `src/butterfly_guy/core/time_utils.py:30-33` and `:177-180`

Holidays are computed from rules, but `get_us_market_early_closes` returns an empty
set for any year other than 2026. **Confirmed by probe:** `market_close_time(2027-11-26)`,
the day after Thanksgiving, returns 16:00. After 2026 this affects `is_market_open`,
`minutes_to_close`, the regime clock, the settlement-bar selection in
`final_regular_session_close_from_candles`, and EOD chart timing. The first affected
date is about 14 months away. `HOLIDAYS_2026` is dead code.

**Recommendation:** use rule-based early closes: the day after Thanksgiving,
Dec 24 when it is a weekday and not the observed holiday, and Jul 3 when it is a
weekday and not the observed holiday. Add a test per rule, or depend on an exchange
calendar package.

### M9 — The chain cache rewrites the whole day's JSON on the event loop

**Where:** `src/butterfly_guy/backtest/chain_cache.py` `save_snapshot`, called from
`collector.py:171`; `data/chains` is bind-mounted in all three app containers

Every 60 seconds, each collector reads, parses, and re-serializes the entire day's
file, then writes it back non-atomically. All of this happens synchronously on the
same event loop that runs position monitoring and order polling. The file grows all
session: roughly (strikes × 2) rows × 390 snapshots. By the afternoon, each append
blocks the loop for the full parse and dump time. A crash mid-write corrupts the
file. The next load then raises `JSONDecodeError`, which `save_snapshot` catches,
so caching stops for the rest of the day. The same data is already in
`option_chain_snapshots`.

**To verify on Helios:** `ls -la data/chains/SPX | tail`.
**Recommendation:** switch to append-only JSONL (one line per snapshot) or one file
per snapshot, move the I/O off the loop with `asyncio.to_thread`, and write
atomically. Alternatively, drop the cache and replay from the DB.

Related: `notify.send` (Telegram) uses blocking `urllib` with a 5 s timeout. It is
called from `collector.run_loop` and `position_service.monitor_loop`, so each alert
can stall the loop for up to 5 s. Wrap it in `asyncio.to_thread`.

### M10 — Live settlement wait has no bound, and post-close failures surface late

**Where:** `position_service.py:778-809` and `run_live.py:709-712`

`_wait_for_broker_cash_settlement` polls every 5 minutes forever. If Schwab's
transaction format changes, or the position is partly closed or assigned, the
function returns `None` indefinitely and never alerts. Separately, `entry_loop`
checks `monitor_task.done()` only after the `is_market_open()` gate. A
`SettlementEvidenceError` raised after the close is therefore not seen, and the
critical alert is not sent, until the next session's open, roughly 17 hours later.

**Recommendation:** alert (without failing) once settlement has been pending past a
threshold, for example 09:30 ET the next trading day. Check monitor-task completion
before the market-hours gate.

### M11 — A restart with an open trade double-counts the entry cost in daily P&L

**Where:** `run_live.py:1135-1148` and `risk/risk_engine.py:134-143`

At startup with an open trade, `realized_pnl` is set to `realized − entry_cost`
("worst-case committed exposure"). When the trade closes, `record_pnl` *adds* the
trade's actual P&L. The final value is `realized + pnl − entry_cost`, so the entry
cost is counted twice. Example: entry $2.00 and exit $3.00 should record +$100, but
the daily state shows −$100. An SPX debit up to $6.50 alone exceeds the $500 daily
limit, so the day is marked halted. With `max_trades_per_day: 1` this is mostly a
reporting error today. It becomes a real gating bug if more trades per day are ever
allowed. **Recommendation:** track committed exposure separately from realized P&L,
or recompute realized P&L from `butterfly_trades` on close instead of adding deltas.

---

## Low / Info

| ID | Where | Finding | Suggestion |
|---|---|---|---|
| L1 | `order_manager.py:519-600` | `execute_entry`, the live ladder, has **no callers** and creates no broker-order intents. If reused, its orders would be invisible to reconciliation. | Delete it, or add intents and tests before any reuse. |
| L2 | `schwab_client.py:211-244` | `_retry` retries non-retryable 4xx errors. A 429 on the last attempt raises `"... after 3 retries: None"`. | Retry only 429/5xx/transport errors, and keep the last 429 as `last_err`. |
| L3 | `schwab_client.py:280-285`, `order_manager.py:511-515` | A 4xx from `place_order` is a definitive rejection but is treated as ambiguous, so it halts the entry loop. | This is conservative and acceptable. Consider classifying 4xx with no `Location` header as "not placed". |
| L4 | `schwab_client.py:264-270` | `get_spot_price` silently falls back to `closePrice` (the prior close) when `lastPrice` is missing or 0. | Raise or log when falling back during market hours. |
| L5 | `schwab_client.py:317-337` | `get_intraday_bars` uses `dt.date.today()` (host timezone) and naive datetimes, and re-imports `datetime` locally. | Use `session_date()` and timezone-aware Eastern datetimes. |
| L6 | `config.py:141-143`, `connection.py:32` | The DSN embeds the password without URL-encoding. Three containers × `max_size=10` = 30 of Helios's ~50-connection cap. | Pass the password with `quote_plus`, or use keyword arguments. Size pools with the shared cap in mind. |
| L7 | `queries.py:541-554` | The "rolling 7-day" weekly loss window spans 8 calendar days (`>= date − 7`). | Use `> date − 7`, or a trading-week definition. |
| L8 | paper vs simulation vs live | There are three fill conventions: paper = mark + commission, `SimulationEngine` = ask + slippage + commission, live = ask + ladder. The paper ledger is an optimistic bound on live results. | Keep reporting paper and executable P&L side by side, as the prospective cohort does. |
| L9 | `backtest/simulation_engine.py:268` | `SimulationEngine` sets direction from the entry *bar close* vs the previous close. Live and the DB backtest use the *session open*. Research that goes through `SimulationEngine` (classifier sweep, entry analysis) is not live-parity. | Use the open, or document the difference. |
| L10 | `trade_service.py:545` | `execute_single_attempt` is always called with quantity 1, so `max_position_size` never sizes anything. | This is fine for now. Document it so it is not mistaken for a sizing control. |
| L11 | `butterfly_builder.py:166-173` | Legs with zero or crossed bid/ask are not rejected. A leg with no market can produce a cheap, high-R/R fly that paper mode fills at mark. | Require `0 < bid <= ask` for all legs, or a minimum fly bid. |
| L12 | `order_manager.py:651` | The exit `bid_floor` only ratchets down across the whole ladder. One bad tick anchors every later step lower. | Re-anchor on each fresh spread, or use the median of the last N. |
| L13 | `order_manager.py:818-860` | `_wait_for_fill` counts only sleep time, so request latency extends the real wait. | Use a monotonic deadline. |
| L14 | `run_live.py:969-982` | The regime is classified once at startup, but containers run for weeks. It is only consumed when `bull_call_bias` is true, which it is not in any config, so the issue is latent. | Reclassify daily in `daily_reset_loop`. |
| L15 | `position_service.py:706-723` | The paper settlement *fallback* values a trade recovered on a later day with *today's* chain (`get_0dte_expiration()`). | Use `trade.trade_date`, or block the fallback for past-dated trades. |
| L16 | maintainability | `run_backtest_db.py` has 3,047 lines at 36% coverage. `position_service` reaches into `notifier._post` and uses `getattr` fallbacks that exist for tests. | Split into loaders, selection, simulation, and reporting modules. Add a public `notify_text`. |

---

## Operational note found during review

`tools/cohort_daily_update.sh` (systemd timer, Mon–Fri 18:30) commits in
`/mnt/Repos/Trading/Butterflyguy` and runs `git push origin HEAD`, pushing **whatever
branch is checked out**. If this checkout is left on a feature branch, the timer
commits cohort ledgers onto that branch and pushes it to the public remote. Either
pin the script to `main` (`git push origin HEAD:main` after verifying the current
branch, or skip when not on `main`), or run it from a dedicated worktree.

## Strengths worth keeping

- **Fail-closed broker state.** Intents are created before submit, and broker
  statuses are walked recursively (`walk_orders`, `order_statuses`). Unmapped and
  missing statuses are rejected. Partial fills and cancel-pending states stop
  trading, and `REJECTED`/`EXPIRED` raise `TerminalOrderError` before any cancel or
  reprice.
- **Evidence-based fills and settlement.** `parse_broker_fill` rebuilds the net price
  from execution legs, checks the leg ratios and the net order type, and enforces
  the submitted limit. `broker_cash_settlement_from_transactions` checks leg
  quantities, the payoff bounds, and whether the implied index values are
  consistent.
- **Layered live gating.** Live mode requires `allow_live_trading`, an
  exact-account confirmation, confirmed allocation and daily-loss values, and an
  SPX/XSP-only allowlist with an XSP canary flag. It also rejects gateway market
  data while live.
- **Strict config.** `extra="forbid"` is set everywhere, and cross-field validation
  runs in `validate_trading_safety`.
- **Token handling.** The token store is locked and atomic, a monotonic
  `creation_timestamp` rejects stale writes, and re-authorizations are hot-reloaded
  after the new client is proven against Schwab.
- **Observability.** Readiness flags, Alertmanager critical conditions with
  resolution, per-decision `decision_log`, and live-vs-DB selection and exit-mark
  parity reports on every trade.
- **Tests and research discipline.** 690 tests run in 16 s and ruff is clean.
  Research uses pre-registered cohorts with checksum-verified ledgers.

## Suggested order of work

1. **H1** — change the Actions fork-approval setting and the runner group today. This is
   configuration only.
2. **H2 + M1** — make direction inputs fail closed and check staleness. This is small, local,
   and has high leverage on strategy correctness.
3. **H3 + M2** — decouple exits from telemetry, add `command_timeout`, and make the
   ambiguity handlers non-masking.
4. **Before any live canary:** M4 (tick size, via `previewOrder`), M5 (root filter),
   M3 (runtime repair), and M10 (settlement alerting).
5. **Restart and config correctness:** M6, M7, and M11.
6. **Before 2027:** M8 (early-close rules).
7. **Performance and hygiene:** M9 (chain cache and blocking Telegram calls), then the
   Low items as they are touched.

## Method

The live path was read in full: `run_live.py`, `trade_service.py`,
`position_service.py`, `order_manager.py`, `order_builder.py`, `entry_pricing.py`,
`risk_engine.py`, `schwab_client.py`, `collector.py`, `chain_utils.py`,
`position_manager.py`, `state_machine.py`, `profit_policy.py`, `entry_selection.py`,
`butterfly_builder.py`, `butterfly_selector.py`, `config.py`, `time_utils.py`,
`db/connection.py`, `db/migrations/run_migrations.py`, the relevant `db/queries.py`
methods, `notify.py`, the provider outline, both workflows, the Dockerfile, and the
compose volumes. The backtest and research code was sampled for parity only. Commands
run: `uv run ruff check .`, `uv run pytest`, `uv run pytest --cov=butterfly_guy`, and a
scratch probe script outside the repo. No broker, DB, Docker, or service commands
were run.

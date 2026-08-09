# Reducing the weekly re-authorization cost — a scoping question

Scoped in Window H (2026-08-08) on operator instruction. **This is a question, not a plan, and
nothing here was built.** The brief called this "the only item that attacks the recurring deadline
rather than paying it" and "worth scoping as a question before it is worth building".

## The cost being attacked

The Schwab refresh token has a hard 7-day life from `creation_timestamp`. This cannot be extended:
an ordinary refresh does not reset it, so re-authorizing early buys only the difference between the
old expiry and seven days from the new one — hours, not weeks. **The deadline recurs weekly and
always will.**

The cost per occurrence is: a human at a browser on zeus, an `scp`, a locked move, and **five
container restarts** — gateway, three trading apps, candidate feed — which must happen on a
non-trading day, which is why the Saturday cadence exists and why losing it matters.

The human-at-a-browser part is imposed by Schwab and is not attackable here. **The five restarts
are.** That is the whole of what follows.

## Why the restarts happen — the actual mechanism

Not because containers cannot *see* the new document. All five bind the token *directory*, so a new
inode is visible immediately. They restart because none of them ever **re-reads** it.

`SchwabClientWrapper.initialize()` (`schwab_client.py:58`) calls schwab-py's
`client_from_access_functions`, passing `self._read_token` as `token_read_func`. In schwab-py's
implementation (`schwab/auth.py`), that function is invoked **exactly once**:

```python
token = token_read_func()
metadata = TokenMetadata.from_loaded_token(token, token_write_func)
...
return client_class(api_key, session_class(..., token=token, ...))
```

The token is then held by the `AsyncOAuth2Client` session in memory for the process lifetime.
schwab-py refreshes from that in-memory copy and calls the *write* function on refresh; it never
calls the read function again. `run_live.py:763` calls `initialize()` once at startup.

So the restart is doing exactly one useful thing: **re-running `token_read_func` once.** Everything
else about the restart — DB pool teardown, metric re-seeding, trade recovery, regime
classification — is incidental cost we pay to trigger a single file read.

## The brief's proposed remedy, and why it is weaker than it looks

The brief's framing: *"If the gateway held the sole credential and the trading apps read through it,
one re-authorization would not require restarting five containers."* That is the eventual
`SCHWAB_ACCESS_MODE=gateway` cutover, with C3 as the confidence-building step.

**This premise is incomplete, and the arithmetic does not work out the way it implies.**

The gateway exposes three routes — `/v1/quotes`, `/v1/spot`, `/v1/chain`. All three are market data.
But the trading apps do far more than read market data through `SchwabClientWrapper`:

| Surface | Methods | On the gateway? |
|---|---|---|
| Market data | `get_option_chain`, `get_spot_price`, `get_intraday_bars`, `get_daily_bars`, `get_equity_quotes`, `get_market_movers` | partly — 3 routes |
| **Account** | `get_account_numbers` (startup), `get_account_snapshot`, `get_positions`, `get_account_balances`, `get_transactions_for_day` | **no — forbidden** |
| **Orders** | `place_order`, `get_order_status`, `cancel_order`, `get_orders_for_day`, `get_todays_orders` | **no — forbidden** |

Account and order operations are forbidden on the gateway by standing policy, and that policy is
load-bearing — it is what keeps a network-exposed service incapable of moving money.

Consequence: **a full market-data cutover does not remove any trading app's need for its own Schwab
credential.** Every app still calls `get_account_numbers()` at startup and `place_order()` during the
session. The restart count goes from **5 to 4**, not from 5 to 1 — only the candidate feed, which is
market-data-only, could genuinely drop its credential.

Four restarts instead of five, in exchange for a cutover of the entire live market-data path, is a
poor trade. **The gateway cutover should be justified on its own merits — blast-radius reduction,
one place to rate-limit, one place to audit — and not sold as the fix for the weekly re-auth cost.**

## The alternative worth costing first

Make the consumers **re-read the document** instead of restarting to re-read it.

Nothing in the architecture prevents this. The read path is already pluggable and already correct:
`_read_token` takes the C1 `flock` on `.tokens.json.lock` and reads through `AtomicFileTokenStore`.
The only reason it runs once is that schwab-py calls it once.

Shape of the change, as a question to cost — not a design:

- Give `SchwabClientWrapper` a `reload()` that re-runs `client_from_access_functions` against the
  same store and swaps `self._client`. The account hash is stable and need not be re-resolved.
- Trigger it on document change — compare inode/digest on a slow timer, or watch the directory. The
  existing supervised-task structure in `run_live.py` is the natural home, and the Window G SIGTERM
  handler already cancels children cleanly.
- Old and new clients must not be in flight simultaneously; the swap needs to be safe against a
  request mid-cycle.

If it works, the weekly cost drops to **zero restarts** and the Saturday constraint weakens
considerably — the re-auth stops requiring a closed market, because nothing is being torn down.
That, not the gateway cutover, is what actually attacks this deadline.

Scope is roughly one method plus one supervised task in one file, against a cutover touching the
whole live data path.

## The questions to answer before building either

1. ~~**Does a mid-session client swap have a safe point?**~~ **Answered — yes, and it needs no
   reference-counting.** Every call site in `schwab_client.py` resolves the bound method *eagerly*
   and hands it to `_retry`:

   ```python
   resp = await self._retry(self.client.get_option_chain, symbol, ...)
   ```

   `self.client.get_option_chain` is evaluated **before** `_retry` is awaited, so an in-flight call
   holds its own reference to the client object it started on. All 26 call sites follow this shape
   (`place_order` at `:168` awaits `self.client.place_order(...)` directly, which resolves eagerly
   for the same reason). Rebinding `self._client` therefore cannot disturb a request already in
   flight: it finishes against the old client, which still has a valid access token in memory, and
   only *subsequent* calls pick up the new one.

   **The one real hazard is `close()`, not the swap.** `close()` (`:401`) calls
   `close_async_session()`, which would break in-flight requests on the old client. So the reload
   must not close the old session immediately. Options, cheapest first: leave it to GC (one orphaned
   httpx session per reload, i.e. one per week — untidy but bounded); or close it after a delay
   exceeding the worst-case retry chain (`MAX_RETRIES` with `RETRY_BACKOFF`, tens of seconds).
   Reference-counting is available but looks like more machinery than a weekly event justifies.

   *This was the question that decided whether the cheap option is actually cheap. It is.*
2. **Would the operator accept a re-auth with the market open?** If yes, zero-restart reload is worth
   real money — it removes the Saturday constraint entirely. If no, it only removes the restarts and
   the weekday constraint stays.
3. **Does the candidate feed matter enough to cut over separately?** It is the one consumer that
   could genuinely become credential-free under the gateway, and it is also the one whose auth has
   never been observed on a real call. Cutting it over would answer both at once.
4. **What is the failure mode of a bad reload?** A restart that fails to authenticate is loud and
   crashes the app. A reload that fails silently could leave an app running on a dead credential
   until its next refresh. Needs an explicit failure path — probably "log, alert, keep the old
   client, retry".
5. **Is `get_account_numbers` really needed at every startup?** It is the only reason the trading
   apps touch the account surface at boot. If the hash were cached, the account surface would be
   order-time-only — which does not remove the credential, but does narrow it.

## Recommendation

**Build the reload.** Question 1 — the one that decided it — is answered: the swap is safe and needs
no reference-counting, and the only hazard is closing the old session too eagerly, which is
avoidable. The reload path dominates the gateway cutover on this axis by a wide margin: less code,
less risk, no policy change, and it takes the restart count to zero rather than to four.

Remaining questions 2–5 shape the design but none of them can invalidate it. Question 4 (silent
reload failure) is the one that must be got right, and the answer is already clear in outline: log,
alert, keep the old client, retry — never leave an app running on a credential it thinks is fresh.

Not yet built. Deployment would in any case require recreating the trading containers, which is an
operator decision and wants a closed market — so the natural moment to ship it is alongside the
2026-08-15 re-authorization, which is the last one it would not help with.

Keep C3 and the gateway cutover on their own justification. They are worth doing for blast radius
and auditability. They are not the answer to the weekly deadline, and Window H's reading of the
route surface is that they were never going to be.

## Status

Nothing built. No decision taken. No code changed.

# Reducing the weekly re-authorization cost — a scoping question

Scoped in Window H (2026-08-08) on operator instruction. **This is a question, not a plan, and
nothing here was built.** The brief called this "the only item that attacks the recurring deadline
rather than paying it" and "worth scoping as a question before it is worth building".

## The cost being attacked

The Schwab refresh token has a hard 7-day life from `creation_timestamp`. This cannot be extended:
an ordinary refresh does not reset it, so re-authorizing early buys only the difference between the
old expiry and seven days from the new one — hours, not weeks. **The deadline recurs weekly and
always will.**

The cost per occurrence is: a human at a browser on zeus, an `scp`, a locked move, and **four
container restarts** — three trading apps and the candidate feed — which must happen on a
non-trading day, which is why the Saturday cadence exists and why losing it matters. (Earlier drafts
said five, counting the gateway; see the correction below.)

The human-at-a-browser part is imposed by Schwab and is not attackable here. **The four restarts
are.** That is the whole of what follows.

## Why the restarts happen — the actual mechanism

Not because containers cannot *see* the new document. All five bind the token *directory*, so a new
inode is visible immediately. They restart because they never **re-read** it — and not all of them
have that problem.

**Correction (2026-08-09): the baseline is four restarts, not five.** There are three distinct token
paths, and only two of them cache:

| Consumer | How it holds the token | Restart on re-auth? |
|---|---|---|
| gateway | **fresh client per request**, built inside the token lock and discarded (`LockedSchwabClientAdapter.execute`) | **No** |
| three trading apps | `client_from_access_functions` once at startup, cached for the process lifetime | Yes |
| candidate feed | read once at first use, cached in memory, never written back (`candidate_fleet/schwab_market_data.py:29`) | Yes |

The gateway was never part of this problem. The claim that it "holds the old refresh token in memory
and would write it back over the new document" — the stated reason for restarting it first — is
false, and the per-request construction that makes it false is documented in `live_provider.py` as
deliberate and load-bearing.

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
session. Against the corrected baseline of four, the restart count goes from **4 to 3** — only the
candidate feed, which is market-data-only, could genuinely drop its credential.

Three restarts instead of four, in exchange for a cutover of the entire live market-data path, is a
poor trade *on this axis*. **The gateway cutover should be justified on its own merits — blast-radius
reduction, one place to rate-limit, one place to audit — and not sold as the fix for the weekly
re-auth cost.**

But note where the two approaches meet: the feed is the one consumer the reload does **not** cover
and the one the gateway *would* free. They are complementary, not competing — see the arithmetic
below.

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

**Built 2026-08-09 as `reload_if_reauthorized` (`schwab_client.py:123`), covering the three trading
apps only.** It does not cover the candidate feed, which builds its own client in
`candidate_fleet/schwab_market_data.py` and would need the same treatment — or the gateway cutover —
to stop needing a weekly restart.

The corrected arithmetic, end to end:

| State | Restarts per re-auth |
|---|---|
| Baseline (gateway never needed one) | **4** — three apps + feed |
| Reload deployed to the trading apps | **1** — feed only |
| …plus the feed reading through the gateway, or given the same reload | **0** |

At zero the Saturday constraint weakens considerably: the re-auth stops requiring a closed market,
because nothing is being torn down. Note that even then a human still runs the browser OAuth flow
every seven days — Schwab's refresh-token life is not negotiable, and **no amount of this work makes
the re-authorization itself go away.** What it removes is the restart choreography around it.

Extending the reload to the feed is the obvious next increment and is smaller than it was for the
apps: the feed resolves no account hash, so there is nothing to verify before swapping.

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
3. **Does the candidate feed matter enough to cut over separately?** **Now the deciding question for
   getting to zero**, since the reload covers the apps and the feed is the only consumer left needing
   a weekly restart. It is also the one consumer that could genuinely become credential-free under
   the gateway, and the one whose auth has never been observed on a real call. Either give it the
   same reload — cheaper, since it resolves no account hash — or cut it over to the gateway, which
   answers both questions at once.
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
less risk, no policy change, and it takes the restart count to one rather than to three.

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

## Candidate-feed reload follow-up (2026-08-10)

Supersedes the candidate-feed portion of the status above. The feed reload is now **built and tested
locally but not deployed**. It watches the same `creation_timestamp` marker every five minutes,
validates a replacement credential with one read-only `$SPX` quote before swapping, retains the
working client on every failure, and retries. Its shared-lock reader opens the existing C1 lock file
read-only, so the candidate container keeps its read-only token-directory mount and never becomes a
persistent token writer.

The live restart count remains **one** until that code is separately deployed and proven. Once it is
deployed and survives a real re-authorization, the expected restart count becomes **zero**; the
manual browser OAuth flow and seven-day deadline remain unchanged.

### Deployment addendum (2026-08-10)

The candidate reload is now **deployed** on Helios image `f9df84dca695`. The feed stayed on a
read-only token-directory mount, initialized through the shared read lock, returned `/ready` 200,
and resumed authenticated snapshots without recreating any evaluator. Its marker-change behavior
remains fake-proven only until the 2026-08-15 re-authorization.

Expected restarts are now **zero**, with an explicit feed restart retained as the fallback if
`candidate_market_data_token_reloaded` does not appear within six minutes or
`candidate_token_reload_failed` is non-zero.

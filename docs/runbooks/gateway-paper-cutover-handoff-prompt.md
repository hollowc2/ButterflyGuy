# Gateway PAPER cutover handoff prompt

Copy and paste the prompt below into a new Codex task when resuming.

---

Continue the Helios SchwabGateway/PAPER strategy cutover from the completed
2026-08-25 deployment. Read `AGENTS.md`, load the `vps-server-management` and
`helios-live-deploy` skills, then read
`docs/runbooks/gateway-paper-cutover-2026-08-25.md` completely before acting.

Current intended state:

- production SchwabGateway is `v0.2.4`, commit
  `25f9ae007d8dcfff38a51c8d74085f04f6368601`, image
  `sha256:9c3a1da5e5b8bf259a8146fdea960790cb04a97f0184beef33390fe58b060ec5`;
- PAPER SPX, NDX, and XSP run ButterflyGuy commit
  `8b1e8913cc45e5fcd0bc2b0a3cee5e01e20a8029`, image
  `sha256:9154ddf82cb1c4841c54c5269408c5c59b965680389be53c50981d393afc8e06`;
- all three use authoritative market data from
  `http://schwab-gateway:8011`;
- all three must remain `paper_trading=true`, `allow_live_trading=false`,
  shadow false, and XSP canary false;
- account, token, transaction, reconciliation, and order operations remain on
  the direct broker client; gateway order writes remain disabled;
- the old gateway and SPX/NDX/XSP images listed in the runbook are retained for
  rollback;
- the scoped consumer secret is in
  `/opt/butterflyguy-gateway-consumer.env` at mode `0600`; never print, copy,
  rotate, or summarize its value.

The deployment occurred after market close. At handoff, every PAPER app was
healthy but `/ready` returned HTTP 503 with exactly
`gateway_market_data_warming`, which is expected until the first fresh
market-open spot, full-chain, and minute-history reads succeed.

Your first task is a read-only next-market-open acceptance check. Do not rebuild,
recreate, restart, or change configuration unless a rollback trigger is proven
and I explicitly approve the mutation.

Verify and report:

1. production gateway exact image, health/readiness, restart count, bounded logs,
   protected admission/rejection metrics, cache metrics, and order-writes=false;
2. exact SPX/NDX/XSP container images, uniqueness, restart counts, PAPER/live
   guards, gateway mode, shadow false, and XSP canary false;
3. `/health` and `/ready` for ports 8000, 8001, and 8003 after the first collector
   cycle; all three must clear `gateway_market_data_warming`;
4. fresh collector evidence for each underlying: spot, option chain, minute
   history, snapshot persistence, and no stale/missing/malformed gateway errors;
5. zero unexpected decision divergence, duplicate processes, token/auth errors,
   gateway 429/504 responses, readiness flapping, or latency that threatens the
   two-second monitoring interval;
6. database OPEN trades and nonterminal broker intents, plus an authenticated
   read-only Schwab audit of SPX/NDX/XSP positions and active/missing/unmapped/
   duplicate order evidence. Never call broker write APIs.

Rollback criteria are persistent warming after fresh market data should be
available, stale/missing data, auth/token degradation, repeated 429/504,
readiness flapping, unsafe latency, or any decision divergence. If a criterion
is observed, stop, preserve evidence, identify the affected component and exact
retained rollback image, and ask for explicit rollback approval before recreating
anything.

Do not enable or place a real-money XSP trade. After PAPER market-open acceptance
passes, separately review and implement a force-fresh option-chain policy for the
real-money workflow, with its own tests, approval, deployment, and rollback plan.

---

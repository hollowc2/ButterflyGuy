# SPX idea sweep — 2026-09-25

Findings are in `docs/research/strategy-discovery-journal.md` (2026-09-25 entries).
`REGISTRY.md` is the variant list, written before round 1 ran; round 2 is marked post-hoc.

## Reproduce

The exported market data (about 140 MB) is not committed. Re-export it read-only from
Helios into this directory's `data/` (or point `SWEEP_DATA` elsewhere), running
the commands below from this directory. Sessions after 2026-09-24 will
also appear; restrict the date range in `variants.py` to match the journal.

```bash
mkdir -p data
ssh -F /dev/null -o BatchMode=yes billy@helios "docker exec -i butterfly_timescaledb psql -U butterfly -d butterfly_guy -q" <<'SQL' | gzip -1 > data/chain.csv.gz
set default_transaction_read_only = on;
copy (select extract(epoch from snapshot_time)::bigint as ts, strike::int as k, left(option_type,1) as t,
  bid, ask, mark, round(iv,4) iv, round(delta,4) delta, spot_price as s
  from option_chain_snapshots where underlying='SPX'
  and expiration = (snapshot_time at time zone 'America/New_York')::date
  and (snapshot_time at time zone 'America/New_York')::time between '09:30' and '16:00'
  and abs(strike - spot_price) <= 200 and strike = round(strike)) to stdout with csv header;
SQL
# spot.csv:  copy (select extract(epoch from ts)::bigint ts, underlying u, price from spot_prices
#            where underlying in ('SPX','$VIX') order by ts) to stdout with csv header;
# daily.csv: copy (select date, underlying u, open, high, low, close from daily_bars
#            where underlying in ('SPX','$VIX') order by date) to stdout with csv header;

../../../.venv/bin/python prep.py   # builds data/chain_days.pkl
../../../.venv/bin/python baseline.py 2026-03-13 2026-09-18   # parity check
../../../.venv/bin/python variants.py   # round 1 -> results.json, e0_trades.csv
../../../.venv/bin/python round2.py     # round 2 (post-hoc) -> results_round2.json
../../../.venv/bin/python lowvix.py && ../../../.venv/bin/python lowvix2.py
../../../.venv/bin/python h2.py && ../../../.venv/bin/python h2b.py
```

Scripts import each other by module name, so run them from this directory.

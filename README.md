# 🦋 Butterfly Guy

![Butterfly Guy Logo](data/images/butterflyguy_logo2.png)

Automated options trading strategy and research platform for 0-DTE SPX, NDX, and XSP butterflies. Designed for high reward-to-risk (R/R) entries on Schwab.

---

## 🚀 Features

- **Multi-Asset Support**: Trade SPX, NDX, or XSP with tailored configurations for each.
- **VIX-Aware Strategy**: Dynamically adjusts wing widths and entry anchors based on market volatility.
- **Flexible Entry Methods**:
  - `VIX`: Anchors the center strike to the VIX-implied 1-sigma move.
  - `TARGET_COST`: Pushes the fly as far OTM as possible until the cost matches your target debit.
  - `BEST_RR`: Selects the candidate with the Reward/Risk closest to your target (e.g., 10:1).
- **Automated Data Collection**: Continuous snapshotting of option chains and spot prices into a TimescaleDB instance.
- **Risk Management**: Layered capital protection including daily/weekly loss limits, consecutive loss circuit breaker, real-time PDT floor enforcement, and buying power validation via Schwab API.
- **Research Tools**: Powerful scripts to inspect historical entries and simulate strategy changes.

---

## 🛡 Risk Management

Butterfly Guy has multiple layers of capital protection, all configurable under the `risk:` block.

| Protection | Config Key | Description |
|---|---|---|
| Daily loss limit | `max_daily_loss` | Halts trading for the day once realized PnL hits this threshold |
| Weekly loss limit | `max_weekly_loss` | Halts trading for the day if rolling 7-day losses exceed this |
| Consecutive loss breaker | `max_consecutive_losses` | Halts after N consecutive losing trades (default: 10) |
| PDT floor | `min_account_value` | Blocks entry if account liquidation value drops below this (default: $25,500) |
| Buying power guard | `min_buying_power` | Blocks entry if available buying power is below this |
| Balance fetch fail-safe | `fail_safe_on_balance_error` | If `true`, blocks trading when the Schwab balance API is unreachable |
| Trade count cap | `max_trades_per_day` | Hard limit on entries per day per underlying |

Account balances are fetched from Schwab before every entry attempt. On restart, any open position's entry cost is included as worst-case committed loss so the daily budget is never silently overspent.

```yaml
risk:
  max_daily_loss: 50.0
  max_weekly_loss: 150.0
  max_consecutive_losses: 10
  min_account_value: 25500.0
  min_buying_power: 200.0
  fail_safe_on_balance_error: true
  max_trades_per_day: 1
```

---

## 🛠 Configuration

Configuration is managed via `config.yaml` (default) or environment-specific files like `config_ndx.yaml`.

### Key Entry Settings

Under the `entry:` block:

```yaml
entry:
  start_time: "07:00"              # PST
  end_time: "07:45"                # PST
  strike_selection_method: "TARGET_COST" # VIX, TARGET_COST, or BEST_RR
  center_tolerance: 15.0           # (VIX mode only) pts tolerance around target
```

### Strategy Settings

Under the `strategy:` block:

```yaml
strategy:
  wing_widths: [10, 20, 30]        # Available butterfly widths
  rr_target: 10.0                  # Ideal Reward/Risk ratio
  max_cost_per_width:              # Cost targets for TARGET_COST mode
    10: 1.00
    20: 2.00
    30: 3.00
```

---

## 📊 Research and Inspection

### Inspecting Historical Entries

Use the `inspect_entry.py` script to see what the bot would have seen on a specific date and which butterfly it would have selected under different methods.

```bash
# Inspect using the default TARGET_COST method
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03

# Compare with the VIX-anchored method
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --method VIX

# Test specific wing widths and R/R filters
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --wing 30 --rr 10.0
```

---

## 📈 Backtesting

Butterfly Guy includes a full simulation engine that replays historical option chain data stored in TimescaleDB, using the same entry/exit logic as the live trader.

### Running a DB Backtest

```bash
# Single day
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-15 2025-01-15 --asset SPX

# Date range
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-01 2025-03-31 --asset SPX

# Sweep all available days across all parameter combinations
uv run python src/butterfly_guy/scripts/run_backtest_db.py --asset SPX --sweep
```

Sweep mode runs the `ParameterSweeper`, which tries every combination of wing widths, drawdown thresholds, and other strategy parameters, then ranks results by Sharpe ratio so you can compare configurations objectively.

### Running Tests

```bash
# Full test suite
uv run pytest

# A specific module
uv run pytest tests/test_strategy.py -v
```

---

## 🐳 Running with Docker

Manage your trading stack using the provided `docker-compose.yml` in the `infra/` directory.

- **Collector (SPX only for VIX)**: Captures market data.
- **Trading App**: Executes the strategy in live or paper modes.

```bash
# Start the SPX stack
docker compose -f infra/docker-compose.yml --profile spx up -d
```

---

## 📜 License

MIT

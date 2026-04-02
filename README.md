# 🦋 Butterfly Guy

![Butterfly Guy Logo](butterflyguy_logo2.png)

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
- **Risk Management**: Built-in daily loss limits and trade count caps.
- **Research Tools**: Powerful scripts to inspect historical entries and simulate strategy changes.

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

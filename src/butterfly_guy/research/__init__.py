"""Unified research core for SPX 0-DTE butterfly studies.

Read-only export of recorded chains into per-session Parquet arrays (`dataset`, `export`),
a fast replay that shares the live entry selection and profit-policy functions
(`market`, `accounting`, `entry`, `exits`, `simulate`), paired and noise-aware
evaluation (`evaluate`, `tieset`), and an append-only variant registry (`registry`).
`SimulationEngine` and `run_backtest_db.py` remain the live-parity reference.
"""

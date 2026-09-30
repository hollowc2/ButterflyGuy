"""Parquet round trip, manifest hashing and dense-grid construction."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from butterfly_guy.research.dataset import (
    Dataset,
    Manifest,
    chain_to_table,
    dense_chain_from_rows,
    table_to_chain,
    write_table,
)
from tests.research_synth import fly_quotes, make_chain, minute


def test_dense_grid_keeps_unrecorded_quotes_missing():
    rows = pd.DataFrame({
        "ts_us": [1, 1, 2], "strike": [100.0, 105.0, 100.0], "t": ["C", "P", "C"],
        "bid": [1.0, 2.0, np.nan], "ask": [1.1, 2.2, 1.2], "mark": [1.05, 2.1, 1.1],
        "iv": [0.1, 0.2, 0.3], "delta": [0.5, -0.4, 0.5], "spot": [101.0, 101.0, 102.0],
    })
    c = dense_chain_from_rows(rows, dt.date(2026, 6, 10))
    assert c.fields["C_bid"].shape == (2, 2)
    assert np.isnan(c.fields["C_bid"][0, 1])  # no C row at 105
    assert np.isnan(c.fields["C_bid"][1, 0])  # recorded as null, stays null
    assert c.fields["C_ask"][1, 0] == 1.2
    assert np.isnan(c.fields["P_mark"][1, 1])
    assert c.spot.tolist() == [101.0, 102.0]


def test_parquet_round_trip_is_exact(tmp_path):
    chain = make_chain([minute(10, 0), minute(10, 1)],
                       fly_quotes(minute(10, 1), (3.05, 3.15), (1.45, 1.55), (0.35, 0.45)))
    entry = write_table(chain_to_table(chain), tmp_path / "c.parquet")
    back = table_to_chain(pq.read_table(tmp_path / "c.parquet"), chain.date)
    assert entry["rows"] == len(chain.ts) * len(chain.strikes)
    assert np.array_equal(back.ts, chain.ts) and np.array_equal(back.strikes, chain.strikes)
    for k, v in chain.fields.items():
        np.testing.assert_array_equal(back.fields[k], v.astype(back.fields[k].dtype))


def _mini_dataset(tmp_path):
    root = tmp_path / "mini"
    chain = make_chain([minute(10, 0)], fly_quotes(minute(10, 0), (1, 1.1), (1, 1.1), (1, 1.1)))
    m = Manifest(dataset="mini", underlying="SPX", source={"kind": "test"}, export={})
    m.files["sessions/2026-06-10/chain.parquet"] = write_table(
        chain_to_table(chain), root / "sessions/2026-06-10/chain.parquet")
    m.save(root / "manifest.json")
    return root, m


def test_manifest_hash_detects_a_modified_file(tmp_path):
    root, m = _mini_dataset(tmp_path)
    ds = Dataset(root)
    assert ds.verify() == [] and ds.hash == m.dataset_hash
    ds.chain(dt.date(2026, 6, 10))
    path = root / "sessions/2026-06-10/chain.parquet"
    path.write_bytes(path.read_bytes() + b"x")
    assert any("sha256 mismatch" in p for p in Dataset(root).verify())
    with pytest.raises(ValueError, match="does not match the manifest"):
        Dataset(root).chain(dt.date(2026, 6, 10))


def test_manifest_rejects_an_edited_file_list(tmp_path):
    root, _ = _mini_dataset(tmp_path)
    text = (root / "manifest.json").read_text().replace('"rows": 6', '"rows": 7')
    body = text.replace(Manifest.load(root / "manifest.json").files[
        "sessions/2026-06-10/chain.parquet"]["sha256"], "0" * 64)
    (root / "manifest.json").write_text(body)
    with pytest.raises(ValueError, match="dataset_hash"):
        Manifest.load(root / "manifest.json")

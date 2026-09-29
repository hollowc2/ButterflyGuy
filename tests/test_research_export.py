"""Export history in the manifest, and the bars-only refresh for pending settlements."""

from __future__ import annotations

import datetime as dt
import io

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.export import ExportPlan, run_export

DAY = dt.date(2026, 6, 10)
TIMES = [f"2026-06-10 14:{m:02d}:00+00" for m in range(0, 60, 5)]


class FakeSource:
    """Answers the export's bounded queries for one session."""

    def __init__(self) -> None:
        self.bars = [("2026-06-09", "SPX", 5990.0, 6010.0, 5980.0, 6000.0),
                     ("2026-06-09", "$VIX", 18.0, 19.0, 17.0, 18.5),
                     ("2026-06-10", "$VIX", 18.5, 19.0, 17.5, 18.0)]
        self.sql: list[str] = []

    def describe(self) -> dict:
        return {"kind": "fake"}

    def close(self) -> None:
        pass

    def copy_csv(self, sql: str) -> bytes:
        self.sql.append(sql)
        out = io.StringIO()
        if "count(distinct snapshot_time)" in sql:
            out.write("n\n60\n")
        elif "distinct on (snapshot_time)" in sql:
            out.write("snapshot_time,spot,spot_min,spot_max\n")
            for t in TIMES:
                out.write(f"{t},6005.0,6005.0,6005.0\n")
        elif "from option_chain_snapshots" in sql:
            out.write("snapshot_time,strike,t,bid,ask,mark,iv,delta,spot\n")
            for t in TIMES:
                for k in (6000, 6010, 6020):
                    out.write(f"{t},{k},C,1.0,1.1,1.05,0.2,0.5,6005.0\n")
        elif "from daily_bars" in sql:
            out.write("date,underlying,open,high,low,close\n")
            for row in self.bars:
                out.write(",".join(str(x) for x in row) + "\n")
        elif "from spot_prices" in sql:
            out.write("ts,underlying,price\n")
            out.write("2026-06-10 13:30:00+00,SPX,6001.0\n2026-06-10 13:30:00+00,$VIX,18.2\n")
        return out.getvalue().encode()


def test_bars_only_refresh_records_the_landed_settlement(tmp_path):
    source = FakeSource()
    first = run_export(source, ExportPlan(DAY, DAY, log=io.StringIO()), tmp_path)
    (h1,) = first.history
    assert h1["sessions_added"] == ["2026-06-10"] and h1["previous_dataset_hash"] is None
    assert h1["pending_settlements"] == ["2026-06-10"]

    source.bars.append(("2026-06-10", "SPX", 6001.0, 6020.0, 5995.0, 6012.5))
    source.sql.clear()
    second = run_export(source, ExportPlan(DAY, DAY, bars_only=True, log=io.StringIO()),
                        tmp_path)
    h2 = second.history[-1]
    assert len(second.history) == 2 and h2["mode"] == "bars_only"
    assert h2["settlements_landed"] == ["2026-06-10"] and h2["pending_settlements"] == []
    assert h2["daily_bars_changes"] == [{"date": "2026-06-10", "underlying": "SPX", "added": {
        "open": 6001.0, "high": 6020.0, "low": 5995.0, "close": 6012.5}}]
    assert list(h2["files_changed"]) == ["daily_bars.parquet"]  # sessions untouched
    assert h2["previous_dataset_hash"] == first.dataset_hash != second.dataset_hash
    assert all("from daily_bars" in q for q in source.sql)  # nothing else was queried

    ds = Dataset(tmp_path / "spx_0dte")
    assert ds.verify() == [] and ds.manifest.history == second.history
    bars = ds.daily_bars()
    assert float(bars[(bars.underlying == "SPX") & (bars.date == DAY)]["close"].iloc[0]) == 6012.5

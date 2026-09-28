"""Event calendar: loading, hashing, validation and the scheduled-before-the-session rule."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
from pathlib import Path

import pytest

from butterfly_guy.research.event_calendar import (
    CALENDAR_PATH,
    COLUMNS,
    EVENT_TYPES,
    EventCalendar,
)

D = dt.date


def _row(**kw: str) -> dict[str, str]:
    base = {c: "" for c in COLUMNS}
    base.update(event_date="2026-06-10", event_type="CPI", release_time_et="08:30",
                kind="scheduled", published_on="2026-05-12",
                published_basis="prior_release_notice", published_source="https://x/prior",
                held="true", reference_period="2026-05", source="https://x/release")
    base.update(kw)
    return base


def _write(tmp_path: Path, rows: list[dict[str, str]], name: str = "market_events_v7.csv",
           columns: tuple[str, ...] = COLUMNS) -> Path:
    path = tmp_path / name
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return path


def test_committed_calendar_loads_and_covers_the_range():
    cal = EventCalendar()
    assert cal.path == CALENDAR_PATH
    assert cal.version == "v1"
    assert cal.sha256 == hashlib.sha256(CALENDAR_PATH.read_bytes()).hexdigest()
    dates = [e.event_date for e in cal.events]
    assert min(dates) >= D(2022, 1, 1) and max(dates) <= D(2026, 12, 31)
    assert min(dates) < D(2022, 1, 31) and max(dates) > D(2026, 12, 1)
    assert {e.event_type for e in cal.events} == set(EVENT_TYPES)
    assert all(e.source and e.published_source for e in cal.events)
    assert all(e.published_on <= e.event_date for e in cal.events)
    meta = cal.meta()
    assert meta == {"file": "market_events_v1.csv", "version": "v1", "sha256": cal.sha256,
                    "rows": len(cal.events)}


def test_committed_calendar_has_a_scheduled_event_of_each_type_every_year():
    cal = EventCalendar()
    for year in range(2022, 2027):
        for t in ("FOMC", "CPI", "NFP", "PCE", "OPEX", "QUARTER_END"):
            n = sum(e.event_type == t and e.event_date.year == year and e.kind != "unscheduled"
                    for e in cal.events)
            assert n >= 4, (year, t, n)


def test_hash_follows_content_and_version_follows_file_name(tmp_path):
    a = EventCalendar(_write(tmp_path, [_row()]))
    b = EventCalendar(_write(tmp_path, [_row(notes="edited")], name="market_events_v8.csv"))
    assert a.version == "v7" and b.version == "v8"
    assert a.sha256 != b.sha256


def test_event_published_on_or_after_the_session_is_invisible_to_it(tmp_path):
    cal = EventCalendar(_write(tmp_path, [
        _row(event_date="2026-06-10", published_on="2026-06-09"),
        _row(event_date="2026-06-11", event_type="NFP", published_on="2026-06-11",
             kind="rescheduled", reference_period="2026-05"),
    ]))
    assert cal.event_types(D(2026, 6, 10)) == ("CPI",)  # published the day before
    assert cal.event_types(D(2026, 6, 11)) == ()  # published on the session itself


def test_unscheduled_events_are_never_features(tmp_path):
    cal = EventCalendar(_write(tmp_path, [
        _row(event_type="FOMC", release_time_et="", kind="unscheduled",
             published_on="2026-05-01", reference_period="", notes="emergency meeting"),
    ]))
    assert cal.events[0].kind == "unscheduled"
    assert cal.events_for(D(2026, 6, 10)) == []


def test_withdrawal_hides_an_event_only_from_later_sessions(tmp_path):
    before = EventCalendar(_write(tmp_path, [
        _row(withdrawn_on="2026-06-09", held="false")], name="a_v1.csv"))
    on_day = EventCalendar(_write(tmp_path, [
        _row(withdrawn_on="2026-06-10", held="false")], name="b_v1.csv"))
    assert before.event_types(D(2026, 6, 10)) == ()
    # Withdrawn on the session itself: at the decision it was still expected.
    assert on_day.event_types(D(2026, 6, 10)) == ("CPI",)


def test_held_is_descriptive_only(tmp_path):
    cal = EventCalendar(_write(tmp_path, [_row(held="false")]))
    assert cal.event_types(D(2026, 6, 10)) == ("CPI",)


def test_release_time_before_entry_is_strict(tmp_path):
    cal = EventCalendar(_write(tmp_path, [
        _row(),
        _row(event_type="OPEX", release_time_et="", reference_period=""),
        _row(event_type="PCE", release_time_et="10:00"),
    ]))
    by_type = {e.event_type: e for e in cal.events}
    assert by_type["CPI"].before(dt.time(10, 0)) is True
    assert by_type["PCE"].before(dt.time(10, 0)) is False
    assert by_type["OPEX"].before(dt.time(10, 0)) is None


@pytest.mark.parametrize("change, message", [
    ({"event_type": "GDP"}, "event_type"),
    ({"kind": "tentative"}, "kind"),
    ({"published_basis": "rumour"}, "published_basis"),
    ({"published_on": "2026-06-11"}, "published_on is after"),
    ({"withdrawn_on": "2026-05-01"}, "withdrawn_on"),
    ({"withdrawn_on": "2026-06-11"}, "withdrawn_on"),
    ({"withdrawn_on": "2026-06-01", "held": "true"}, "withdrawn"),
    ({"held": "yes"}, "held"),
    ({"release_time_et": "8:30"}, "release_time_et"),
    ({"reference_period": "2026-13"}, "reference_period"),
    ({"source": " "}, "source"),
    ({"event_date": "2026-02-30"}, "event_date"),
])
def test_invalid_rows_are_rejected(tmp_path, change, message):
    with pytest.raises(ValueError, match=message):
        EventCalendar(_write(tmp_path, [_row(**change)]))


def test_file_level_checks(tmp_path):
    with pytest.raises(ValueError, match="columns"):
        EventCalendar(_write(tmp_path, [], columns=COLUMNS[:-1]))
    with pytest.raises(ValueError, match="duplicate"):
        EventCalendar(_write(tmp_path, [_row(), _row()]))
    with pytest.raises(ValueError, match="sorted"):
        EventCalendar(_write(tmp_path, [_row(event_date="2026-06-11"), _row()]))

"""Versioned table of scheduled market events, loaded as a hashed research input.

`data/market_events_v<N>.csv` (committed) holds one row per event announcement:

    event_date        session the event falls on (ISO date)
    event_type        FOMC | CPI | NFP | PCE | OPEX | QUARTER_END | EARLY_CLOSE
    release_time_et   HH:MM ET (08:30 releases, 14:00 FOMC statement, 13:00 early close),
                      blank for OPEX and quarter-end
    kind              scheduled | rescheduled | unscheduled
    published_on      date the schedule (or reschedule notice) was public
    published_basis   press_release | schedule_doc | prior_release_notice | notice |
                      wayback_first_capture | rule
    published_source  URL or publication showing `published_on`
    withdrawn_on      date a postponement or cancellation of this date was announced
    held              true | false | blank (not yet known); descriptive only
    reference_period  data month for releases (YYYY-MM), blank otherwise
    source            URL or publication showing the event date
    notes             free text

`published_on` is the earliest evidence found that the date was public. When only an
archive capture is available it is an upper bound on the real publication date, so it
can hide an event from a session but never reveal one early.

**Leakage rule.** A row is visible to session S only when it is not `unscheduled`,
`published_on < S`, and it had not been withdrawn before S (`withdrawn_on` empty or
`>= S`). `held` is never used: a release that was expected on S and then did not happen
is still an expected event for S. Unscheduled rows (emergency meetings, notation votes)
are kept for the record and never become features.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CALENDAR_PATH = DATA_DIR / "market_events_v1.csv"

COLUMNS = ("event_date", "event_type", "release_time_et", "kind", "published_on",
           "published_basis", "published_source", "withdrawn_on", "held",
           "reference_period", "source", "notes")
EVENT_TYPES = ("FOMC", "CPI", "NFP", "PCE", "OPEX", "QUARTER_END", "EARLY_CLOSE")
KINDS = ("scheduled", "rescheduled", "unscheduled")
BASES = ("press_release", "schedule_doc", "prior_release_notice", "notice",
         "wayback_first_capture", "rule")
_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class MarketEvent:
    event_date: dt.date
    event_type: str
    release_time_et: dt.time | None
    kind: str
    published_on: dt.date
    published_basis: str
    published_source: str
    withdrawn_on: dt.date | None
    held: bool | None
    reference_period: str
    source: str
    notes: str

    def visible_to(self, session: dt.date) -> bool:
        """The leakage rule: may a decision on `session` know about this event?"""
        return (self.kind != "unscheduled" and self.published_on < session
                and (self.withdrawn_on is None or self.withdrawn_on >= session))

    def before(self, t: dt.time) -> bool | None:
        """Whether the event's release time is strictly before `t` (None if it has none):
        a 10:00 release is not known to a 10:00 decision."""
        return None if self.release_time_et is None else self.release_time_et < t


def _date(value: str, field: str, line: int) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"line {line}: bad {field} {value!r}") from exc


def parse_row(row: dict[str, str], line: int) -> MarketEvent:
    """Validate one CSV row; raises ValueError naming the line."""
    def fail(msg: str) -> ValueError:
        return ValueError(f"line {line}: {msg}")

    event_date = _date(row["event_date"], "event_date", line)
    if row["event_type"] not in EVENT_TYPES:
        raise fail(f"unknown event_type {row['event_type']!r}")
    if row["kind"] not in KINDS:
        raise fail(f"unknown kind {row['kind']!r}")
    if row["published_basis"] not in BASES:
        raise fail(f"unknown published_basis {row['published_basis']!r}")
    t = row["release_time_et"]
    if t and not _TIME.match(t):
        raise fail(f"bad release_time_et {t!r}")
    published = _date(row["published_on"], "published_on", line)
    if published > event_date:
        raise fail("published_on is after the event")
    withdrawn = _date(row["withdrawn_on"], "withdrawn_on", line) if row["withdrawn_on"] else None
    if withdrawn is not None and not published <= withdrawn <= event_date:
        raise fail("withdrawn_on must fall between published_on and the event date")
    held = {"true": True, "false": False, "": None}.get(row["held"])
    if row["held"] not in ("true", "false", ""):
        raise fail(f"held must be true, false or blank, not {row['held']!r}")
    if withdrawn is not None and held:
        raise fail("a withdrawn event cannot have been held")
    if row["reference_period"] and not _PERIOD.match(row["reference_period"]):
        raise fail(f"bad reference_period {row['reference_period']!r}")
    if not row["source"].strip() or not row["published_source"].strip():
        raise fail("source and published_source are required")
    return MarketEvent(
        event_date=event_date, event_type=row["event_type"],
        release_time_et=dt.time.fromisoformat(t) if t else None, kind=row["kind"],
        published_on=published, published_basis=row["published_basis"],
        published_source=row["published_source"], withdrawn_on=withdrawn, held=held,
        reference_period=row["reference_period"], source=row["source"], notes=row["notes"],
    )


class EventCalendar:
    """A loaded, validated calendar file with its content hash."""

    def __init__(self, path: Path = CALENDAR_PATH) -> None:
        self.path = Path(path)
        data = self.path.read_bytes()
        self.sha256 = hashlib.sha256(data).hexdigest()
        reader = csv.DictReader(data.decode("utf-8").splitlines())
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError(f"{self.path.name}: columns must be {', '.join(COLUMNS)}")
        self.events = [parse_row(row, i) for i, row in enumerate(reader, start=2)]
        keys = [(e.event_date, e.event_type, e.kind, e.reference_period) for e in self.events]
        if len(set(keys)) != len(keys):
            raise ValueError(f"{self.path.name}: duplicate rows")
        if keys != sorted(keys, key=lambda k: (k[0], k[1])):
            raise ValueError(f"{self.path.name}: rows must be sorted by event_date, event_type")

    @property
    def version(self) -> str:
        m = re.search(r"_v(\d+)\.csv$", self.path.name)
        return f"v{m.group(1)}" if m else self.path.stem

    @cached_property
    def _by_date(self) -> dict[dt.date, list[MarketEvent]]:
        out: dict[dt.date, list[MarketEvent]] = {}
        for e in self.events:
            out.setdefault(e.event_date, []).append(e)
        return out

    def events_for(self, session: dt.date) -> list[MarketEvent]:
        """Events on `session` that a decision on `session` could know about."""
        return [e for e in self._by_date.get(session, []) if e.visible_to(session)]

    def event_types(self, session: dt.date) -> tuple[str, ...]:
        """The per-session `events` feature: sorted distinct visible event types."""
        return tuple(sorted({e.event_type for e in self.events_for(session)}))

    def meta(self) -> dict:
        """What a run records when it uses the calendar (like the config hash)."""
        return {"file": self.path.name, "version": self.version, "sha256": self.sha256,
                "rows": len(self.events)}

#!/usr/bin/env python3
"""Build the research event calendar from public sources.

    uv run python tools/build_market_events.py [--cache DIR] [--today YYYY-MM-DD]

writes `src/butterfly_guy/research/data/market_events_v<N>.csv` (see
`butterfly_guy.research.event_calendar` for the columns and the leakage rule). Every
fetched page is cached under `--cache` with its effective URL, so a rebuild is
reproducible from the cache and each row cites the page it came from.

Sources and how `published_on` is established:

- FOMC: the Fed's meeting calendar (statement day = the meeting's last day, 14:00 ET)
  and the press release announcing each year's tentative schedule (`press_release`).
  Notation votes are `unscheduled`.
- CPI and NFP (BLS Employment Situation): the archived news releases. Each release
  names the next release's date, so a date's `published_on` is the release that
  announced it (`prior_release_notice`). BLS blocks scripted access, so pages are read
  through Internet Archive replays of bls.gov; the archive URL is recorded.
- PCE (BEA Personal Income and Outlays): the release pages, whose "Next release" line
  plays the same role.
- Reschedules and cancellations (the 2025 and 2026 appropriations lapses, and BEA's
  2026 schedule changes) come from the dated notices in `NOTICES`. When a notice is only
  known from an archive capture, the capture date is used: an upper bound on the real
  announcement date, which can hide an event from a session but never reveal it early.
  A withdrawal with no dated notice before the event is recorded on the event date.
- Dates after the last release so far come from the agencies' current schedule pages,
  dated by the day they were fetched.
- OPEX (third Friday, the preceding session when that Friday is an exchange holiday),
  quarter-end (last session of the quarter) and early closes: the NYSE holidays page.
  `published_on` is the earliest archived copy of that page listing the year.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "butterfly_guy" / "research" / "data" / "market_events_v1.csv"
DEFAULT_CACHE = (Path.home() / ".cache" / "butterfly_guy" / "research" / "_sources"
                 / "market_events")
FIRST, LAST = dt.date(2022, 1, 1), dt.date(2026, 12, 31)
COLUMNS = ("event_date", "event_type", "release_time_et", "kind", "published_on",
           "published_basis", "published_source", "withdrawn_on", "held",
           "reference_period", "source", "notes")
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MON = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
WAYBACK = "https://web.archive.org/web/{ts}id_/{url}"

FED_CALENDAR = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FED_SCHEDULE_RELEASES = {  # schedule year -> tentative-schedule press release
    2022: "https://www.federalreserve.gov/newsevents/pressreleases/monetary20210604a.htm",
    2023: "https://www.federalreserve.gov/newsevents/pressreleases/monetary20220624a.htm",
    2024: "https://www.federalreserve.gov/newsevents/pressreleases/monetary20230623a.htm",
    2025: "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240809a.htm",
    2026: "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240809a.htm",
}
BLS_INDEX = {"CPI": "https://www.bls.gov/bls/news-release/cpi.htm",
             "NFP": "https://www.bls.gov/bls/news-release/empsit.htm"}
BLS_RELEASE = {"CPI": "https://www.bls.gov/news.release/archives/cpi_{mmddyyyy}.htm",
               "NFP": "https://www.bls.gov/news.release/archives/empsit_{mmddyyyy}.htm"}
BLS_SCHEDULE = {"CPI": "https://www.bls.gov/schedule/news_release/cpi.htm",
                "NFP": "https://www.bls.gov/schedule/news_release/empsit.htm"}
BEA_RELEASE = "https://www.bea.gov/news/{year}/personal-income-and-outlays-{slug}"
BEA_SCHEDULE = "https://www.bea.gov/news/schedule"
NYSE_HOURS = "https://www.nyse.com/markets/hours-calendars"
NYSE_CAPTURES = ("20210601", "20220601", "20230601", "20240601", "20250601")
LAPSE = "https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm"


@dataclass(frozen=True)
class Notice:
    """A dated announcement that moved or cancelled a release."""

    revised: dt.date | None  # None: cancelled
    revised_time: str
    published_on: dt.date | None  # when the revised date was public
    published_source: str
    withdrawn_on: dt.date | None  # when the original date was withdrawn (None: unknown)
    withdrawn_source: str
    note: str


def _wb(ts: str, url: str) -> str:
    return WAYBACK.format(ts=ts, url=url)


# (series, reference month) -> notice. Capture timestamps are the earliest archived copies
# found that carry the change; see the module docstring.
NOTICES: dict[tuple[str, str], Notice] = {
    ("CPI", "2025-09"): Notice(
        dt.date(2025, 10, 24), "08:30", dt.date(2025, 10, 12),
        _wb("20251012085353", "https://www.bls.gov/cpi/"), dt.date(2025, 10, 12),
        _wb("20251012085353", "https://www.bls.gov/cpi/"),
        "2025 lapse in appropriations; CPI home page 'Next Release' notice (the 2025-10-09 "
        "capture does not have it)"),
    ("CPI", "2025-10"): Notice(
        None, "", None, "", None, _wb("20251121165438", LAPSE),
        "cancelled (2025 lapse); first listed as cancelled in the 2025-11-21 capture, after "
        "the original date, so the withdrawal is recorded on the event date"),
    ("CPI", "2025-11"): Notice(
        dt.date(2025, 12, 18), "08:30", dt.date(2025, 11, 21), _wb("20251121165438", LAPSE),
        dt.date(2025, 11, 21), _wb("20251121165438", LAPSE),
        "2025 lapse; originally scheduled 2025-12-10 (annual schedule)"),
    ("CPI", "2026-01"): Notice(
        dt.date(2026, 2, 13), "08:30", dt.date(2026, 2, 5), _wb("20260205224201", LAPSE),
        dt.date(2026, 2, 5), _wb("20260205224201", LAPSE),
        "2026 lapse in appropriations (not in the 2026-02-03 capture)"),
    ("NFP", "2025-09"): Notice(
        dt.date(2025, 11, 20), "08:30", dt.date(2025, 11, 16), _wb("20251116071537", LAPSE),
        None, _wb("20251116071537", LAPSE),
        "2025 lapse; no dated notice before the original 2025-10-03 date"),
    ("NFP", "2025-10"): Notice(
        None, "", None, "", None, _wb("20251121165438", LAPSE),
        "cancelled (2025 lapse); October payrolls published with November"),
    ("NFP", "2025-11"): Notice(
        dt.date(2025, 12, 16), "08:30", dt.date(2025, 11, 21), _wb("20251121165438", LAPSE),
        dt.date(2025, 11, 21), _wb("20251121165438", LAPSE),
        "2025 lapse; originally scheduled 2025-12-05 (annual schedule)"),
    ("NFP", "2026-01"): Notice(
        dt.date(2026, 2, 11), "08:30", dt.date(2026, 2, 5), _wb("20260205224201", LAPSE),
        dt.date(2026, 2, 5), _wb("20260205224201", LAPSE),
        "2026 lapse in appropriations (not in the 2026-02-03 capture)"),
    ("PCE", "2025-09"): Notice(
        dt.date(2025, 12, 5), "10:00", dt.date(2025, 11, 24),
        "https://www.bea.gov/news/blog/2025-11-24/economic-release-schedule-updates",
        None, "https://www.bea.gov/news/blog/2025-11-24/economic-release-schedule-updates",
        "2025 lapse; originally 2025-10-31; no dated notice before that date"),
    ("PCE", "2025-10"): Notice(
        None, "", None, "", dt.date(2025, 11, 20),
        "https://www.bea.gov/news/blog/2025-11-20/economic-release-schedule-updates-gdp-and-"
        "personal-income-and-outlays",
        "originally 2025-11-26; combined with November into the 2026-01-22 release"),
    ("PCE", "2025-11"): Notice(
        dt.date(2026, 1, 22), "10:00", dt.date(2026, 1, 7),
        "https://www.bea.gov/news/blog/2026-01-07/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", None, "",
        "October and November 2025 combined; November originally 2025-12-19"),
    ("PCE", "2025-12"): Notice(
        dt.date(2026, 2, 20), "08:30", dt.date(2026, 1, 7),
        "https://www.bea.gov/news/blog/2026-01-07/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", dt.date(2026, 1, 7),
        "https://www.bea.gov/news/blog/2026-01-07/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", "originally 2026-01-29"),
    ("PCE", "2026-01"): Notice(
        dt.date(2026, 3, 13), "08:30", dt.date(2026, 1, 15),
        "https://www.bea.gov/news/blog/2026-01-15/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", dt.date(2026, 1, 7),
        "https://www.bea.gov/news/blog/2026-01-07/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", "originally 2026-02-26"),
    ("PCE", "2026-02"): Notice(
        dt.date(2026, 4, 9), "08:30", dt.date(2026, 1, 15),
        "https://www.bea.gov/news/blog/2026-01-15/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", dt.date(2026, 1, 15),
        "https://www.bea.gov/news/blog/2026-01-15/economic-release-schedule-updates-gdp-"
        "personal-income-and-outlays", "originally 2026-03-27"),
}


class Fetcher:
    """Cached, throttled page fetches; returns (text, effective URL, fetched date)."""

    def __init__(self, cache: Path, delay: float = 2.0) -> None:
        self.cache, self.delay = cache, delay
        cache.mkdir(parents=True, exist_ok=True)

    def get(self, url: str, *, required: bool = True) -> tuple[str, str, dt.date] | None:
        key = self.cache / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
        if key.exists():
            rec = json.loads(key.read_text())
            return rec["body"], rec["effective"], dt.date.fromisoformat(rec["fetched_at"][:10])
        for attempt in range(4):
            p = subprocess.run(
                ["curl", "-sSL", "--compressed", "-m", "90", "-A", "Mozilla/5.0",
                 "-w", "\n%{http_code} %{url_effective}", url], capture_output=True)
            body, _, tail = p.stdout.decode(errors="replace").rpartition("\n")
            code, _, effective = tail.partition(" ")
            time.sleep(self.delay)
            if code == "200" and len(body) > 2000 and "Temporarily Offline" not in body:
                now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
                key.write_text(json.dumps({"url": url, "effective": effective,
                                           "fetched_at": now, "body": body}))
                return body, effective, dt.date.fromisoformat(now[:10])
            if code == "404":
                break
            time.sleep(5 * (attempt + 1))
        if required:
            raise RuntimeError(f"could not fetch {url}")
        return None


def text_of(page: str, sep: str = " ") -> str:
    b = html.unescape(re.sub(r"<[^>]+>", sep, page))
    return re.sub(r"(\s*\|\s*)+", " | ", b) if sep == " | " else re.sub(r"\s+", " ", b)


def parse_day(s: str) -> dt.date:
    s = s.replace(".", "").title().replace("Sept ", "Sep ")
    m = re.match(r"([A-Z][a-z]+) (\d{1,2}),? (\d{4})", s)
    if not m:
        raise ValueError(f"cannot parse date {s!r}")
    return dt.date(int(m.group(3)), MON[m.group(1)[:3]], int(m.group(2)))


def capture_date(effective: str, fetched: dt.date) -> dt.date:
    m = re.search(r"/web/(\d{8})", effective)
    return dt.date(int(m.group(1)[:4]), int(m.group(1)[4:6]), int(m.group(1)[6:8])) if m \
        else fetched


def hhmm(t: str, ampm: str) -> str:
    h, m = (int(x) for x in t.split(":"))
    h = h % 12 + (12 if ampm.lower().startswith("p") else 0)
    return f"{h:02d}:{m:02d}"


def ref_add(ref: str, months: int) -> str:
    y, m = (int(x) for x in ref.split("-"))
    k = y * 12 + m - 1 + months
    return f"{k // 12}-{k % 12 + 1:02d}"


@dataclass
class Row:
    event_date: dt.date
    event_type: str
    release_time_et: str
    kind: str
    published_on: dt.date
    published_basis: str
    published_source: str
    source: str
    withdrawn_on: dt.date | None = None
    held: bool | None = None
    reference_period: str = ""
    notes: str = ""

    def csv(self) -> dict[str, str]:
        return {"event_date": self.event_date.isoformat(), "event_type": self.event_type,
                "release_time_et": self.release_time_et, "kind": self.kind,
                "published_on": self.published_on.isoformat(),
                "published_basis": self.published_basis,
                "published_source": self.published_source,
                "withdrawn_on": self.withdrawn_on.isoformat() if self.withdrawn_on else "",
                "held": "" if self.held is None else str(self.held).lower(),
                "reference_period": self.reference_period, "source": self.source,
                "notes": self.notes}


# ---------------------------------------------------------------------------
# FOMC
# ---------------------------------------------------------------------------


def fomc_rows(f: Fetcher, today: dt.date) -> list[Row]:
    page, _, _ = f.get(FED_CALENDAR)
    rows: list[Row] = []
    releases = {y: text_of(f.get(u)[0]) for y, u in FED_SCHEDULE_RELEASES.items()}
    years = re.split(r'<h4><a id="\d+">(\d{4}) FOMC Meetings</a></h4>', page)
    for year_s, body in zip(years[1::2], years[2::2], strict=True):
        year = int(year_s)
        if not FIRST.year <= year <= LAST.year:
            continue
        blocks = re.split(r'(?=<div class="[^"]*row fomc-meeting")', body)
        before = len(rows)
        for block in blocks:
            m = re.search(r'fomc-meeting__month[^>]*><strong>([^<]+)</strong>.*?'
                          r'fomc-meeting__date[^>]*>([^<]+)<', block, re.S)
            if not m:
                continue
            months, days = m.group(1).strip(), html.unescape(m.group(2)).strip()
            statement = "Statement:" in block
            last_month = months.split("/")[-1]
            first_month = months.split("/")[0]
            month_no = next(i + 1 for i, name in enumerate(MONTHS) if name.startswith(last_month))
            if "notation vote" in days:
                day = int(re.match(r"\d+", days).group(0))
                date = dt.date(year, month_no, day)
                rows.append(Row(date, "FOMC", "", "unscheduled", date, "notice",
                                FED_CALENDAR, FED_CALENDAR, held=True,
                                notes=f"notation vote ({text_of(block).strip()[:80]})"))
                continue
            d1, d2 = re.match(r"(\d+)-(\d+)", days).groups()
            date = dt.date(year, month_no, int(d2))
            start = next(n for n in MONTHS if n.startswith(first_month))
            release = releases[year]
            if f"{start} {int(d1)}" not in release:
                raise ValueError(f"FOMC {date}: {start} {d1} not in the {year} schedule release")
            pr = FED_SCHEDULE_RELEASES[year]
            published = dt.date(int(pr[-13:-9]), int(pr[-9:-7]), int(pr[-7:-5]))
            rows.append(Row(date, "FOMC", "14:00", "scheduled", published, "press_release", pr,
                            FED_CALENDAR, held=True if statement else (None if date >= today
                                                                        else False),
                            notes="SEP meeting" if "*" in days else ""))
        if sum(r.kind == "scheduled" for r in rows[before:]) != 8:
            raise ValueError(f"FOMC {year}: expected 8 scheduled meetings")
    return rows


# ---------------------------------------------------------------------------
# BLS (CPI, NFP) and BEA (PCE): releases, next-release notices and notices
# ---------------------------------------------------------------------------


@dataclass
class Release:
    ref: str
    date: dt.date
    time: str
    url: str  # archive URL actually read
    next_date: dt.date | None = None
    next_time: str = ""
    next_ref: str | None = None


_NEXT_BLS = re.compile(
    r"(?:Consumer Price Index|CPI|Employment Situation)[^.]{0,40}? for ([A-Z][a-z]+(?: \d{4})?)"
    r" (?:is|are) scheduled to be (?:released|published) on (?:[A-Z][a-z]+, )?"
    r"([A-Z][a-z]+\.? \d{1,2}, \d{4})"
    r",? at (\d{1,2}:\d{2}) ?([ap])\.? ?m")


def bls_releases(f: Fetcher, series: str, today: dt.date) -> list[Release]:
    idx, idx_url, _ = f.get(_wb("2026", BLS_INDEX[series]))
    stem = "cpi" if series == "CPI" else "empsit"
    pending = sorted({dt.date(int(s[4:]), int(s[:2]), int(s[2:4]))
                      for s in re.findall(stem + r"_(\d{8})\.htm", idx)})
    out: list[Release] = []
    seen: set[dt.date] = set()
    while pending:
        d = pending.pop(0)
        if d in seen or not dt.date(2021, 11, 1) <= d <= min(today, LAST):
            continue
        seen.add(d)
        url = BLS_RELEASE[series].format(mmddyyyy=d.strftime("%m%d%Y"))
        got = f.get(_wb("2026", url), required=False)
        if got is None:
            if stem + d.strftime("_%m%d%Y") in idx:
                # Listed in the archived release index but no archived copy of the page:
                # the index is the evidence it was released; its notice is unknown.
                prev = d.replace(day=1) - dt.timedelta(days=1)
                out.append(Release(f"{prev.year}-{prev.month:02d}", d, "08:30", idx_url))
            continue
        page, effective, _ = got
        t = text_of(page)
        # Provisional reference month: the title's "YYYY Mnn Results" (titles also say
        # "Q01" or "M13"); else a documented reschedule to this date; else the month before
        # the release. The announcing release's notice overrides it below.
        m = re.search(r"(\d{4}) M(0[1-9]|1[0-2]) Results", t)
        ref = f"{m.group(1)}-{m.group(2)}" if m else next(
            (r for (s_, r), n in NOTICES.items() if s_ == series and n.revised == d), None)
        if ref is None:
            prev = d.replace(day=1) - dt.timedelta(days=1)
            ref = f"{prev.year}-{prev.month:02d}"
        rel = Release(ref, d, "08:30", effective)
        nm = _NEXT_BLS.search(t)
        if nm:
            rel.next_date = parse_day(nm.group(2))
            rel.next_time = hhmm(nm.group(3), nm.group(4))
            name = nm.group(1)
            month = MON[name[:3]]
            # The reference month is the latest such month before the release date.
            year = int(name[-4:]) if name[-4:].isdigit() else (
                rel.next_date.year if month < rel.next_date.month else rel.next_date.year - 1)
            rel.next_ref = f"{year}-{month:02d}"
            # A release newer than the archived index: read it from its announced date.
            if rel.next_date not in seen and rel.next_date not in pending:
                pending.append(rel.next_date)
                pending.sort()
        out.append(rel)
    announced = {r.next_date: r.next_ref for r in out if r.next_date}
    for r in out:
        r.ref = announced.get(r.date, r.ref)
    return sorted(out, key=lambda r: r.date)


def bea_releases(f: Fetcher) -> list[Release]:
    out = []
    refs = [f"{y}-{m:02d}" for y in range(2021, 2027) for m in range(1, 13)]
    refs = [r for r in refs if "2021-11" <= r <= "2026-12"]
    slugs = {r: [f"{MONTHS[int(r[5:]) - 1].lower()}-{r[:4]}",
                 f"{MONTHS[int(r[5:]) - 1].lower()}-{r[:4]}-and-annual-update"] for r in refs}
    slugs["2025-11"] = ["october-and-november-2025"]
    slugs["2025-10"] = []
    for ref in refs:
        y = int(ref[:4])
        for slug in slugs[ref]:
            if any(r.ref == ref for r in out):
                break
            got = None
            for year in (y, y + 1):
                got = f.get(BEA_RELEASE.format(year=year, slug=slug), required=False)
                if got and "EMBARGOED" in got[0].upper():
                    break
                got = None
            if got is None:
                continue
            page, effective, _ = got
            t = text_of(page)
            m = re.search(r"EMBARGOED UNTIL RELEASE AT (\d{1,2}:\d{2}) ([ap])\.m\. E[SD]T,? "
                          r"[A-Za-z]+,? ([A-Z][a-z]+ \d{1,2}, \d{4})", t, re.I)
            if not m:
                raise ValueError(f"{effective}: no embargo line")
            rel = Release(ref, parse_day(m.group(3)), hhmm(m.group(1), m.group(2)), effective)
            nm = re.search(r"Next release: ?:? ?([A-Z][a-z]+ \d{1,2}, \d{4})(?:,? at (\d{1,2}:\d{2}) "
                           r"([ap])\.m\.)?", t)
            if nm:
                rel.next_date = parse_day(nm.group(1))
                rel.next_time = hhmm(nm.group(2), nm.group(3)) if nm.group(2) else "08:30"
                rel.next_ref = ref_add(ref, 1)
            out.append(rel)
    return out


def schedule_dates(f: Fetcher, series: str, today: dt.date) -> tuple[list[tuple[str, dt.date,
                                                                              str]], str, dt.date]:
    """(ref, date, time) from an agency's current schedule page, and its evidence date."""
    if series == "PCE":
        page, effective, fetched = f.get(BEA_SCHEDULE)
        t = text_of(page, " | ")
        out = []
        for m in re.finditer(r"Personal Income and Outlays, ([A-Z][a-z]+) (\d{4}) \| "
                             r"([A-Z][a-z]+ \d{1,2}) \| (\d{1,2}:\d{2}) ([AP])M", t):
            ref = f"{m.group(2)}-{MON[m.group(1)[:3]]:02d}"
            day = parse_day(f"{m.group(3)}, {int(m.group(2)) + (1 if m.group(1) == 'December' else 0)}")
            out.append((ref, day, hhmm(m.group(4), m.group(5))))
        return out, effective, fetched
    got = None
    # Some archive captures of these pages are empty; the blsmon1 mirror is the fallback.
    for url in (_wb("2026", BLS_SCHEDULE[series]), _wb("20260915", BLS_SCHEDULE[series]),
                _wb("20260801", BLS_SCHEDULE[series]),
                BLS_SCHEDULE[series].replace("www.bls.gov", "blsmon1.bls.gov")):
        got = f.get(url, required=False)
        if got is not None and "Release Date" in got[0]:
            break
    if got is None:
        raise RuntimeError(f"no usable copy of {BLS_SCHEDULE[series]}")
    page, effective, fetched = got
    t = text_of(page, " | ")
    out = []
    for m in re.finditer(r"\| ([A-Z][a-z]+) (\d{4}) \| ([A-Z][a-z]+\.? \d{1,2}, \d{4}) \| "
                         r"(\d{2}:\d{2}) ([AP])M", t):
        out.append((f"{m.group(2)}-{MON[m.group(1)[:3]]:02d}", parse_day(m.group(3)),
                    hhmm(m.group(4), m.group(5))))
    return out, effective, capture_date(effective, fetched)


def release_rows(series: str, releases: list[Release], sched: list[tuple[str, dt.date, str]],
                 sched_source: str, sched_date: dt.date, today: dt.date) -> list[Row]:
    rows: list[Row] = []
    actual = {r.ref: r for r in releases}
    announced: dict[str, Release] = {}  # ref -> the release that announced its date
    for r in sorted(releases, key=lambda r: r.date):
        if r.next_ref:
            announced[r.next_ref] = r
    refs = sorted(set(actual) | set(announced) | {s[0] for s in sched})
    for ref in refs:
        a, n = actual.get(ref), announced.get(ref)
        notice = NOTICES.get((series, ref))
        if a is not None and n is not None and n.next_date == a.date and notice is None:
            rows.append(Row(a.date, series, a.time, "scheduled", n.date, "prior_release_notice",
                            n.url, a.url, held=True, reference_period=ref))
            continue
        if notice is None:
            s = [x for x in sched if x[0] == ref]
            if a is None and n is not None and n.next_date >= today and (
                    not s or s[0][1] == n.next_date):
                rows.append(Row(n.next_date, series, n.next_time, "scheduled", n.date,
                                "prior_release_notice", n.url, n.url, held=None,
                                reference_period=ref))
                continue
            if a is None and n is None:
                for s_ref, s_day, s_time in sched:
                    if s_ref == ref and s_day > today:
                        rows.append(Row(s_day, series, s_time, "scheduled", sched_date,
                                        "schedule_doc", sched_source, sched_source,
                                        reference_period=ref))
                continue
            if a is not None and n is None and a.date < dt.date(2022, 1, 1):
                continue
            # A schedule change after the last notice (e.g. BEA's current schedule page)
            if a is None and n is not None and s and s[0][1] != n.next_date:
                rows.append(Row(n.next_date, series, n.next_time, "scheduled", n.date,
                                "prior_release_notice", n.url, n.url,
                                withdrawn_on=min(sched_date, n.next_date), held=False,
                                reference_period=ref,
                                notes=f"moved to {s[0][1]} on the current schedule page"))
                rows.append(Row(s[0][1], series, s[0][2], "rescheduled", sched_date,
                                "schedule_doc", sched_source, sched_source,
                                reference_period=ref, notes=f"originally {n.next_date}"))
                continue
            raise ValueError(f"{series} {ref}: release {a and a.date}, notice "
                             f"{n and n.next_date}; add a NOTICES entry")
        # A documented reschedule or cancellation.
        if n is not None and (notice.revised is None or n.next_date != notice.revised):
            withdrawn = n.next_date if notice.withdrawn_on is None else min(
                notice.withdrawn_on, n.next_date)
            rows.append(Row(n.next_date, series, n.next_time, "scheduled", n.date,
                            "prior_release_notice", n.url, n.url, withdrawn_on=withdrawn,
                            held=False, reference_period=ref, notes=notice.note))
        if notice.revised is not None:
            if a is not None and a.date != notice.revised:
                raise ValueError(f"{series} {ref}: released {a.date}, notice says "
                                 f"{notice.revised}")
            published = notice.published_on
            basis, src = "notice", notice.published_source
            if n is not None and n.next_date == notice.revised and n.date < published:
                published, basis, src = n.date, "prior_release_notice", n.url
            rows.append(Row(notice.revised, series, notice.revised_time, "rescheduled", published,
                            basis, src, a.url if a else src,
                            held=True if a else None, reference_period=ref, notes=notice.note))
    return rows


# ---------------------------------------------------------------------------
# NYSE: holidays, early closes, OPEX, quarter-end
# ---------------------------------------------------------------------------


def nyse_calendars(f: Fetcher) -> list[tuple[dt.date, str, set[dt.date], set[dt.date],
                                              list[int]]]:
    """[(evidence date, source URL, holidays, early closes, years listed)] per copy."""
    out = []
    pages = [f.get(_wb(ts, NYSE_HOURS)) for ts in NYSE_CAPTURES] + [f.get(NYSE_HOURS)]
    for page, effective, fetched in pages:
        t = text_of(page, " | ")
        m = re.search(r"\| Holiday \| (\d{4}) \| (\d{4}) \| (\d{4}) \|", t)
        years = [int(m.group(i)) for i in (1, 2, 3)]
        body = t[m.end():t.find("Trading Hours", m.end())]
        holidays: set[dt.date] = set()
        cells = [c.strip() for c in body.split("|")]
        date_re = re.compile(r"(?:[A-Z][a-z]+, )?([A-Z][a-z]+) (\d{1,2})(?:, (\d{4}))?")
        i = 0
        while i < len(cells):
            if cells[i] and not date_re.match(cells[i]) and not cells[i].startswith(("*", "—")) \
                    and i + 3 < len(cells):
                for k, y in enumerate(years):
                    dm = date_re.match(cells[i + 1 + k])
                    if dm and dm.group(1) in MONTHS:
                        holidays.add(dt.date(int(dm.group(3) or y), MON[dm.group(1)[:3]],
                                             int(dm.group(2))))
                i += 4
            else:
                i += 1
        early = set()
        for sentence in re.findall(r"[^|]*close early[^|]*", t):
            for dm in re.finditer(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", sentence):
                if dm.group(1) in MONTHS:
                    early.add(dt.date(int(dm.group(3)), MON[dm.group(1)[:3]], int(dm.group(2))))
        out.append((capture_date(effective, fetched), effective, holidays, early, years))
    return out


def market_rows(f: Fetcher, today: dt.date) -> list[Row]:
    copies = nyse_calendars(f)
    rows: list[Row] = []
    for year in range(FIRST.year, LAST.year + 1):
        listing = [c for c in copies if year in c[4]]
        if not listing:
            raise ValueError(f"no NYSE calendar lists {year}")
        first = min(listing, key=lambda c: c[0])
        last = max(listing, key=lambda c: c[0])
        holidays = {d for d in last[2] if d.year == year}
        early = {d for d in last[3] if d.year == year}
        first_early = {d for d in first[3] if d.year == year}

        def session(d: dt.date) -> bool:
            return d.weekday() < 5 and d not in holidays

        for month in range(1, 13):
            d = dt.date(year, month, 1)
            fridays = [d + dt.timedelta(days=k) for k in range(31)
                       if (d + dt.timedelta(days=k)).month == month
                       and (d + dt.timedelta(days=k)).weekday() == 4]
            opex = fridays[2]
            note = ""
            while not session(opex):
                opex -= dt.timedelta(days=1)
                note = f"third Friday {fridays[2]} is an exchange holiday"
            rows.append(Row(opex, "OPEX", "", "scheduled", first[0], "rule", first[1],
                            "Standard monthly expiration: third Friday, or the preceding "
                            "business day if that Friday is an exchange holiday (OCC/Cboe)",
                            held=True if opex <= today else None,
                            notes=("quarterly; " if month % 3 == 0 else "") + note))
            if month % 3 == 0:
                q = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)
                while not session(q):
                    q -= dt.timedelta(days=1)
                rows.append(Row(q, "QUARTER_END", "", "scheduled", first[0], "rule", first[1],
                                "Last NYSE session of the calendar quarter",
                                held=True if q <= today else None))
        for d in sorted(early):
            published = first[0] if d in first_early else min(
                c[0] for c in listing if d in c[3])
            src = next(c[1] for c in sorted(listing, key=lambda c: c[0]) if d in c[3])
            rows.append(Row(d, "EARLY_CLOSE", "13:00", "scheduled", published, "schedule_doc",
                            src, src, held=True if d <= today else None,
                            notes="1:00 p.m. ET close (1:15 p.m. for eligible options)"))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    f = Fetcher(args.cache)
    rows = fomc_rows(f, args.today) + market_rows(f, args.today)
    for series in ("CPI", "NFP"):
        sched, src, when = schedule_dates(f, series, args.today)
        rows += release_rows(series, bls_releases(f, series, args.today), sched, src, when,
                             args.today)
    sched, src, when = schedule_dates(f, "PCE", args.today)
    rows += release_rows("PCE", bea_releases(f), sched, src, when, args.today)
    rows = [r for r in rows if FIRST <= r.event_date <= LAST]
    rows.sort(key=lambda r: (r.event_date, r.event_type, r.kind, r.reference_period))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r.csv())
    counts: dict[str, int] = {}
    for r in rows:
        counts[f"{r.event_type}/{r.kind}"] = counts.get(f"{r.event_type}/{r.kind}", 0) + 1
    print(f"wrote {args.out} ({len(rows)} rows)")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")


if __name__ == "__main__":
    main()

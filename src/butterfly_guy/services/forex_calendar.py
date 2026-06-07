"""Fetch and format USD economic calendar events from ForexFactory."""

from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from curl_cffi import requests as curl_requests

FOREX_FACTORY_XML_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
FOREX_FACTORY_CALENDAR_URL = "https://www.forexfactory.com/calendar?week={week}"

_IMPACT_MARKERS = {
    "Low": "🟡",
    "Medium": "🟠",
    "High": "🔴",
    "Holiday": "⚪",
}
_IMPACT_FROM_ICON = {
    "impact-red": "High",
    "impact-ora": "Medium",
    "impact-yel": "Low",
    "impact-gra": "Holiday",
}
_ROW_RE = re.compile(r'<tr[^>]*class="calendar__row[^"]*"[^>]*>.*?</tr>', re.DOTALL)


@dataclass(frozen=True)
class ForexEvent:
    title: str
    country: str
    event_date: dt.date
    time_str: str
    impact: str
    forecast: str
    previous: str


def _parse_event_date(raw: str) -> dt.date:
    return dt.datetime.strptime(raw.strip(), "%m-%d-%Y").date()


def _week_url_param(ref_date: dt.date) -> str:
    """ForexFactory week slug for the Sunday that starts the calendar week."""
    days_since_sunday = (ref_date.weekday() + 1) % 7
    sunday = ref_date - dt.timedelta(days=days_since_sunday)
    return f"{sunday.strftime('%b').lower()}{sunday.day}.{sunday.year}"


def _parse_day_label(label: str, year: int) -> dt.date:
    # e.g. "Jun 7" -> date in the requested calendar year
    return dt.datetime.strptime(f"{label.strip()} {year}", "%b %d %Y").date()


def _impact_from_row(row_html: str) -> str:
    for icon, impact in _IMPACT_FROM_ICON.items():
        if icon in row_html:
            return impact
    return "Low"


def _cell_text(row_html: str, css_class: str) -> str:
    match = re.search(
        rf'calendar__cell calendar__{css_class}[^"]*">(?:<span>)?([^<]+)',
        row_html,
    )
    return match.group(1).strip() if match else ""


def _parse_events_from_html(html: str, *, currency: str = "USD") -> list[ForexEvent]:
    year_match = re.search(r"calendar\?week=[a-z]+\d+\.(\d{4})", html)
    year = int(year_match.group(1)) if year_match else dt.date.today().year

    current_day: dt.date | None = None
    last_time_str = ""
    events: list[ForexEvent] = []

    for row in _ROW_RE.findall(html):
        if "calendar__row--day-breaker" in row:
            day_match = re.search(r"<span>([A-Za-z]{3} \d{1,2})</span>", row)
            if day_match:
                current_day = _parse_day_label(day_match.group(1), year)
                last_time_str = ""
            continue

        if "calendar__row--new-day" in row:
            day_match = re.search(
                r'calendar__date"[^>]*><span class="date">[^<]*<span>([A-Za-z]{3} \d{1,2})</span>',
                row,
            )
            if day_match:
                current_day = _parse_day_label(day_match.group(1), year)
                last_time_str = ""

        time_str = _cell_text(row, "time")
        if time_str:
            last_time_str = time_str

        country = _cell_text(row, "currency")
        if country != currency or current_day is None:
            continue

        title_match = re.search(r'calendar__event-title">([^<]+)', row)
        if not title_match:
            continue

        events.append(
            ForexEvent(
                title=title_match.group(1).strip(),
                country=country,
                event_date=current_day,
                time_str=time_str or last_time_str or "Tentative",
                impact=_impact_from_row(row),
                forecast=_cell_text(row, "forecast"),
                previous=_cell_text(row, "previous"),
            )
        )

    events.sort(key=lambda e: (e.event_date, e.time_str))
    return events


def _parse_events_from_xml(xml_text: str, *, currency: str = "USD") -> list[ForexEvent]:
    root = ET.fromstring(xml_text)
    events: list[ForexEvent] = []
    for node in root.findall("event"):
        country = (node.findtext("country") or "").strip()
        if country != currency:
            continue
        events.append(
            ForexEvent(
                title=(node.findtext("title") or "").strip(),
                country=country,
                event_date=_parse_event_date(node.findtext("date") or ""),
                time_str=(node.findtext("time") or "").strip(),
                impact=(node.findtext("impact") or "").strip(),
                forecast=(node.findtext("forecast") or "").strip(),
                previous=(node.findtext("previous") or "").strip(),
            )
        )
    events.sort(key=lambda e: (e.event_date, e.time_str))
    return events


def _fetch_calendar_html(week: str | None = None) -> str:
    week_slug = week or _week_url_param(dt.date.today())
    url = FOREX_FACTORY_CALENDAR_URL.format(week=week_slug)
    resp = curl_requests.get(url, impersonate="chrome", timeout=20)
    resp.raise_for_status()
    return resp.text


async def fetch_usd_events(
    *,
    week: str | None = None,
    xml_url: str = FOREX_FACTORY_XML_URL,
) -> list[ForexEvent]:
    """Download this week's ForexFactory calendar and return USD events."""
    # HTML scrape is the reliable source; XML is an unofficial fallback.
    try:
        html = _fetch_calendar_html(week)
        events = _parse_events_from_html(html)
        if events:
            return events
    except Exception:
        pass

    resp = curl_requests.get(xml_url, impersonate="chrome", timeout=20)
    resp.raise_for_status()
    return _parse_events_from_xml(resp.text)


def _format_event_line(event: ForexEvent) -> str:
    marker = _IMPACT_MARKERS.get(event.impact, "⚪")
    title = event.title
    if event.impact == "High":
        title = f"**{title}**"
    elif event.impact == "Medium":
        title = f"*{title}*"

    detail = f"{marker} {event.time_str} | {title}"
    if event.forecast or event.previous:
        extras = []
        if event.forecast:
            extras.append(f"Fcst {event.forecast}")
        if event.previous:
            extras.append(f"Prev {event.previous}")
        detail += f" ({', '.join(extras)})"
    return detail


def format_usd_calendar_text(events: list[ForexEvent]) -> str:
    """Compact Discord summary of USD events for the week."""
    if not events:
        return "📰 **USD Economic Calendar**\n> No USD events scheduled this week."

    week_start = events[0].event_date
    week_end = events[-1].event_date
    lines = [
        "📰 **USD Economic Calendar** (ForexFactory)",
        f"> Week of {week_start:%b %d} – {week_end:%b %d}",
        "> 🟡 Low  🟠 Medium  🔴 High",
        "",
    ]

    current_day: dt.date | None = None
    for event in events:
        if event.event_date != current_day:
            current_day = event.event_date
            lines.append(f"**{current_day:%a %b %d}**")
        lines.append(_format_event_line(event))

    return "\n".join(lines)

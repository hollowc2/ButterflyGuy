"""Tests for ForexFactory USD calendar integration."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.services.forex_calendar import (
    _parse_events_from_xml,
    _week_url_param,
    format_usd_calendar_text,
)

SAMPLE_XML = """<?xml version="1.0" encoding="windows-1252"?>
<weeklyevents>
    <event>
        <title>Core CPI m/m</title>
        <country>USD</country>
        <date><![CDATA[06-10-2026]]></date>
        <time><![CDATA[12:30pm]]></time>
        <impact><![CDATA[High]]></impact>
        <forecast><![CDATA[0.3%]]></forecast>
        <previous><![CDATA[0.2%]]></previous>
    </event>
    <event>
        <title>Bank Lending y/y</title>
        <country>JPY</country>
        <date><![CDATA[06-07-2026]]></date>
        <time><![CDATA[11:50pm]]></time>
        <impact><![CDATA[Low]]></impact>
        <forecast><![CDATA[5.6%]]></forecast>
        <previous><![CDATA[5.4%]]></previous>
    </event>
    <event>
        <title>NFIB Small Business Index</title>
        <country>USD</country>
        <date><![CDATA[06-09-2026]]></date>
        <time><![CDATA[10:00am]]></time>
        <impact><![CDATA[Low]]></impact>
        <forecast><![CDATA[98.5]]></forecast>
        <previous><![CDATA[98.0]]></previous>
    </event>
</weeklyevents>
"""


def test_parse_events_filters_usd_only():
    events = _parse_events_from_xml(SAMPLE_XML)
    assert len(events) == 2
    assert all(e.country == "USD" for e in events)
    assert events[0].title == "NFIB Small Business Index"
    assert events[1].title == "Core CPI m/m"


def test_format_usd_calendar_text_includes_week_and_impact_markers():
    events = _parse_events_from_xml(SAMPLE_XML)
    text = format_usd_calendar_text(events)
    assert "USD Economic Calendar" in text
    assert "Jun 09" in text
    assert "Jun 10" in text
    assert "🟡" in text
    assert "🔴" in text
    assert "**Core CPI m/m**" in text
    assert "Bank Lending" not in text


def test_week_url_param_uses_sunday_slug():
    assert _week_url_param(dt.date(2026, 6, 7)) == "jun7.2026"
    assert _week_url_param(dt.date(2026, 6, 10)) == "jun7.2026"

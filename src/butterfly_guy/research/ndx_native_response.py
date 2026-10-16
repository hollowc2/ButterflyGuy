"""Opt-in preservation of buffered gateway option-chain bodies; never fetches data."""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import httpx
from schwab_gateway_sdk.models import OptionChainResponseV1

from butterfly_guy.research.ndx_evidence import digest
from butterfly_guy.research.ndx_recording import LocalClock, encode, sha, unique_pairs

MAX_NATIVE_BODY_BYTES = 16 * 1024 * 1024
BODY_SCOPE = "gateway-http-decoded-option-chain-v1"


def decode_body(body, *, expected_symbols, session):
    """Validate the native market-only SDK schema, keeping original bytes separate."""
    if len(body) > MAX_NATIVE_BODY_BYTES:
        raise ValueError("native market body exceeds 16 MiB recording budget")
    # Duplicate keys must not disappear before the extra-field allowlist is applied.
    raw = json.loads(body, parse_float=Decimal, object_pairs_hook=unique_pairs)
    OptionChainResponseV1.model_validate_json(body)
    chain = raw["option_chain"]
    if chain["symbol"].lstrip("$") != "NDX" or chain["expiration"] != session:
        raise ValueError("native chain identity mismatch")
    dt.date.fromisoformat(session)
    if len(expected_symbols) != 3 or len(set(expected_symbols)) != 3:
        raise ValueError("exact three-symbol research universe required")
    contracts = {q["symbol"]: q for q in chain["contracts"]}
    selected = []
    for symbol in expected_symbols:
        if symbol not in contracts:
            raise ValueError("selected native contract missing")
        q = contracts[symbol]
        match = re.fullmatch(r"NDXP\s+(\d{6})([CP])(\d{8})", symbol)
        if (not match or match[1] != dt.date.fromisoformat(session).strftime("%y%m%d")
                or match[2] != q["option_type"][0] or q["expiration"] != session
                or Decimal(match[3]) / 1000 != Decimal(str(q["strike"]))):
            raise ValueError("selected native instrument identity mismatch")
        values = {}
        for key in ("strike", "multiplier", "bid", "ask", "mark", "age_seconds"):
            value = q.get(key)
            # Fixed-point derivative strings; exponent/lexical tokens remain in body.
            values[key] = format(Decimal(str(value)), "f") if value is not None else None
        selected.append({"symbol": symbol, "root": "NDXP", "expiration": session,
            "option_type": q["option_type"], **values,
            "bid_size": q.get("bid_size"), "ask_size": q.get("ask_size"),
            "event_timestamp": q.get("event_timestamp"), "age_reference": None,
            "flags": q.get("data_quality_flags"), "stale": q.get("stale"),
            "normalization":
                "gateway-normalized fields; decimal fixed-point derivative; no defaults"})
    return selected, {k: chain.get(k) for k in (
        "symbol", "expiration", "gateway_received_at", "event_timestamp", "age_seconds",
        "source", "stale", "data_quality_flags", "call_contract_count", "put_contract_count",
        "strike_count")}


@dataclass(frozen=True)
class NativeCapture:
    body: bytes
    document_json: str

    @property
    def document(self):
        return json.loads(self.document_json)


def preserve_buffered_response(response, *, snapshot_id, record_id, request_id, pass_id,
                               acquisition_id, expected_symbols, session, clock=None,
                               request_start=None, evidence_kind="prospective", version=1,
                               parent_document_sha256=None):
    """Called explicitly AFTER a caller's GET returned; does not consume streams.

    No headers, query values, authorization, account endpoint or HTTP error body
    are retained. The timestamp is when this observer saw a buffered response,
    not an invented network receipt or upstream freshness reference instant.
    """
    if (response.request.method != "GET" or response.request.url.path != "/v1/option-chain"
            or response.status_code != 200):
        raise ValueError("only successful native option-chain GET bodies may be preserved")
    if evidence_kind not in ("synthetic", "historical", "prospective"):
        raise ValueError("invalid evidence kind")
    if not all(isinstance(s, str) and s for s in
               (snapshot_id, record_id, request_id, pass_id, acquisition_id)):
        raise ValueError("stable acquisition/pass/request/record/snapshot identities required")
    if type(version) is not int or version < 1:
        raise ValueError("invalid snapshot version")
    clock = clock or LocalClock()
    observed = clock.stamp()
    try:
        body = response.content
    except httpx.ResponseNotRead as exc:
        raise ValueError("response not buffered; recording must not consume the transport") from exc
    selected, chain = decode_body(body, expected_symbols=expected_symbols, session=session)
    # Reported chain age is separate from actual clocks and never supplies age_reference.
    document = {"schema_version": "NDX-native-gateway-v1", "evidence_kind": evidence_kind,
        "snapshot_id": snapshot_id, "record_id": record_id, "version": version,
        "request_id": request_id, "pass_id": pass_id, "acquisition_id": acquisition_id,
        "parent_document_sha256": parent_document_sha256,
        "session": session, "expected_symbols": list(expected_symbols), "selected": selected,
        "chain": {k: str(v) if isinstance(v, Decimal) else v for k, v in chain.items()},
        "body_scope": BODY_SCOPE, "body_sha256": sha(body), "body_bytes": len(body),
        "provider_original_body": False, "gateway_build_sha256": None,
        "observer_clock": {"domain": clock.domain, "description": clock.description},
        "observer_saw_buffered_response_at": observed, "request_start": request_start,
        "age_reference": None, "replay_eligible": False,
        "observer_source_sha256": digest(Path(__file__)),
        "observer_dependencies": {name: importlib.metadata.version(name)
                                  for name in ("httpx", "schwab-gateway-sdk")},
        "effective_recording_settings": {"max_native_body_bytes": MAX_NATIVE_BODY_BYTES,
                                         "market_endpoint": "/v1/option-chain",
                                         "body_scope": BODY_SCOPE}}
    return NativeCapture(body, encode(document))


def validate_capture(capture):
    doc = capture.document
    if (doc["schema_version"] != "NDX-native-gateway-v1" or doc["body_scope"] != BODY_SCOPE
            or doc["body_sha256"] != sha(capture.body) or doc["body_bytes"] != len(capture.body)
            or doc["provider_original_body"] is not False or doc["replay_eligible"] is not False):
        raise ValueError("native capture scope/hash mismatch")
    selected, chain = decode_body(capture.body, expected_symbols=doc["expected_symbols"],
                                  session=doc["session"])
    if selected != doc["selected"] or {
        k: str(v) if isinstance(v, Decimal) else v for k, v in chain.items()
    } != doc["chain"]:
        raise ValueError("native body/derivative mismatch")
    return doc


def assess_native(document, *, receipt_recorded, commit_ack_recorded):
    """State known omissions; never promote captured gateway bytes to provider truth."""
    unknown = ["upstream_age_reference_unavailable", "clock_synchronization_unattested",
               "gateway_build_unattested", "provider_original_body_unavailable"]
    if not receipt_recorded:
        unknown.append("consumer_receipt_journal_unavailable")
    if not commit_ack_recorded:
        unknown.append("post_commit_ack_unavailable")
    if any(q["multiplier"] is None for q in document["selected"]):
        unknown.append("selected_multiplier_unavailable")
    return {"status": "insufficient", "unknown": unknown, "body_scope": BODY_SCOPE,
            "evidence_kind": document["evidence_kind"], "freshness_verified": False,
            "replay_eligible": False, "earliest_availability": None, "decision": None, "fill": None}

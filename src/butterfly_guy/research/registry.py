"""Append-only, hash-chained registry of every variant evaluated on a dataset.

One JSONL file per dataset name (`reports/research/registry/<dataset>.jsonl`). Each
record carries the previous record's hash and its own, so an edit, deletion or reorder of
earlier lines is detected, and writing refuses until the chain is intact. The file is only
ever opened for append.

Events:
- `register`: a variant definition written down before it is evaluated on this dataset.
- `evaluate`: a run scored the variant. Its stage is `pre` when a `register` event (or a
  `pre` backfill) for the same definition hash precedes it in this file, otherwise `post`
  (conservative: anything not registered in advance counts as chosen after seeing results).
- `backfill`: a variant tried on this data before the registry existed, carried over
  from the research journal with the stage its source recorded.

The multiple-testing count reported with results is the number of distinct definitions
with an `evaluate` or `backfill` event on the dataset name, since extended data still
contains the earlier sessions.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

GENESIS = "0" * 64
EVENTS = {"register", "evaluate", "backfill"}
STAGES = {"pre", "post"}


class RegistryError(RuntimeError):
    pass


def _canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)


def record_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(_canonical(body).encode()).hexdigest()


@dataclass
class Registry:
    path: Path

    @classmethod
    def for_dataset(cls, root: Path, dataset: str) -> Registry:
        return cls(Path(root) / f"{dataset}.jsonl")

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text().splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def verify(self) -> list[str]:
        """Return chain problems; empty when the file is intact."""
        problems = []
        prev = GENESIS
        for n, rec in enumerate(self.records()):
            if rec.get("seq") != n:
                problems.append(f"record {n}: seq {rec.get('seq')} out of order")
            if rec.get("prev_hash") != prev:
                problems.append(f"record {n}: prev_hash does not match record {n - 1}")
            if rec.get("hash") != record_hash(rec):
                problems.append(f"record {n}: content does not match its hash")
            prev = rec.get("hash", "")
        return problems

    def append(self, event: str, *, variant: str, definition: dict, definition_hash: str,
               stage: str | None = None, **fields: object) -> dict:
        if event not in EVENTS:
            raise ValueError(f"unknown registry event {event!r}")
        problems = self.verify()
        if problems:
            raise RegistryError("registry chain is broken: " + "; ".join(problems))
        existing = self.records()
        if event == "evaluate":
            stage = "pre" if self._registered(existing, definition_hash) else "post"
        elif event == "register":
            if any(r["definition_hash"] == definition_hash for r in existing):
                raise RegistryError(
                    f"{variant} is already in the registry; it cannot be pre-registered now"
                )
            stage = "pre"
        if stage not in STAGES:
            raise ValueError("a backfill record needs stage 'pre' or 'post'")
        rec = {
            "seq": len(existing),
            "event": event,
            "stage": stage,
            "variant": variant,
            "definition": definition,
            "definition_hash": definition_hash,
            "recorded_at": fields.pop("recorded_at", None)
            or dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            **fields,
            "prev_hash": existing[-1]["hash"] if existing else GENESIS,
        }
        rec["hash"] = record_hash(rec)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            fh.write(_canonical(rec) + "\n")
        return rec

    @staticmethod
    def _registered(records: list[dict], definition_hash: str) -> bool:
        return any(r["definition_hash"] == definition_hash
                   and (r["event"] == "register" or (r["event"] == "backfill"
                                                     and r["stage"] == "pre"))
                   for r in records)

    def tried(self, dataset_hash: str | None = None) -> dict[str, int]:
        """Distinct definitions evaluated (or backfilled) on this dataset name, overall and
        on one exact dataset hash."""
        recs = [r for r in self.records() if r["event"] in {"evaluate", "backfill"}]
        out = {"dataset": len({r["definition_hash"] for r in recs}),
               "post_hoc": len({r["definition_hash"] for r in recs if r["stage"] == "post"})}
        if dataset_hash is not None:
            out["this_hash"] = len({r["definition_hash"] for r in recs
                                    if r.get("dataset_hash") == dataset_hash})
        return out

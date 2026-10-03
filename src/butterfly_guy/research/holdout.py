"""The SPX holdout split, the window currently sealed, and the only way to unseal it.

`docs/research/next-sweep-preregistration-draft.md` fixed the split before any vendor data
was seen:

- development: 2022-01-03 -> 2024-06-28 (exploration, debugging, threshold fitting);
- holdout: 2024-07-01 -> 2026-03-12, downloaded and evaluated only after registration.

The holdout is spent. H-TS1 was registered (registry seq 0, git `9051357`) and evaluated
once on 2026-09-30 as run `ce91c4a08efd` (FAIL). `HOLDOUT` stays as the label of that
window: manifests count its sessions, and the registered evaluation (`protocol.py`) still
reproduces on it. Its data may now be read, but any result on it is post hoc and can never
be presented as an unseen test.

`SEALED` is the window that is actually closed. It is `None` until a new holdout is fixed.
While it is set, every vendor request, every write into a dataset and every session load
checks its dates with `guard`. Anything touching it raises `HoldoutSealedError` unless it
carries an `Unseal`, and an `Unseal` exists only as the result of `verify_unseal`, which
checks the registry:

- the registry's hash chain is intact;
- the named record is a `register` event, and every `register` record for the dataset up
  to it came from a clean tree (`git_dirty` false);
- every one of them was made on a dataset hash that the dataset's manifest history shows
  held no holdout session (`holdout_sessions == 0`).

A boolean flag is never enough, and nothing here downloads or reads holdout data.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from butterfly_guy.research.dataset import Manifest
from butterfly_guy.research.registry import Registry

DEVELOPMENT = (dt.date(2022, 1, 3), dt.date(2024, 6, 28))
HOLDOUT = (dt.date(2024, 7, 1), dt.date(2026, 3, 12))
# H-TS1 spent HOLDOUT on 2026-09-30 (run ce91c4a08efd). Set a new window here to seal it.
SEALED: tuple[dt.date, dt.date] | None = None
# Already-seen recorded sessions used to check a vendor's data quality
# (docs/research/vendor-data-quality-plan-2026-09-28.md).
VALIDATION = (dt.date(2026, 3, 13), dt.date(2026, 9, 25))

_TOKEN = object()


class HoldoutSealedError(RuntimeError):
    """A request, write or load touched the sealed holdout without a verified unseal."""


@dataclass(frozen=True)
class Unseal:
    """Proof that the registry allows holdout access for one dataset. Build it only with
    `verify_unseal`."""

    dataset: str
    registry_seq: int
    registered: tuple[str, ...]  # variant names registered up to `registry_seq`
    _token: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._token is not _TOKEN:
            raise TypeError("an Unseal can only be created by verify_unseal")


def in_holdout(d: dt.date) -> bool:
    """Whether `d` is in the (spent) H-TS1 holdout window. A label, not a lock."""
    return HOLDOUT[0] <= d <= HOLDOUT[1]


def touches_holdout(start: dt.date, end: dt.date) -> bool:
    if end < start:
        raise ValueError(f"empty range {start}..{end}")
    return start <= HOLDOUT[1] and end >= HOLDOUT[0]


def is_sealed(d: dt.date) -> bool:
    return SEALED is not None and SEALED[0] <= d <= SEALED[1]


def touches_sealed(start: dt.date, end: dt.date) -> bool:
    if end < start:
        raise ValueError(f"empty range {start}..{end}")
    return SEALED is not None and start <= SEALED[1] and end >= SEALED[0]


def guard(start: dt.date, end: dt.date, *, what: str, dataset: str | None = None,
          unseal: Unseal | None = None) -> None:
    """Raise unless `start..end` (inclusive) avoids the sealed window, or `unseal` is a
    verified unseal for `dataset`."""
    if not touches_sealed(start, end):
        return
    if unseal is None:
        raise HoldoutSealedError(
            f"{what} for {start}..{end} touches the sealed holdout {SEALED[0]}..{SEALED[1]}; "
            "it opens only with a registry-verified unseal (after registration)")
    if unseal.dataset != dataset:
        raise HoldoutSealedError(f"{what}: the unseal is for {unseal.dataset!r}, not {dataset!r}")


def verify_unseal(registry: Registry, manifest: Manifest, seq: int) -> Unseal:
    """Check the registry and the dataset's manifest history (see the module docstring)."""
    if registry.path.stem != manifest.dataset:
        raise HoldoutSealedError(f"{registry.path.name} is not the registry of {manifest.dataset}")
    problems = registry.verify()
    if problems:
        raise HoldoutSealedError("registry chain is broken: " + "; ".join(problems))
    records = registry.records()
    if not 0 <= seq < len(records) or records[seq]["event"] != "register":
        raise HoldoutSealedError(f"registry record {seq} is not a register event")
    registrations = [r for r in records[:seq + 1] if r["event"] == "register"]
    dev_hashes = {h["dataset_hash"] for h in manifest.history
                  if h.get("holdout_sessions") == 0 and h.get("dataset_hash")}
    for r in registrations:
        if r.get("git_dirty") is not False:
            raise HoldoutSealedError(f"{r['variant']} (seq {r['seq']}) was not registered "
                                     "from a clean, committed tree")
        if r.get("dataset_hash") not in dev_hashes:
            raise HoldoutSealedError(
                f"{r['variant']} (seq {r['seq']}) was registered on dataset hash "
                f"{r.get('dataset_hash')!r}, which {manifest.dataset}'s history does not show "
                "as development-only data")
    return Unseal(manifest.dataset, seq, tuple(r["variant"] for r in registrations), _TOKEN)

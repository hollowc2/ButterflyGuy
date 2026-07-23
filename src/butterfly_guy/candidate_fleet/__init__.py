"""Paper-only SPX candidate fleet fed by a shared market-data service."""

from butterfly_guy.candidate_fleet.models import MarketSnapshot, SnapshotIdentity
from butterfly_guy.candidate_fleet.provider import MarketDataProvider

__all__ = ["MarketDataProvider", "MarketSnapshot", "SnapshotIdentity"]

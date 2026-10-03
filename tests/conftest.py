import pytest

from butterfly_guy.research import holdout


@pytest.fixture
def sealed_holdout(monkeypatch):
    """Seal the (spent) H-TS1 window again, to test the guard that protects any future
    holdout. Production has `SEALED = None`."""
    monkeypatch.setattr(holdout, "SEALED", holdout.HOLDOUT)

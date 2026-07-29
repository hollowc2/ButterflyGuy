from butterfly_guy.core.entry_pricing import (
    capped_entry_limit,
    entry_fill_within_limit,
)


def test_capped_entry_limit_never_rounds_above_configured_maximum() -> None:
    assert capped_entry_limit(0.81, 0.40) == 0.40
    assert capped_entry_limit(0.409, 0.405) == 0.40
    assert capped_entry_limit(0.399, 0.40) == 0.39


def test_entry_fill_limit_comparison_is_decimal_safe() -> None:
    assert entry_fill_within_limit(0.40, 0.40)
    assert not entry_fill_within_limit(0.4001, 0.40)

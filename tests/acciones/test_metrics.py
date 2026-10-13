"""Valores esperados calculados a mano y aislamiento entre símbolos."""

from math import sqrt

import pytest

from acciones_app import metrics
from acciones_app.validator import validate_bars


def test_price_return_by_symbol_and_sorting(bars_frame):
    valid, _ = validate_bars(bars_frame)
    result = metrics.price_return_by_symbol(valid.iloc[::-1]).set_index("symbol")
    assert result.loc["AAA", "return_pct"] == pytest.approx(-1)
    assert result.loc["BBB", "return_pct"] == pytest.approx(20)
    assert result["observations"].tolist() == [3, 3]


def test_known_average_volume(bars_frame):
    valid, _ = validate_bars(bars_frame)
    result = metrics.average_volume_by_symbol(valid).set_index("symbol")
    assert result.loc["AAA", "average_daily_volume"] == 20
    assert result.loc["BBB", "average_daily_volume"] == 200


def test_known_sample_volatility(bars_frame):
    valid, _ = validate_bars(bars_frame)
    result = metrics.volatility_by_symbol(valid.iloc[::-1]).set_index("symbol")
    # Retornos de AAA: +0.10 y -0.10; std muestral = sqrt(0.02).
    expected = sqrt(0.02) * sqrt(252) * 100
    assert result.loc["AAA", "annualized_volatility_pct"] == pytest.approx(expected)
    assert result.loc["AAA", "return_observations"] == 2


@pytest.mark.parametrize("count", [1, 2])
def test_insufficient_returns_do_not_invent_volatility(bars_frame, count):
    valid, _ = validate_bars(bars_frame.iloc[:count])
    result = metrics.volatility_by_symbol(valid)
    assert result["annualized_volatility_pct"].isna().all()


def test_empty_metrics(bars_frame):
    valid, _ = validate_bars(bars_frame.iloc[:0])
    assert metrics.price_return_by_symbol(valid).empty
    assert metrics.average_volume_by_symbol(valid).empty
    assert metrics.volatility_by_symbol(valid).empty

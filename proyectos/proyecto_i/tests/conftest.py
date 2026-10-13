""">> Fixtures pequeñas y deterministas; no contienen cotizaciones de Alpaca."""

import pandas as pd
import pytest


@pytest.fixture
def sales_frame():
    """> Dos ventas válidas y una inválida, con agregaciones calculables a mano."""
    return pd.DataFrame({
        "region": ["Norte", "Sur", "Norte"], "producto": ["A", "B", "A"],
        "unidades": [2, 0, 3], "precio_unitario": [10.0, 20.0, 10.0],
        "cliente_id": ["C1", "C2", "C1"],
    })


@pytest.fixture
def bars_frame():
    """> Seis barras ficticias: AAA pasa de 100 a 99; BBB pasa de 50 a 60."""
    closes = [100.0, 110.0, 99.0, 50.0, 55.0, 60.0]
    return pd.DataFrame({
        "symbol": ["AAA"] * 3 + ["BBB"] * 3,
        "timestamp": ["2026-01-02T05:00:00Z", "2026-01-05T05:00:00Z", "2026-01-06T05:00:00Z"] * 2,
        "open": closes, "high": [x + 1 for x in closes], "low": [x - 1 for x in closes],
        "close": closes, "volume": [10, 20, 30, 100, 200, 300],
        "trade_count": [1, 2, 3, 1, 2, 3], "vwap": closes,
    })

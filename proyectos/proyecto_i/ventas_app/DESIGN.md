# Diseño de `ventas_app`

- `~>` **SRP (Single Responsibility Principle) — `validator.py` y `metrics.py`:** `validate_sales` concentra las reglas de calidad de las filas, mientras que las funciones de `metrics.py` solo agregan ventas que ya han sido validadas. Cada módulo tiene un motivo de cambio diferente.
- `~>` **OCP (Open/Closed Principle) — `metrics.py`:** las métricas se apoyan en el DataFrame válido y no conocen el formato de entrada. Por ello, se puede añadir una nueva métrica o una nueva fuente de datos sin modificar las reglas de validación existentes.
- `~>` **DIP (Dependency Inversion Principle) — `loader.py`:** `load_from` depende del contrato `SalesRepository`, no de una clase concreta. `CsvSalesRepository` y `JsonSalesRepository` son implementaciones intercambiables de ese contrato; por eso se añade JSON sin tocar `metrics.py`.

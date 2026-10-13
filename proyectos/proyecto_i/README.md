# Proyecto I — Ventas y acciones

La implementación está en la raíz del repositorio para conservar los puntos de entrada de clase:

- [`ventas_app/`](../../ventas_app/): Parte A.
- [`acciones_app/`](../../acciones_app/): Parte B, barras diarias de Alpaca.
- [`tests/`](../../tests/): tests separados para los cuatro módulos de cada parte.
- [README de ejecución, validación, métricas y CI](../../README.md).
- [Enunciado del profesor](https://github.com/dmartincc/dsia-26-27/blob/main/proyectos/proyecto_i/README.md), copiado en [`INSTRUCTIONS.md`](INSTRUCTIONS.md).
- [Procedencia y script reproducible del dataset B](ALPACA.md).

Desde la raíz, activar `.venv` y ejecutar:

```bash
python -m ventas_app.cli --input E1_pandas/Datos/ventas.csv --output proyectos/proyecto_i/data/processed/ventas.csv
python -m acciones_app.cli --input proyectos/proyecto_i/data/raw/alpaca_barras.csv --output proyectos/proyecto_i/data/processed/acciones.csv
pytest -q --cov=ventas_app --cov=acciones_app --cov-report=term-missing --cov-fail-under=60
```

El segundo comando requiere descargar antes el CSV como explica `ALPACA.md`. Los tests y CI usan fixtures ficticias y no necesitan Alpaca. Los datos de mercado y los resultados derivados están excluidos de Git por sus condiciones de uso; se entrega el descargador documentado. El repositorio temporal de entrega está en [dalonsoLabs/dsia-26-27-alonso-daniel](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel).

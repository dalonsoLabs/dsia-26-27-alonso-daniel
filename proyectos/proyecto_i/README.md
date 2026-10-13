# Desarrollo de Soluciones de IA — Proyecto I

**Daniel Alonso Gómez · Curso 2026–2027**

## **Leyenda utilizada en la wiki**

`->` Inicio, objetivo o tarea planteada.

`~>` Desarrollo, cambio o ajuste realizado.

`>` Paso técnico llevado a cabo.

`>>` Evidencia, archivo o comprobación del paso.

`=>` Resultado obtenido o estado final de la fecha.

![CI](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel/actions/workflows/ci.yml/badge.svg?branch=main)

`->` Construir las dos partes del [enunciado del profesor](https://github.com/dmartincc/dsia-26-27/blob/main/proyectos/proyecto_i/README.md): pipeline de ventas (A) y pipeline de barras diarias de acciones de Alpaca (B), siguiendo carga → validación → métricas → CLI, con excepciones de dominio, pytest y un workflow común de CI. El repositorio de entrega temporal está en la cuenta `dalonsoLabs`.

## Instalación

`>` Desde la raíz del repositorio, con **Python 3.12**:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd proyectos/proyecto_i
```

`>` En Windows, activar con `.venv\Scripts\activate` antes de cambiar de carpeta. Todos los comandos siguientes se ejecutan desde `proyectos/proyecto_i/`, con el entorno activo. Las versiones directas están fijadas en `requirements.txt`; pandas es la dependencia de runtime. `pytest` y `pytest-cov` verifican la entrega, e `ipykernel` conserva el soporte de los notebooks de clase. No es necesario tener Alpaca para ejecutar los tests.

## Estructura

```text
proyectos/proyecto_i/
  README.md
  INSTRUCTIONS.md           # >> Copia del enunciado
  ALPACA.md                 # >> Procedencia y extracción reproducible
  VERIFICACION.md            # >> Evidencia de la entrega
  requirements.txt
  pytest.ini
  ventas_app/               # -> Parte A: loader, validator, metrics, cli
  acciones_app/             # -> Parte B: loader, validator, metrics, cli
  tests/
    conftest.py             # >> Fixtures sintéticas en memoria
    ventas/                 # >> Tests de los cuatro módulos de A
    acciones/               # >> Tests de los cuatro módulos de B
  data/
    ventas.csv              # >> CSV del curso, versionado
    raw/                    # >> Descargas locales, excluidas de Git
    processed/              # >> Resultados locales, excluidos de Git
  descargar_alpaca.py        # > Descarga paginada del dataset B
  descargar_alpaca_masivo.py
  descargar_alpaca_eventos.py
  descargar_alpaca_actual.py
  continuar_alpaca.py
  estado_alpaca.py
```

`~>` Los paquetes, tests, datos y dependencias están agrupados en esta carpeta como muestra el enunciado. El material de prácticas se organiza en `1_programacion_avanzada_python/` y `2_pruebas_y_despliegue/`, en la raíz del repositorio. El workflow único está en la raíz, en `.github/workflows/ci.yml`, y ejecuta ambos paquetes desde esta carpeta. pytest descubre solo los tests de la entrega.

## Parte A — Ventas

`>` Ejecutar el pipeline con la copia del CSV del curso incluida en el proyecto:

```bash
python -m ventas_app.cli \
  --input data/ventas.csv \
  --output data/processed/ventas.csv
```

`~>` El loader admite CSV y una lista de objetos JSON. El validador requiere las columnas `region`, `producto`, `unidades`, `precio_unitario` y `cliente_id`, convierte los valores numéricos y rechaza unidades o precios nulos, no numéricos, no finitos o no positivos. Calcula `importe = unidades × precio_unitario` y comprueba que el resultado sea finito y positivo.

`=>` El CSV del curso produce **140 válidas y 10 inválidas**, comprobadas en un test de integración.

`~>` La CLI escribe `ventas.csv` y `ventas_invalidas.csv`, este último con el motivo de rechazo. Muestra las métricas de importe por región, top 3 productos por importe y clientes con más de una compra válida. Las rutas inexistentes, los formatos no soportados, los esquemas incorrectos y los errores de lectura o escritura terminan con código 1. Ambas CLI rechazan rutas de salida que sobrescribirían el archivo de entrada, también mediante enlaces simbólicos o duros.

`>>` Diseño OOP: [ventas_app/DESIGN.md](ventas_app/DESIGN.md). Los repositorios CSV y JSON implementan el contrato `SalesRepository`; las métricas reciben únicamente ventas validadas.

## Parte B — Acciones

`->` Adaptar la solución a datos de internet, con reglas OHLCV y tres métricas propias del dominio.

`>>` La elección son **barras diarias de diez símbolos**, con observaciones comparables y reglas OHLCV específicas del dominio. El dataset descargado el **29 de septiembre de 2026** contiene **21.960 filas**, del 2 de enero de 2018 al 28 de septiembre de 2026, con feed SIP y ajuste por splits. La API es públicamente documentada y requiere una cuenta y autenticación; sus datos no se presentan como open data.

`>>` Origen: [Alpaca Market Data API](https://docs.alpaca.markets/us/docs/about-market-data-api), endpoint `https://data.alpaca.markets/v2/stocks/bars`. Alpaca [prohíbe redistribuir los datos obtenidos mediante su API](https://alpaca.markets/support/redistribute-alpaca-api). Se entrega el **script documentado**, alternativa permitida por el enunciado, y se excluyen de Git las descargas y los resultados derivados. Las fixtures de los tests son inventadas, no cotizaciones redistribuidas.

`>` Para reproducir la descarga, instalar la [CLI oficial de Alpaca](https://docs.alpaca.markets/us/docs/alpacas-cli), iniciar sesión con `alpaca profile login` y ejecutar:

```bash
python descargar_alpaca.py \
  --symbols AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,JPM,JNJ,XOM \
  --start 2018-01-01 --end 2026-09-28 \
  --feed sip --adjustment split --min-rows 10000
```

`>>` El mínimo de 10.000 es una comprobación elegida para este descargador; **no es un requisito del enunciado**. La descarga sigue `next_page_token` hasta agotar las páginas y guarda CSV, JSONL y un manifiesto con fuente, parámetros, fecha y recuentos. Las credenciales se administran mediante el perfil de la CLI, sin incluir claves en el repositorio.

`>` Con el CSV descargado:

```bash
python -m acciones_app.cli \
  --input data/raw/alpaca_barras.csv \
  --output data/processed/acciones.csv
```

`~>` También se admite un lote `.jsonl` o `.jsonl.gz` de la extracción masiva; sus campos compactos se normalizan al mismo esquema. Se carga el archivo elegido en memoria: para la entrega se recomienda el CSV de diez símbolos y, para la colección masiva, procesar un lote cada vez.

### Esquema y validación

| Columnas | Regla |
|---|---|
| `symbol` | Texto normalizado a mayúsculas, formato de ticker válido |
| `timestamp` | Fecha ISO 8601 válida, convertida a UTC |
| `open`, `high`, `low`, `close`, `vwap` | Números finitos y positivos |
| `volume`, `trade_count` | Números finitos, enteros y no negativos |
| OHLC | `low ≤ open, close ≤ high` y `low ≤ high` |
| `(symbol, timestamp)` | Clave única; se rechazan todos los miembros de un duplicado |

`~>` El validador conserva el DataFrame de entrada, devuelve válidas ordenadas por símbolo y fecha y añade motivos a las inválidas. Los campos adicionales recibidos de la API se conservan. Un esquema incompleto genera `ValidationError`; un fallo de carga genera `DataLoadError`.

### Tres métricas

| Métrica | Cálculo e interpretación |
|---|---|
| Rentabilidad del precio por símbolo | `100 × (último cierre / primer cierre − 1)` del intervalo observado |
| Volumen medio diario por símbolo | Media aritmética de `volume` sobre las barras válidas disponibles |
| Volatilidad anualizada por símbolo | Retornos simples entre cierres consecutivos; desviación muestral (`ddof=1`) × `sqrt(252)` × 100 |

`~>` Se calculan los retornos por símbolo y en orden temporal, sin mezclar empresas ni rellenar observaciones ausentes. Con menos de dos retornos la volatilidad queda vacía. La anualización supone sesiones diarias regulares; los huecos pueden convertir un retorno en uno de varios días. La rentabilidad ajustada por splits **no incluye dividendos, comisiones ni impuestos**. Las métricas son descriptivas del intervalo, no predicciones ni recomendaciones de inversión.

`~>` La CLI escribe `acciones.csv`, `acciones_invalidas.csv`, `acciones_rentabilidad.csv`, `acciones_volumen.csv` y `acciones_volatilidad.csv`. Para cada símbolo, la rentabilidad conserva fechas inicial/final y número de observaciones; la volatilidad informa del número de retornos utilizados.

`>>` Más información de extracción y cobertura de los productos de la API: [ALPACA.md](ALPACA.md). Las noticias y subastas masivas son una colección adicional, todavía parcial; no son entradas necesarias del pipeline B de esta entrega.

## Tests y cobertura

`>` Ejecutar desde esta carpeta:

```bash
pytest -q
pytest -q -m "not integration"
pytest -q -m integration
pytest --cov=ventas_app --cov=acciones_app --cov-report=term-missing --cov-fail-under=60
```

`>>` Hay tests de `loader`, `validator`, `metrics` y `cli` en ambas partes. Se usan fixtures en memoria y `tmp_path`, Arrange/Act/Assert, `pytest.raises` y `parametrize`. Los tests de integración comprueban el CSV del curso (140/10) y los puntos de entrada `python -m ...` con archivos temporales; no acceden a la red ni usan rutas propias de una máquina.

`>` Desde la raíz se puede ejecutar también `python -m pytest -q`: el `pytest.ini` raíz apunta a los tests de esta carpeta. Los tests de ejemplo del Tema 2 se ejecutan por separado.

`=>` Verificación local del 13 de octubre de 2026: **98 tests en verde**, de los cuales 3 son de integración, y **99,25 % de cobertura conjunta**. Incluyen regresiones para valores infinitos, importes no representables, errores de codificación, extensiones gzip en mayúsculas y protección del archivo de entrada. Las CLI procesaron también el CSV real de ventas (140/10) y el CSV descargado de Alpaca (21.960 válidas, 0 inválidas).

## CI

`>>` Workflow: [.github/workflows/ci.yml](../../.github/workflows/ci.yml), adaptado de la plantilla del profesor. Se ejecuta en `push` a `main`, `pull_request` y manualmente, sobre Ubuntu con **Python 3.12**, instala `requirements.txt` y comprueba ambos paquetes con `--cov-fail-under=60`. Un fallo de tests o de cobertura hace fallar el job.

`>>` Ejecuciones y evidencia: [GitHub Actions](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel/actions/workflows/ci.yml).

`=>` Run verde de la reorganización del **13 de octubre de 2026**: [38464158185](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel/actions/runs/38464158185), con **98 tests** y **99,25 % de cobertura** en Ubuntu / Python 3.12. Checklist de comprobaciones: [VERIFICACION.md](VERIFICACION.md).

## Desarrollo por fechas

- `->` **21 septiembre:** preparar la arquitectura modular de `ventas_app` y documentar su diseño.
- `~>` **29 septiembre:** selección y extracción del dataset de Alpaca.
- `~>` **13 octubre:** reorganización de la entrega dentro de `proyectos/proyecto_i/` y aplicación de la leyenda a README y comentarios.
- `>` **13 octubre:** ejecutar ambos pipelines y verificar los tests y la cobertura.
- `>>` **13 octubre:** comprobar los archivos generados y el workflow de GitHub Actions.
- `=>` **13 octubre:** pipelines ejecutables, tests en verde y documentación en la carpeta de la entrega.

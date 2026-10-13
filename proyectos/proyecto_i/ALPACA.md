# Dataset de acciones con Alpaca para el Proyecto I

## Alcance

Para la Parte B se usan **barras diarias históricas de acciones de EE. UU.**: una fila por símbolo y sesión, con fecha/hora, apertura, máximo, mínimo, cierre, volumen, número de operaciones y precio medio ponderado por volumen. El descargador conserva también la respuesta completa de cada barra en JSONL.

Alpaca ofrece además operaciones y cotizaciones individuales, subastas, datos recientes, opciones, criptomonedas y noticias. Descargar todos esos productos y todos los símbolos no forma un dataset finito y homogéneo para este proyecto. Las barras diarias permiten aplicar reglas de validación y métricas comparables.

Documentación oficial: [CLI](https://docs.alpaca.markets/us/docs/alpacas-cli), [Market Data API](https://docs.alpaca.markets/us/docs/about-market-data-api), [barras históricas](https://docs.alpaca.markets/us/reference/stockbars) y [FAQ de fuentes IEX/SIP](https://docs.alpaca.markets/us/docs/market-data-faq).

## Preparación

1. Instalar la CLI oficial si no está instalada: `brew install alpacahq/tap/cli`.
2. Crear una cuenta de Alpaca e iniciar sesión en la CLI: `alpaca profile login`. La sesión por defecto es de paper trading y sirve para acceder a datos de mercado. No compartir ni subir credenciales al repositorio.
3. Comprobar `alpaca profile list` y probar una petición pequeña:

```bash
alpaca data bars --symbol AAPL --start 2026-09-01 --end 2026-09-02 \
  --timeframe 1Day --feed sip --limit 2
```

La documentación actual indica que el plan Basic permite consultar datos históricos SIP si el final del intervalo tiene más de 15 minutos. El acceso gratuito en tiempo real se limita a IEX. Si la cuenta deniega `sip`, repetir con `--feed iex` y documentar que representa solo ese mercado.

## Descarga reproducible

Desde esta carpeta:

```bash
python3 descargar_alpaca.py \
  --symbols AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,JPM,JNJ,XOM \
  --start 2018-01-01 --end 2026-09-28 \
  --feed sip --adjustment split --min-rows 10000
```

Para `sip` en el plan Basic, usar como `--end` un día de mercado ya completado. Durante la descarga del 29 de septiembre, usar ese mismo día como fecha final produjo `403 subscription does not permit querying recent SIP data`; terminar el intervalo el 28 de septiembre funcionó.

El script recorre `next_page_token` hasta agotar todas las páginas. El `limit` de 10.000 que figura en la API es **por respuesta**, no una prueba de que el conjunto completo tenga 10.000 filas. Si el total es menor que `--min-rows`, el comando falla y no publica un CSV incompleto.

Los archivos generados quedan en `data/raw/`, excluidos de Git:

- `alpaca_barras.csv`: formato tabular para pandas y la Parte B.
- `alpaca_barras.jsonl`: cada barra con todos los campos recibidos de Alpaca.
- `alpaca_barras.manifest.json`: URL, fecha de descarga, símbolos, intervalo, feed, ajuste, número de filas y páginas.
- `alpaca_activos.json`: catálogo completo de activos de clase `us_equity` devuelto por `alpaca asset list --asset-class us_equity`.

Descarga verificada el 29 de septiembre de 2026: **21.960 filas**, 10 símbolos, 3 páginas, del 2 de enero de 2018 al 28 de septiembre de 2026. El CSV y el JSONL tienen el mismo número de barras; no aparecen duplicados de símbolo y fecha/hora, valores vacíos en los campos principales ni barras que incumplan las relaciones de precios OHLC. El catálogo de activos contiene **33.549 registros** (14.378 activos y 19.171 inactivos); incluye productos OTC, cuyos datos no están disponibles mediante el feed SIP ordinario.

Para el README de la entrega, registrar la URL, el manifiesto y las condiciones de uso. Alpaca [indica que no se pueden redistribuir sus datos de API](https://alpaca.markets/support/redistribute-alpaca-api), por lo que este repositorio debe publicar el **script de descarga**, no los CSV/JSONL descargados. El enunciado acepta expresamente un script documentado en lugar de subir datos grandes.

## Extracción amplia solicitada

Para consultar el universo completo de activos de clase `us_equity` que devuelve este perfil:

```bash
alpaca asset list --asset-class us_equity > data/raw/alpaca_activos.json
python3 descargar_alpaca_masivo.py --kind bars --start 2016-01-01 --end 2026-09-28
python3 descargar_alpaca_masivo.py --kind auctions --start 2016-01-01 --end 2026-09-28
python3 descargar_alpaca_eventos.py actions --end 2026-09-28 --workers 1
python3 descargar_alpaca_eventos.py news --end 2026-09-28 --workers 2 --delay 1.2
python3 descargar_alpaca_actual.py
```

Los scripts de barras y subastas consultan **todos los símbolos no OTC con formato de ticker** del catálogo, tanto activos como inactivos. Los rechazos concretos de la API quedan en el manifiesto de cada lote; `activos_no_consultados.json` recoge los excluidos de entrada. Las noticias y acciones corporativas se consultan sin filtro de símbolo, para no perder eventos ligados a tickers históricos. Las capturas actuales usan solo activos vigentes y el feed IEX. Cada lote o periodo terminado tiene un archivo comprimido y un manifiesto; repetir el comando salta los archivos terminados y vuelve a intentar los fallidos. `fallos.json` debe quedar vacío tras una ejecución completa. No hay datos de la sesión bursátil en curso en los históricos SIP del plan Basic.

La extracción dispone de un supervisor local (`continuar_alpaca.py`) que espera a los procesos originales, reintenta barras, subastas y noticias, y registra el resultado en `data/raw/masivo/supervisor.log`. En la revisión del **13 de octubre de 2026** no hay procesos activos: las barras terminaron en 310/310 lotes (21.391.408 registros), las acciones corporativas en 19/19 periodos (382.051), y las capturas actuales en 265/265 lotes (13.167 símbolos con datos). Las subastas quedaron en 36/310 lotes y las noticias en 21/141 meses. Esta colección masiva parcial es adicional al CSV de diez símbolos usado por la Parte B. Para consultar el avance local:

```bash
python3 estado_alpaca.py
tail -n 20 data/raw/masivo/supervisor.log
```

Los datos se guardan en `data/raw/masivo/`, fuera de Git. Cada descargador detiene la escritura si su propio directorio supera 50 GB o quedan menos de 20 GB libres; los límites pueden ajustarse con `--max-gb` y `--min-free-gb`. El archivo `estado_actual/` es una **captura puntual**, no un historial.

Las operaciones y cotizaciones individuales también existen en la API, pero cada página tiene como máximo 10.000 registros y puede llenarse con una fracción de un solo día para una sola empresa. Extraer cada tick de todos los símbolos durante todos los años exigiría un volumen y tiempo muy superiores a esta colección de barras diarias. Para el análisis del Proyecto I, usar `alpaca_barras.csv` (21.960 filas) o convertir por lotes `masivo/barras_diarias/*.jsonl.gz` sin cargar el universo completo en memoria. El enunciado **no establece un mínimo de 10.000 filas**: exige una fuente documentada, validación, métricas, CLI, tests y CI.

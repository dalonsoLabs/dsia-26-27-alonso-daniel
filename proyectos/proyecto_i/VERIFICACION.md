# Verificación del Proyecto I

Fecha: **13 de octubre de 2026**. Referencia: [enunciado del profesor](https://github.com/dmartincc/dsia-26-27/blob/main/proyectos/proyecto_i/README.md).

| Requisito | Evidencia comprobada |
|---|---|
| Parte A con loader, validator, metrics y CLI | `ventas_app/`; ejecución real: 140 válidas y 10 inválidas |
| Parte B con el mismo patrón | `acciones_app/`; ejecución real: 21.960 válidas y 0 inválidas |
| Dataset de internet documentado | Origen, condiciones, fecha, parámetros y descargador en README y ALPACA.md |
| Validación adaptada al dominio B | Fechas UTC, precios finitos positivos, OHLC, contadores y duplicados |
| Tres métricas B | Rentabilidad del precio, volumen medio diario y volatilidad anualizada |
| Tests de los cuatro módulos en ambas partes | `tests/ventas/` y `tests/acciones/` |
| ≥8 tests en total | **98 tests en verde** |
| Cobertura ≥60 % | **99,25 % conjunta**; el módulo con menor cobertura alcanza 97 % |
| AAA, assert, raises, parametrize, fixture | Aplicados en la suite; fixtures en memoria y `tmp_path` |
| ≥1 integración | **3 tests de integración**, sin red; incluye checkpoint 140/10 y ambas CLI |
| CI para ambas partes | `.github/workflows/ci.yml`, Python 3.12, push a main y pull_request, gate 60 % |
| GitHub Actions en verde | Run [38426844375](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel/actions/runs/38426844375): 78 tests y 99,20 % de cobertura |
| Documentación de ejecución y tests | README raíz y `proyectos/proyecto_i/README.md` |
| Datos grandes y secretos excluidos de Git | Descargas y resultados ignorados; los scripts usan el perfil local de Alpaca |
| Historial Git | Commits separados para ventas/tests, acciones/tests y documentación/CI |

Comandos comprobados en el entorno Python 3.12.13:

```bash
python -m pytest -q --cov=ventas_app --cov=acciones_app --cov-report=term-missing --cov-fail-under=60
python -m pytest -q -m "not integration"
python -m pip check
python -m ventas_app.cli --input E1_pandas/Datos/ventas.csv --output proyectos/proyecto_i/data/processed/ventas.csv
python -m acciones_app.cli --input proyectos/proyecto_i/data/raw/alpaca_barras.csv --output proyectos/proyecto_i/data/processed/acciones.csv
```

Resultado de unitarios: **95 passed, 3 deselected**. `pip check`: sin dependencias incompatibles. Los reports de las CLI se guardan en `data/processed/`, excluidos de Git.

## Evidencia remota

Repositorio temporal: [dalonsoLabs/dsia-26-27-alonso-daniel](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel), **público**.

Publicación completada en `main`. El run [38426844375](https://github.com/dalonsoLabs/dsia-26-27-alonso-daniel/actions/runs/38426844375), correspondiente al commit `e00040894bf00a0ae6e31724ef5bbb372cad5013`, concluyó con **success** el 13 de octubre de 2026. El job ejecutó el comando de cobertura sobre ambos paquetes y confirmó **78 tests en verde** y **99,20 % de cobertura**, superando el gate del 60 %. Se comprobó también que las descargas y resultados de mercado no se incluyeron en el árbol remoto.

## Revisión posterior a la publicación pública

Se corrigieron y comprobaron valores infinitos e importes no representables en ventas, errores de codificación CSV/JSON, lectura de `.JSONL.GZ` y colisiones entre entrada y salidas de ambas CLI. Las pruebas verifican la conservación del archivo original, incluidos enlaces simbólicos y duros. La suite ampliada obtiene **98 tests en verde** y **99,25 % de cobertura**. Los enlaces locales de la documentación se comprobaron y no se encontraron claves privadas ni tokens de GitHub o literales de credenciales Alpaca con los patrones revisados en archivos versionados. Las carpetas de datos publicadas contienen únicamente sus `.gitignore`.

El descargador se ejecutó de nuevo contra la API el **13 de octubre de 2026**, con los diez símbolos y el intervalo documentados, usando un directorio temporal. Completó **3 páginas** y obtuvo **21.960 barras**, todas válidas. El manifiesto registró `2026-10-13T16:27:38.681713+00:00`, feed SIP y ajuste por splits. Esta comprobación adicional no sustituye la fecha de descarga del dataset original.

## Alcance de datos

La Parte B utiliza el CSV de diez símbolos descargado el 29 de septiembre, con corte histórico al 28 de septiembre de 2026. El script documentado sustituye a la publicación de datos reales, conforme a la alternativa del enunciado y a las condiciones de Alpaca. Las fixtures son datos ficticios creados para los tests. Las descargas masivas adicionales de noticias y subastas siguen parciales y no forman parte del pipeline B evaluado.

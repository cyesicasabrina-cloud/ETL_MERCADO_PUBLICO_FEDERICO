## Contexto rápido

Proyecto pequeño de scripts Python para descargar licitaciones desde la API de MercadoPublico y filtrar las que contienen "tecnología".

- Entradas: CSV generados por `licitaciones.py` en `./data` (nombres: `licitaciones_YYYYMMDD.csv`).
- Transformación: `filtrar_tecnologia.py` busca palabras clave (regex) en columnas texto y genera `tecnologia_YYYYMMDD.csv` (y opcionalmente XLSX).
- Integración: `licitaciones.py` llama a la API pública https://api.mercadopublico.cl y escribe CSVs; `filtrar_tecnologia.py` consume esos CSVs.

## Archivos clave (referencias rápidas)

- `licitaciones.py` — descarga y parseo de la API. Busca funciones/variables: `parse_licitaciones`, `fetch_with_retries`, `save_csv`. Soporta opciones por `fecha` y `estado` en algunas variantes.
- `filtrar_tecnologia.py` — reglas de negocio para detección de tecnología (lista `KEYWORDS`, lista de columnas `TEXT_COLS`, funciones `build_regex`, `match_row`, `latest_csv`).
- `tecnologia.py` — variaciones/ejemplos de uso de la API (duplicado con pequeñas diferencias). Verifique contenido para elegir la versión a usar.
- `data/` — carpeta de entrada/salida. También hay convenciones de subcarpetas `data/raw` y `data/clean` usadas por `filtrar_tecnologia.py`.

## Qué debe saber un asistente AI para ser productivo aquí

1. Entrada -> salida: `licitaciones.py` -> produces `data/licitaciones_{YYYYMMDD}.csv`. `filtrar_tecnologia.py` toma el CSV más reciente (prefiere `data/clean` luego `data/raw`) y escribe `tecnologia_{YYYYMMDD}.csv` en la raíz del proyecto.
2. Configuración principal: las palabras clave están en `KEYWORDS` (regex list) y columnas a inspeccionar en `TEXT_COLS`. Cambios rápidos a la detección se hacen editando esas variables.
3. Codificación/CSV: los scripts usan `encoding='utf-8-sig'` para compatibilidad Excel; mantén ese encoding en cualquier export.
4. Dependencias: `pandas`, `requests`. `openpyxl` opcional para generar XLSX. No se incluyen archivos de requirements; usa `pip install pandas requests openpyxl` si hace falta.
5. API key: está embebida en los scripts (constante `API_KEY` / `TICKET`). Para cambios en producción, mover a variables de entorno es recomendado.

## Comandos de desarrollo (PowerShell)

Usar el intérprete Python del entorno. Desde la raíz del repo:

```powershell
python .\licitaciones.py       # descarga CSV más reciente
python .\filtrar_tecnologia.py # genera tecnologia_YYYYMMDD.csv a partir del último CSV
```

Si falta `openpyxl` y quieres XLSX:

```powershell
pip install openpyxl
```

Si usas una fecha concreta con la versión CLI de `licitaciones.py` (algunas variantes soportan argumentos):

```powershell
python .\licitaciones.py --fecha 03102025
python .\licitaciones.py --estado activas
```

## Patrones y convenciones específicas del proyecto

- Nombres de archivo: `licitaciones_*_{fecha}.csv` y `tecnologia_{fecha}.csv`. Buscar y reusar esos prefijos cuando se agreguen pipelines adicionales.
- Búsqueda de texto: se priorizan columnas listadas en `TEXT_COLS`; si no coincide, se hace fallback sobre todo el texto concatenado de la fila.
- Ordenamiento: `filtrar_tecnologia.py` intenta ordenar por `FechaCierre` o `FechaPublicacion` si detecta columnas datetime.
- Robustez API: algunas versiones del repositorio incluyen un `fetch_with_retries` que reintenta en 5xx con backoff exponencial — prefiera esa implementación para integraciones estables.

## Ejemplos concretos (copiar/pegar para ediciones rápidas)

- Añadir una keyword simple (ejemplo en `filtrar_tecnologia.py`):

```python
KEYWORDS.append(r"ia|inteligencia\s*artificial")
```

- Forzar uso de un CSV específico en vez de `latest_csv()` (temporal, para depuración):

```python
# src = latest_csv()
src = Path(r"./data/licitaciones_20251004.csv")
```

## Cosas a vigilar / notas para el asistente

- Hay duplicación de código (múltiples variantes de `licitaciones.py`/`tecnologia.py`) — confirmar cuál es la versión «fuente de verdad» antes de refactorizar.
- Los scripts escriben en la carpeta `data/` sin control de versiones; al desarrollar, no asumas la presencia de `data/clean` hasta que sea creada por pasos previos.
- No hay pruebas automáticas; si introduces cambios no triviales, añade pruebas unitarias pequeñas que validen `parse_licitaciones` y `match_row`.

Si quieres, puedo:
- Normalizar `licitaciones.py` (dejar una única versión con argumentos CLI y `fetch_with_retries`).
- Añadir `requirements.txt` y un pequeño `README.md` con pasos de uso.

Dime qué parte quieres que mejore primero y hago la edición y verificación automática.

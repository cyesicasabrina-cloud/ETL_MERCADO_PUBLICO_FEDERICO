# ETL_MERCADO_PUBLICO_FEDERICO

Pequeño conjunto de scripts Python para descargar licitaciones desde la API pública de
MercadoPublico (https://api.mercadopublico.cl) y filtrar las que contienen keywords de
"tecnología".

Este README explica cómo instalar dependencias, ejecutar los scripts principales y las
convenciones que debe conocer un desarrollador o un agente automatizado.

## Estructura relevante

- `licitaciones.py` — descarga y parsea resultados desde la API y escribe CSV(s) en `data/`.
- `filtrar_tecnologia.py` — consume el CSV más reciente (prefiere `data/clean` luego `data/raw`) y genera `tecnologia_{YYYYMMDD}.csv` en la raíz.
- `tecnologia.py` — variante/ejemplo con lógica similar a `licitaciones.py` (puede contener duplicación).
- `data/` — carpeta donde se leen/escriben CSVs (puede contener subcarpetas `raw` y `clean`).
- `.github/copilot-instructions.md` — instrucciones para agentes AI (actualizadas).

## Requisitos

- Python 3.9+ recomendado.
- Paquetes listados en `requirements.txt` (pandas, requests). `openpyxl` es opcional si quiere salida XLSX.

Instalar dependencias (PowerShell):

```powershell
pip install -r requirements.txt
```

## Uso rápido

Desde la raíz del repositorio (PowerShell):

```powershell
python .\licitaciones.py       # descarga y escribe CSV más reciente en data/
python .\filtrar_tecnologia.py # lee último CSV y genera tecnologia_YYYYMMDD.csv
```

Algunas variantes de `licitaciones.py` aceptan argumentos tipo `--fecha` o `--estado` (revisa el archivo si necesitas pasar una fecha concreta).

## Convenciones del proyecto

- Encoding de salida CSV: `utf-8-sig` (compatibilidad con Excel). No cambiar al exportar.
- Formato de nombres: `licitaciones_{YYYYMMDD}.csv` y `tecnologia_{YYYYMMDD}.csv`.
- Búsqueda de texto en `filtrar_tecnologia.py`: prioriza columnas listadas en `TEXT_COLS`; si no hay coincidencia, hace fallback sobre el texto concatenado de la fila.
- Ordenamiento: `filtrar_tecnologia.py` intenta ordenar por `FechaCierre` o `FechaPublicacion` si detecta columnas datetime.

## Configuración y secretos

Algunos scripts contienen una constante `TICKET` / `API_KEY`. Para producción, mueva la clave a una variable de entorno y modifique el script para leerla con `os.getenv('MP_TICKET')`.

Ejemplo (sugerido):

```python
import os
TICKET = os.getenv('MP_TICKET')
```

## Tests

No hay pruebas automatizadas en el repo actualmente. Si añades tests, usa `pytest` y coloca los archivos de test en una carpeta `tests/`.

## Notas para desarrolladores / agentes AI

- Antes de refactorizar, confirme cuál de `licitaciones.py` / `tecnologia.py` es la fuente de verdad — hay duplicación histórica.
- Para cambiar la detección de "tecnología", edita `KEYWORDS` y `TEXT_COLS` en `filtrar_tecnologia.py`.
- Mantén `encoding='utf-8-sig'` en las exportaciones CSV para evitar problemas con Excel.

## Contribuciones

Abre un issue o un PR con una descripción clara del cambio. Si cambias parseo o matching, añade un test que cubra el caso.

---

Si quieres, puedo: (1) unificar las variantes de `licitaciones.py`, (2) añadir un `requirements.txt` con versiones fijas, o (3) crear tests mínimos para `match_row`. Dime qué prefieres.
# ETL_MERCADO_PUBLICO_FEDERICO
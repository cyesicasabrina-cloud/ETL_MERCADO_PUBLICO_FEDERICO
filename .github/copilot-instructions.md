# Instrucciones para Colaborador(a) / Copilot

Proyecto minimalista para **descargar licitaciones** desde la API de **Mercado Público** y **filtrar tecnología**.

## TL;DR
- `licitaciones.py` → llama a la API y escribe CSV en `./data/` (y opcionalmente `data/raw` y `data/clean`).
- `filtrar_tecnologia.py` → detecta licitaciones **tech** por regex y genera `tecnologia_YYYYMMDD.csv` (opcional `.xlsx`).
- **Entrada → Salida:** `API → CSV → filtro tech → CSV/XLSX`.

---

## Estructura del repo

```
.
├─ licitaciones.py            # Descarga y normaliza (opcional) desde la API
├─ filtrar_tecnologia.py      # Filtrado por palabras clave de tecnología
├─ 
├─ copilot-instructions.md    # Este archivo
├─ data/
│  ├─ raw/                    # CSV crudos (opcional)
│  ├─ clean/                  # CSV limpios/aplanados (opcional)
│  └─ licitaciones_YYYYMMDD.csv
└─ venv/ (opcional)
```

---

## Requisitos

```bash
pip install pandas requests
# opcional para XLSX
pip install openpyxl
```

---

## Uso rápido (PowerShell)

```powershell
# Descargar por fecha (recomendado; formato ddmmaaaa)
python .\licitaciones.py --fecha 03102025

# Alternativa por estado (puede fallar más si la API está inestable)
python .\licitaciones.py --estado activas

# Filtrar tecnología (auto-detecta el CSV más reciente; prioriza data/clean luego data/raw)
python .\filtrar_tecnologia.py

# O indicar el CSV fuente explícitamente
python .\filtrar_tecnologia.py --src .\data\licitaciones_YYYYMMDD.csv
```

**Salida esperada**
- `data/licitaciones_YYYYMMDD.csv` (y si se usa pipeline RAW/CLEAN: `data/raw/*_raw_*.csv`, `data/clean/*_clean_*.csv`)
- `tecnologia_YYYYMMDD.csv` en la raíz del proyecto  
- `tecnologia_YYYYMMDD.xlsx` si está `openpyxl`

---

## Detalles clave para mantener

### `licitaciones.py`
- Funciones/objetos relevantes:
  - `parse_licitaciones(payload)` — tolera formatos `dict`/`list` de la API.
  - `fetch_with_retries(params)` — reintentos con backoff en errores 5xx.
  - `normalize_and_select(df_raw)` — **aplana** estructuras anidadas con `pd.json_normalize(..., sep=".")` y devuelve columnas clave.
  - `ensure_dirs(base_dir)` — crea `data/raw` y `data/clean`.
  - CLI: `--fecha ddmmaaaa` **(no mezclar con `--estado`)** o `--estado activas`.
- Export:
  - CSV con `encoding="utf-8-sig"`.
  - Si el CSV se abrirá **directo en Excel** (doble clic, configuración regional ES), usar `sep=";"`.
  - Si se importará desde **Datos → Desde texto/CSV** en Excel, se puede dejar coma `,`.

### `filtrar_tecnologia.py`
- Configuración:
  - `KEYWORDS` (lista de **regex**) — añade/quita términos aquí.
  - `TEXT_COLS` — columnas donde buscar primero (`Nombre`, `Descripcion`, etc.).  
    Si no existen, hace **fallback** a todo el texto de la fila.
- Orden:
  - Ordena por `FechaCierre` o `FechaPublicacion` si detecta columnas datetime.
- CLI:
  - Sin parámetros: toma el **último CSV** (clean → raw → base).
  - `--src` para especificar un CSV concreto.

---

## Convenciones de nombres

- **Descargas**: `licitaciones_YYYYMMDD.csv`  
  (o `licitaciones_estado_ACTIVAS_YYYYMMDD.csv`, según variante)
- **Pipeline RAW/CLEAN**: `*_raw_YYYYMMDD.csv`, `*_clean_YYYYMMDD.csv`
- **Filtro Tech**: `tecnologia_YYYYMMDD.(csv|xlsx)`

---

## Variables sensibles (API Key)

- Actualmente la API key puede estar embebida (constantes `API_KEY`, `TICKET`).
- Para “producción” mover a **variables de entorno**:
  ```powershell
  # Windows PowerShell
  setx MP_TICKET "TU_API_KEY"
  ```
  En Python:
  ```python
  import os
  TICKET = os.getenv("MP_TICKET", "")
  ```

---

## Errores comunes y soluciones

- **`NameError: ensure_dirs is not defined`**  
  La función quedó indentada o el archivo ejecutado no la contiene.  
  → Asegura que `def ensure_dirs(...)` esté **arriba** y al **nivel tope**, antes de `main()`.

- **`SyntaxError: unterminated string literal`**  
  Copiaste un bloque con comilla sin cerrar (suele pasar en regex largos).  
  → Reemplaza el bloque completo (no pegues a medias).

- **Powershell mostrando “import no es un cmdlet”**  
  Estás escribiendo **código Python** en PowerShell.  
  → Ejecuta Python: `python script.py` o entra al intérprete `python` y luego `import ...`.

- **Excel muestra todo en una columna**  
  CSV con coma en región ES.  
  → Exporta con `sep=";"` o importa desde **Datos → Desde texto/CSV** seleccionando delimitador **coma** y **UTF-8**.

- **500 desde la API**  
  Intermitente.  
  → Usa `fetch_with_retries`, o consulta por **`--fecha`** (más estable que `--estado`).

---

## “Buena contribución” checklist

- [ ] Mantienes el **aplanado** (`json_normalize`) antes de exportar cuando agregas columnas nuevas.
- [ ] No rompes la convención de **nombres de archivo**.
- [ ] Cambios en detección de tech se concentran en `KEYWORDS` y se testean con `--src`.
- [ ] No mezclas `--fecha` y `--estado` en la misma llamada.
- [ ] Export con `encoding="utf-8-sig"` y, si aplica, `sep=";"`.

---

## Backlog / futuras extensiones

- Normalización robusta de fechas/montos + escritura en **SQLite** (`data/mp.sqlite`) para Power BI.
- Clasificación tech por **subcategorías**: `software`, `hardware`, `redes`, `cloud`, `seguridad`.
- Tarea programada (Windows **Task Scheduler**) para correr diario y refrescar dashboards.
- Tests rápidos (p.ej. `pytest -q` con fixtures de payload).

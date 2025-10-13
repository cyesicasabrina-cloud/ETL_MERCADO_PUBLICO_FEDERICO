
# 🚀 ETL_mercadopublico_filtro_tecnologia


Conjunto de scripts en **Python** para automatizar la descarga y filtrado de licitaciones desde la API pública de [Mercado Público](https://api.mercadopublico.cl).  
El objetivo: **detectar oportunidades relacionadas con tecnología** mediante un proceso ETL (Extract, Transform, Load) ligero y reproducible.

---

## 🧠 Descripción general

Este proyecto descarga licitaciones diarias, las guarda en formato CSV y filtra aquellas que contengan palabras clave asociadas a tecnología.  
El flujo básico es:

1. **Extracción:** `licitaciones.py` consulta la API y guarda los datos en `data/`.
2. **Transformación:** `filtrar_tecnologia.py` limpia y filtra las licitaciones relevantes.
3. **Carga/Salida:** genera `tecnologia_{YYYYMMDD}.csv` con los resultados más recientes.

---

## 📂 Estructura del proyecto

| Archivo / Carpeta | Descripción |
|-------------------|-------------|
| `licitaciones.py` | Descarga y parsea resultados desde la API; guarda CSVs en `data/`. |
| `filtrar_tecnologia.py` | Filtra CSVs recientes y genera `tecnologia_{YYYYMMDD}.csv` en la raíz. |
| `tecnologia.py` | Versión alternativa de `licitaciones.py` (mantiene compatibilidad histórica). |
| `data/` | Carpeta de almacenamiento (`raw` y `clean` son opcionales). |
| `.github/copilot-instructions.md` | Guía para agentes AI y colaboradores automáticos. |

---

## ⚙️ Requisitos

- **Python 3.9+** (recomendado)
- Dependencias mínimas:
  - `pandas`
  - `requests`
  - `openpyxl` *(opcional para salida XLSX)*

Instalación rápida (PowerShell):

```powershell
pip install -r requirements.txt
```

🧩 Uso rápido

Desde la raíz del repositorio:

python .\licitaciones.py       # Descarga y guarda CSV en data/
python .\filtrar_tecnologia.py # Filtra y crea tecnologia_YYYYMMDD.csv


Algunas versiones de licitaciones.py admiten argumentos como:

python .\licitaciones.py --fecha 20251012 --estado 7


📘 Revisa el script para conocer parámetros disponibles.

📐 Convenciones del proyecto

Encoding CSV: utf-8-sig (para compatibilidad con Excel)

Nombres estándar:

licitaciones_{YYYYMMDD}.csv

tecnologia_{YYYYMMDD}.csv

Filtrado: filtrar_tecnologia.py busca coincidencias en columnas definidas en TEXT_COLS; si no hay coincidencia directa, concatena texto de toda la fila.

Ordenamiento: se priorizan columnas datetime (FechaCierre, FechaPublicacion) al exportar.

🔐 Configuración de credenciales

Las claves o tickets de la API deben almacenarse en variables de entorno.

Ejemplo de uso recomendado:

import os
TICKET = os.getenv("MP_TICKET")


Configura tu entorno (PowerShell):

setx MP_TICKET "tu_clave_aquí"

🧪 Tests

Aún no hay tests automatizados.
Si agregas alguno, utiliza pytest y crea una carpeta tests/:

tests/
 ├─ test_filtrar_tecnologia.py
 └─ test_match_row.py

🤖 Notas para desarrolladores / agentes AI

Identifica cuál script (licitaciones.py o tecnologia.py) es la fuente principal antes de refactorizar.

Las palabras clave se definen en KEYWORDS dentro de filtrar_tecnologia.py.

Mantén el encoding utf-8-sig para evitar conflictos con Excel.

Considera unificar variantes y agregar tipado estático con mypy.

💡 Contribuciones

Haz un fork del repositorio.

Crea una rama para tu mejora:

git checkout -b feature/nueva-funcion


Envía un Pull Request con una descripción clara.

Si modificas la lógica de filtrado o parseo, incluye un test que cubra el caso.

🧭 Próximos pasos sugeridos

Unificar versiones de licitaciones.py y tecnologia.py.

Añadir requirements.txt con versiones fijas.

Crear tests mínimos para match_row() y funciones auxiliares.


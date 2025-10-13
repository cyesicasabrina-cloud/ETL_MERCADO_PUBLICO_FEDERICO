
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

import re
import glob
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE = Path(r"C:\Users\Pochocla\Desktop\licitaciones")
CLEAN_DIR = BASE / "data" / "clean"
RAW_DIR = BASE / "data" / "raw"

# Radar de tecnología (ajustable)
KEYWORDS = [
    r"tecnolog(í|i)a", r"informátic(a|o)", r"\bti\b", r"\bict\b",
    r"software", r"licencia(s)?", r"office\s*365|microsoft\s*365|o365",
    r"windows|linux|ubuntu|macos",
    r"hardware|servidor(es)?|server|storage|backup|respaldo",
    r"red(es)?|switch|router|firewall|wi-?fi|wlan|lan|sd-?wan",
    r"datacenter|data\s*center|cloud|nube|aws|azure|gcp",
    r"fibra|cableado|óptic[ao]",
    r"ciberseguridad|antivirus|endpoint|siem|soar|d(lp|1lp)",
    r"telecom|telefon(í|i)a|voip|comunicacion(es)?",
    r"tablet(s)?|ipad|notebook|laptop|computador|pc|monitor(es)?|pantalla\s*led",
    r"impresor(a|es)|plotter",
    r"desarroll(o|ar)|devops|api|integraci(ó|o)n|automatizaci(ó|o)n",
    r"base(s)?\s*de\s*datos|postgres|mysql|sql\s*server|oracle|mongodb|sqlite",
    r"analytics|bi|power\s*bi|tableau|looker"
]

TEXT_COLS = ["Nombre", "Descripcion", "Justificacion",
             "Comprador.NombreOrganismo", "Categorias.Categoria.Categoria"]


def latest_csv():
    files = sorted(glob.glob(str(CLEAN_DIR / "*_clean_*.csv")))
    if files:
        return Path(files[-1])
    files = sorted(glob.glob(str(RAW_DIR / "*_raw_*.csv")))
    if files:
        return Path(files[-1])
    # Fallback: busca CSV directos en data/ (caso común cuando licitaciones.py guarda en data/)
    data_root = BASE / "data"
    files = sorted(glob.glob(str(data_root / "licitaciones_*.csv")))
    if files:
        return Path(files[-1])
    raise FileNotFoundError(
        f"No encontré CSV en {CLEAN_DIR}, {RAW_DIR} ni {data_root}. Ejecutá primero licitaciones.py.")


def build_regex():
    return re.compile("(" + "|".join(KEYWORDS) + ")", re.IGNORECASE)


def match_row(row, rx):
    # Busca en columnas de texto conocidas
    for c in TEXT_COLS:
        if c in row and pd.notna(row[c]) and rx.search(str(row[c])):
            return True
    # Fallback: busca en todo el texto de la fila
    joined = " ".join([str(v) for v in row.values if isinstance(v, str)])
    return bool(rx.search(joined))


def main():
    src = latest_csv()
    print(f"📄 Fuente: {src}")
    df = pd.read_csv(src, dtype=str, keep_default_na=False, encoding="utf-8")

    # Intentar parsear columnas de fecha si existen
    for col in df.columns:
        if "Fecha" in col:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass

    rx = build_regex()
    tech = df[df.apply(lambda r: match_row(r, rx), axis=1)].copy()

    # Ordenar por alguna fecha si existe
    fecha_cols = [c for c in df.columns if "FechaCierre" in c or "FechaPublicacion" in c]
    for c in fecha_cols:
        if c in tech.columns and str(tech[c].dtype).startswith("datetime"):
            tech = tech.sort_values(c, na_position="last")
            break

    hoy = datetime.now().strftime("%Y%m%d")
    out_csv = BASE / f"tecnologia_{hoy}.csv"
    tech.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # XLSX opcional
    try:
        # openpyxl es opcional; si no está, se captura la excepción
        from openpyxl import Workbook  # type: ignore
        out_xlsx = BASE / f"tecnologia_{hoy}.xlsx"
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
            tech.to_excel(w, index=False, sheet_name="Tecnologia")
        print(f"✅ Filas Tech: {len(tech)} | CSV: {out_csv} | XLSX: {out_xlsx}")
    except Exception:
        print(f"✅ Filas Tech: {len(tech)} | CSV: {out_csv} (instala openpyxl si querés XLSX)")


if __name__ == "__main__":
    main()


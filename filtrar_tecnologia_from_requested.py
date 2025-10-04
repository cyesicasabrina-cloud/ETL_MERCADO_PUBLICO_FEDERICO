import re
import glob
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
CLEAN_DIR = BASE / "data" / "clean"

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


def latest_requested_csv():
    files = sorted(glob.glob(str(CLEAN_DIR / "licitaciones_requested_*.csv")))
    if files:
        return Path(files[-1])
    # fallback to any licitaciones_* in data/
    files = sorted(glob.glob(str(BASE / "data" / "licitaciones_*.csv")))
    if files:
        return Path(files[-1])
    raise FileNotFoundError("No encontré CSV 'requested' ni licitaciones en data/")


def build_regex():
    return re.compile("(" + "|".join(KEYWORDS) + ")", re.IGNORECASE)


def match_row(row, rx):
    # columnas que esperamos en el CSV requested
    text_cols = [
        "Descripcion", "Comprador.NombreOrganismo", "Comprador.NombreUnidad",
        "Comprador.ComunaUnidad", "Comprador.RegionUnidad", "Comprador.NombreUsuario",
        "Comprador.CargoUsuario", "Modalidad", "EmailResponsablePago"
    ]
    for c in text_cols:
        if c in row and pd.notna(row[c]) and rx.search(str(row[c])):
            return True
    joined = " ".join([str(v) for v in row.values if isinstance(v, str)])
    return bool(rx.search(joined))


def main():
    src = latest_requested_csv()
    print(f"Fuente: {src}")
    df = pd.read_csv(src, dtype=str, keep_default_na=False, encoding="utf-8-sig")

    # intentar parsear FechaCierre
    if "FechaCierre" in df.columns:
        try:
            df["FechaCierre"] = pd.to_datetime(df["FechaCierre"], errors="coerce")
        except Exception:
            pass

    rx = build_regex()
    tech = df[df.apply(lambda r: match_row(r, rx), axis=1)].copy()

    hoy = datetime.now().strftime("%Y%m%d")
    out_csv = BASE / f"tecnologia_{hoy}_v2.csv"
    tech.to_csv(out_csv, index=False, encoding="utf-8-sig")

    try:
        from openpyxl import Workbook  # type: ignore
        out_xlsx = BASE / f"tecnologia_{hoy}_v2.xlsx"
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
            tech.to_excel(w, index=False, sheet_name="Tecnologia")
        print(f"✅ Filas Tech: {len(tech)} | CSV: {out_csv} | XLSX: {out_xlsx}")
    except Exception:
        print(f"✅ Filas Tech: {len(tech)} | CSV: {out_csv} (instala openpyxl si querés XLSX)")


if __name__ == "__main__":
    main()

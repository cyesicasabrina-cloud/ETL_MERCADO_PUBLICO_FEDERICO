"""Licitaciones: descarga, normaliza y exporta CSVs desde la API de MercadoPublico.

Características principales:
- Función `mercado_publico_ticket()` para leer el ticket desde variable de entorno o parámetro.
- `fetch_with_retries()` maneja 429 (Retry-After) y 5xx con backoff exponencial.
- Normaliza estructuras anidadas con `pd.json_normalize` y convierte montos/fechas.
- Exporta: data/raw/<prefix>_raw_YYYYMMDD.csv, data/clean/<prefix>_clean_YYYYMMDD.csv,
  data/clean/<prefix>_requested_YYYYMMDD.csv (campos aplanados requeridos).

Uso:
    python licitaciones.py --fecha 04102025
    python licitaciones.py --estado activas

Requisitos: pandas, requests, openpyxl (opcional para xlsx en otros scripts).
"""

from __future__ import annotations

import os
import time
import argparse
import sqlite3
import requests
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional

BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
UA = "licitaciones-script/clean/FINAL-7"


def mercado_publico_ticket(env_var: str = "MP_TICKET", explicit: Optional[str] = None) -> str:
    """Devuelve el ticket (API key). Prioriza `explicit`, luego variable de entorno."""
    if explicit:
        return explicit
    return os.environ.get(env_var, "")


def parse_licitaciones(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if "Listado" in payload:
            listado = payload["Listado"]
            if isinstance(listado, dict) and "Licitacion" in listado:
                return listado["Licitacion"]
            if isinstance(listado, list):
                return listado
        if "Licitacion" in payload and isinstance(payload["Licitacion"], list):
            return payload["Licitacion"]
        if "Resultados" in payload and isinstance(payload["Resultados"], list):
            return payload["Resultados"]
    return []


def fetch_with_retries(params: Dict[str, str], max_retries: int = 6, backoff: float = 2.0) -> Any:
    headers = {"User-Agent": UA}
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait = int(retry_after)
                    except Exception:
                        wait = min(60, int(backoff ** attempt))
                else:
                    wait = min(60, int(backoff ** attempt))
                print(f"[429] Rate limit. Esperando {wait}s antes de reintentar (intento {attempt}/{max_retries})")
                time.sleep(wait)
                last_err = Exception("HTTP 429 Rate limit")
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            last_err = e
            code = getattr(e.response, "status_code", 0)
            if 500 <= code < 600:
                wait = min(60, int(backoff ** attempt))
                print(f"[5xx] {code} -> reintentando en {wait}s (intento {attempt}/{max_retries})")
                time.sleep(wait)
                continue
            raise
        except requests.RequestException as e:
            last_err = e
            wait = min(60, int(backoff ** attempt))
            print(f"Error de red/transitorio: {e} -> reintentando en {wait}s (intento {attempt}/{max_retries})")
            time.sleep(wait)
        except Exception as e:
            last_err = e
            wait = min(60, int(backoff ** attempt))
            print(f"Error inesperado: {e} -> reintentando en {wait}s (intento {attempt}/{max_retries})")
            time.sleep(wait)
    print("ERROR: Máximo de reintentos alcanzado. Revisa tu conexión o cuota (ticket).")
    raise last_err


def ensure_dirs(base_dir: str) -> tuple[str, str]:
    raw_dir = os.path.join(base_dir, "data", "raw")
    clean_dir = os.path.join(base_dir, "data", "clean")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(clean_dir, exist_ok=True)
    return raw_dir, clean_dir


def normalize(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    try:
        has_nested = any(df.map(lambda x: isinstance(x, (dict, list))).any())
        if has_nested:
            df = pd.json_normalize(df_raw.to_dict(orient="records"), sep=".")
    except Exception:
        pass

    for col in ["MontoEstimado", "Monto", "MontoTotal"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for c in list(df.columns):
        if "Fecha" in c:
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                pass

    return df


def extract_fields(licitacion: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "FechaCierre": licitacion.get("FechaCierre"),
        "Descripcion": licitacion.get("Descripcion") or licitacion.get("DescripcionLarga") or licitacion.get("Nombre"),
        "Estado": licitacion.get("Estado"),
        "Comprador.NombreOrganismo": None,
        "Comprador.NombreUnidad": None,
        "Comprador.ComunaUnidad": None,
        "Comprador.RegionUnidad": None,
        "Comprador.NombreUsuario": None,
        "Comprador.CargoUsuario": None,
        "CodigoTipo": licitacion.get("CodigoTipo"),
        "TipoConvocatoria": licitacion.get("TipoConvocatoria"),
        "MontoEstimado": licitacion.get("MontoEstimado") or licitacion.get("Monto"),
        "Modalidad": licitacion.get("Modalidad"),
        "EmailResponsablePago": licitacion.get("EmailResponsablePago"),
    }
    comprador = licitacion.get("Comprador") or {}
    if isinstance(comprador, list) and comprador:
        comprador = comprador[0]
    if isinstance(comprador, dict):
        out["Comprador.NombreOrganismo"] = comprador.get("NombreOrganismo")
        out["Comprador.NombreUnidad"] = comprador.get("NombreUnidad") or comprador.get("Unidad")
        out["Comprador.ComunaUnidad"] = comprador.get("ComunaUnidad")
        out["Comprador.RegionUnidad"] = comprador.get("RegionUnidad")
        out["Comprador.NombreUsuario"] = comprador.get("NombreUsuario") or comprador.get("NombreResponsable")
        out["Comprador.CargoUsuario"] = comprador.get("CargoUsuario") or comprador.get("CargoResponsable")
    return out


def save_csv(df: pd.DataFrame, out_dir: str, prefix: str) -> str:
    fecha = datetime.now().strftime("%Y%m%d")
    path = os.path.join(out_dir, f"{prefix}_{fecha}.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def to_sqlite(df_clean: pd.DataFrame, base_dir: str, table_name: str) -> str:
    db_path = os.path.join(base_dir, "data", "mp.sqlite")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        df_clean.to_sql(table_name, con, if_exists="append", index=False)
    finally:
        con.close()
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga licitaciones de Mercado Publico con manejo de rate limit")
    parser.add_argument("--fecha", help="Fecha ddmmaaaa (ej: 03102025). No mezclar con --estado")
    parser.add_argument("--estado", default="activas", help="Estado diario (activas, publicadas, cerradas). Default: activas")
    parser.add_argument("--ticket", help="Ticket/API key (sobrescribe variable de entorno)")
    parser.add_argument("--max-retries", type=int, default=6, help="Reintentos ante 5xx/429. Default: 6")
    args = parser.parse_args()

    ticket = mercado_publico_ticket(explicit=args.ticket)

    if not ticket:
        print("ERROR: No se encontró ticket de API. Configura MP_TICKET en variables de entorno o usa --ticket")
        return

    if args.fecha:
        params = {"fecha": args.fecha, "ticket": ticket}
        prefix = f"licitaciones_fecha_{args.fecha}"
        table = f"licitaciones_fecha_{args.fecha}"
        print(f"Consultando por fecha = {args.fecha} ...")
    else:
        params = {"estado": args.estado, "ticket": ticket}
        prefix = f"licitaciones_estado_{args.estado}"
        table = f"licitaciones_estado_{args.estado}"
        print(f"Consultando por estado = {args.estado} ...")

    base_dir = os.path.dirname(__file__)
    raw_dir, clean_dir = ensure_dirs(base_dir)

    try:
        payload = fetch_with_retries(params, max_retries=args.max_retries)
        lic = parse_licitaciones(payload)

        if not lic:
            print("INFO: No se encontraron licitaciones para los parámetros especificados")
            return

        df_raw = pd.DataFrame(lic)
        raw_path = save_csv(df_raw, raw_dir, prefix + "_raw")

        df_clean = normalize(df_raw)
        clean_path = save_csv(df_clean, clean_dir, prefix + "_clean")

        flat = [extract_fields(item) for item in lic]
        df_requested = pd.DataFrame(flat)
        if "FechaCierre" in df_requested.columns:
            df_requested["FechaCierre"] = pd.to_datetime(df_requested["FechaCierre"], errors="coerce")
        if "MontoEstimado" in df_requested.columns:
            df_requested["MontoEstimado"] = pd.to_numeric(df_requested["MontoEstimado"], errors="coerce")
        requested_path = save_csv(df_requested, clean_dir, prefix + "_requested")

        try:
            db_path = to_sqlite(df_clean, base_dir, table)
        except Exception:
            db_path = "(no sqlite)"

        print(f"Filas RAW:       {len(df_raw)}  -> {raw_path}")
        print(f"Filas CLEAN:     {len(df_clean)} -> {clean_path}")
        print(f"Filas REQUESTED: {len(df_requested)} -> {requested_path}")
        print(f"SQLite DB: {db_path} (tabla: {table})")

    except Exception as e:
        print(f"ERROR: Error final: {e}")


if __name__ == "__main__":
    main()
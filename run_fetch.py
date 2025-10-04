"""Script mínimo para descargar licitaciones y escribir un CSV en data/.

Se usa para evitar ejecutar el archivo principal `licitaciones.py` que contiene
duplicados/errores. Genera `data/licitaciones_{YYYYMMDD}.csv` con encoding utf-8-sig.
"""
import os
import requests
import pandas as pd
from datetime import datetime
from typing import Any

API_KEY = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"


def parse_licitaciones(payload: Any) -> list:
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


def extract_fields(licitacion: dict) -> dict:
    out = {}
    out["FechaCierre"] = licitacion.get("FechaCierre")
    out["Descripcion"] = licitacion.get("Descripcion") or licitacion.get("DescripcionLarga") or licitacion.get("Nombre")
    out["Estado"] = licitacion.get("Estado")
    out["CodigoTipo"] = licitacion.get("CodigoTipo")
    out["TipoConvocatoria"] = licitacion.get("TipoConvocatoria")
    out["MontoEstimado"] = licitacion.get("MontoEstimado") or licitacion.get("Monto")
    out["Modalidad"] = licitacion.get("Modalidad")

    email = licitacion.get("EmailResponsablePago")
    if not email:
        rp = licitacion.get("ResponsablePago") or {}
        if isinstance(rp, dict):
            email = rp.get("Email") or rp.get("EmailResponsablePago")
    out["EmailResponsablePago"] = email

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
    else:
        out["Comprador.NombreOrganismo"] = None
        out["Comprador.NombreUnidad"] = None
        out["Comprador.ComunaUnidad"] = None
        out["Comprador.RegionUnidad"] = None
        out["Comprador.NombreUsuario"] = None
        out["Comprador.CargoUsuario"] = None

    return out


def main():
    params = {"estado": "activas", "ticket": API_KEY}
    try:
        r = requests.get(BASE_URL, params=params, timeout=60)
        r.raise_for_status()
        payload = r.json()
        lic = parse_licitaciones(payload)
        df = pd.DataFrame(lic)

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "data")
        os.makedirs(out_dir, exist_ok=True)
        fecha = datetime.now().strftime("%Y%m%d")
        csv_file = os.path.join(out_dir, f"licitaciones_{fecha}.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")

        # Crear CSV "requested" con columnas aplanadas en data/clean
        flat = [extract_fields(item) for item in lic]
        df_requested = pd.DataFrame(flat)
        # Normalizar tipos sencillos
        if "FechaCierre" in df_requested.columns:
            try:
                df_requested["FechaCierre"] = pd.to_datetime(df_requested["FechaCierre"], errors="coerce")
            except Exception:
                pass
        if "MontoEstimado" in df_requested.columns:
            df_requested["MontoEstimado"] = pd.to_numeric(df_requested["MontoEstimado"], errors="coerce")

        clean_dir = os.path.join(base_dir, "data", "clean")
        os.makedirs(clean_dir, exist_ok=True)
        requested_path = os.path.join(clean_dir, f"licitaciones_requested_{fecha}.csv")
        df_requested.to_csv(requested_path, index=False, encoding="utf-8-sig")

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo RAW: {csv_file}")
        print(f"📄 Archivo REQUESTED: {requested_path}")
    except Exception as e:
        print(f"❌ Error al descargar licitaciones: {e}")


if __name__ == "__main__":
    main()

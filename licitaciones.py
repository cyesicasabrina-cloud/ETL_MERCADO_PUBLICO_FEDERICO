"""Script limpio para descargar y procesar licitaciones.

Genera CSVs en data/raw y data/clean, y un resumen con los campos solicitados.
"""

import os
import time
import argparse
import sqlite3
import requests
import pandas as pd
from datetime import datetime
from typing import Any, Dict


API_KEY = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
UA = "licitaciones-script/1.0"


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


def fetch_with_retries(params: Dict[str, str], max_retries: int = 5, backoff: float = 1.5) -> Any:
    headers = {"User-Agent": UA}
    last_err = None
    for i in range(max_retries):
        """Script limpio para descargar y procesar licitaciones desde MercadoPublico.

        Genera CSVs en data/raw y data/clean, y un CSV con los campos solicitados.
        """

        import os
        import time
        import argparse
        import sqlite3
        import requests
        import pandas as pd
        from datetime import datetime
        from typing import Any, Dict


        API_KEY = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
        BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
        UA = "licitaciones-script/1.0"


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


        def fetch_with_retries(params: Dict[str, str], max_retries: int = 5, backoff: float = 1.5) -> Any:
            headers = {"User-Agent": UA}
            last_err = None
            for i in range(max_retries):
                try:
                    r = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
                    r.raise_for_status()
                    return r.json()
                except requests.HTTPError as e:
                    last_err = e
                    code = getattr(e.response, "status_code", 0)
                    if 500 <= code < 600:
                        sleep_s = backoff ** i
                        time.sleep(sleep_s)
                        continue
                    raise
                except Exception as e:
                    last_err = e
                    sleep_s = backoff ** i
                    time.sleep(sleep_s)
            raise last_err


        def ensure_dirs(base_dir: str):
            raw_dir = os.path.join(base_dir, "data", "raw")
            clean_dir = os.path.join(base_dir, "data", "clean")
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(clean_dir, exist_ok=True)
            return raw_dir, clean_dir


        def normalize(df_raw: pd.DataFrame) -> pd.DataFrame:
            df = df_raw.copy()
            try:
                if any(df.applymap(lambda x: isinstance(x, (dict, list))).any()):
                    df = pd.json_normalize(df_raw.to_dict(orient="records"), sep=".")
            except Exception:
                pass

            for col in ["MontoEstimado", "Monto", "MontoTotal"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            for c in list(df.columns):
                if "Fecha" in c:
                    try:
                        df[c] = pd.to_datetime(df[c], errors="coerce")
                    except Exception:
                        pass

            return df


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
            parser = argparse.ArgumentParser(description="Descarga y procesa licitaciones de MercadoPublico.")
            parser.add_argument("--fecha", help="Fecha ddmmaaaa (ej: 03102025). Si se usa, ignora --estado.")
            parser.add_argument("--estado", default="activas", help="Estado (activas, publicadas, cerradas). Default: activas")
            parser.add_argument("--ticket", help="Ticket/API key (sobrescribe variable de entorno)")
            parser.add_argument("--max-retries", type=int, default=5, help="Reintentos ante 5xx")
            args = parser.parse_args()

            ticket = args.ticket or API_KEY
            if args.fecha:
                params = {"fecha": args.fecha, "ticket": ticket}
                prefix = f"licitaciones_fecha_{args.fecha}"
                table = f"licitaciones_fecha_{args.fecha}"
            else:
                params = {"estado": args.estado, "ticket": ticket}
                prefix = f"licitaciones_estado_{args.estado}"
                table = f"licitaciones_estado_{args.estado}"

            base_dir = os.path.dirname(__file__)
            raw_dir, clean_dir = ensure_dirs(base_dir)

            try:
                payload = fetch_with_retries(params, max_retries=args.max_retries)
                lic = parse_licitaciones(payload)

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

                db_path = to_sqlite(df_clean, base_dir, table)

                print("Filas RAW:", len(df_raw), "->", raw_path)
                print("Filas CLEAN:", len(df_clean), "->", clean_path)
                print("Filas REQUESTED:", len(df_requested), "->", requested_path)
                print("SQLite DB:", db_path, "(tabla:", table, ")")

            except Exception as e:
                print("Error final:", e)


        if __name__ == "__main__":
            main()
    main()
import os
import time
import argparse
import requests
import pandas as pd
from datetime import datetime
from typing import Any, Dict

# Lee ticket desde variable de entorno si está presente; sino usa el valor embebido
API_KEY = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
UA = "Yesi-MP-Script/1.2 (+python requests)"


def parse_licitaciones(payload: Any) -> list:
    """
    Normaliza los distintos formatos que puede devolver la API a una list[dict].
    Soporta:
      - {"Listado": {"Licitacion": [ ... ]}}
      - {"Listado": [ ... ]}
      - {"Licitacion": [ ... ]}
      - [ ... ]
    """
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


def fetch_with_retries(params: Dict[str, str], max_retries: int = 5, backoff: float = 1.5) -> Any:
    """
    Realiza la petición a la API con reintentos exponenciales en errores 5xx o fallos transitorios.
    Devuelve el JSON parseado o lanza la excepción final.
    """
    headers = {"User-Agent": UA}
    last_err = None
    for i in range(max_retries):
        try:
            r = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            last_err = e
            code = getattr(e.response, "status_code", 0)
            if 500 <= code < 600:
                sleep_s = round((backoff ** i), 2)
                print(f"⚠️  {e} → reintentando en {sleep_s}s... (intento {i+1}/{max_retries})")
                time.sleep(sleep_s)
                continue
            raise
        except Exception as e:
            last_err = e
            sleep_s = round((backoff ** i), 2)
            print(f"⚠️  Error transitorio: {e} → reintentando en {sleep_s}s... (intento {i+1}/{max_retries})")
            time.sleep(sleep_s)
    raise last_err


def save_csv(df: pd.DataFrame, base_dir: str, prefix: str = "licitaciones") -> str:
    out_dir = os.path.join(base_dir, "data")
    os.makedirs(out_dir, exist_ok=True)
    fecha = datetime.now().strftime("%Y%m%d")
    csv_file = os.path.join(out_dir, f"{prefix}_{fecha}.csv")
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    return csv_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga licitaciones de Mercado Público (CLI unificada).")
    parser.add_argument("--fecha", help="Fecha ddmmaaaa (ej: 03102025). Si se usa, ignora --estado.")
    parser.add_argument("--estado", default="activas", help="Estado diario (activas, publicadas, cerradas, etc.). Default: activas")
    parser.add_argument("--ticket", help="Ticket/API key (sobrescribe MERCADO_PUBLICO_TICKET env var).")
    parser.add_argument("--max-retries", type=int, default=5, help="Reintentos ante 5xx. Default: 5")
    args = parser.parse_args()

    ticket = args.ticket or API_KEY

    if args.fecha:
        params = {"fecha": args.fecha, "ticket": ticket}
        prefix = f"licitaciones_fecha_{args.fecha}"
        print(f"🔎 Consultando por fecha = {args.fecha} ...")
    else:
        params = {"estado": args.estado, "ticket": ticket}
        prefix = f"licitaciones_estado_{args.estado}"
        print(f"🔎 Consultando por estado = {args.estado} ...")

    try:
        payload = fetch_with_retries(params, max_retries=args.max_retries)
        lic = parse_licitaciones(payload)
        df = pd.DataFrame(lic)

        base_dir = os.path.dirname(__file__)
        csv_path = save_csv(df, base_dir, prefix=prefix)

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo: {csv_path}")

        # Vista rápida de columnas útiles si existen
        vista = [c for c in ("CodigoExterno", "Nombre", "Estado", "FechaCierre", "MontoEstimado") if c in df.columns]
        if vista:
            print("👀 Preview:")
            print(df[vista].head(5).to_string(index=False))
        else:
            print(f"ℹ️ Columnas: {list(df.columns)[:10]} ...")

    except Exception as e:
        print(f"❌ Error final: {e}")


if __name__ == "__main__":
    main()
import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = "BB946777-2A2E-4685-B5F5-43B441772C27"
URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
params = {"estado": "activas", "ticket": API_KEY}

def main():
    try:
        r = requests.get(URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        licitaciones = data.get("Listado", {}).get("Licitacion", [])
        df = pd.DataFrame(licitaciones)

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "data")
        os.makedirs(out_dir, exist_ok=True)

        fecha = datetime.now().strftime("%Y%m%d")
        csv_file = os.path.join(out_dir, f"licitaciones_activas_{fecha}.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo: {csv_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = "BB946777-2A2E-4685-B5F5-43B441772C27"
URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

# Ajusta aquí si quieres por fecha (ddmmaaaa) en vez de 'estado=activas'
PARAMS = {"estado": "activas", "ticket": API_KEY}
# Ejemplo por fecha exacta: PARAMS = {"fecha": "03102025", "ticket": API_KEY}

def parse_licitaciones(payload):
    """
    La API puede devolver:
    1) {"Listado": {"Licitacion": [ ... ]}}
    2) {"Listado": [ ... ]}
    3) [ ... ]  (lista directa)
    4) {"Licitacion": [ ... ]}  (raro pero posible)
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        # Caso clásico
        if "Listado" in payload:
            listado = payload["Listado"]
            if isinstance(listado, dict) and "Licitacion" in listado:
                return listado["Licitacion"]
            if isinstance(listado, list):
                return listado
        # Otros alias vistos a veces
        if "Licitacion" in payload and isinstance(payload["Licitacion"], list):
            return payload["Licitacion"]
        if "Resultados" in payload and isinstance(payload["Resultados"], list):
            return payload["Resultados"]

    # Si nada matchea, devolvemos lista vacía
    return []

def main():
    try:
        r = requests.get(URL, params=PARAMS, timeout=60)
        r.raise_for_status()
        data = r.json()

        licitaciones = parse_licitaciones(data)
        df = pd.DataFrame(licitaciones)

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "data")
        os.makedirs(out_dir, exist_ok=True)

        fecha = datetime.now().strftime("%Y%m%d")
        csv_file = os.path.join(out_dir, f"licitaciones_{fecha}.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo: {csv_file}")

        # Debug opcional: muestra 5 columnas claves si existen
        cols = [c for c in ["CodigoExterno","Nombre","Estado","FechaCierre","MontoEstimado"] if c in df.columns]
        if cols:
            print("👀 Muestra rápida:")
            print(df[cols].head(5).to_string(index=False))
        else:
            print(f"ℹ️ Claves disponibles: {list(df.columns)[:10]} ...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
    import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = "BB946777-2A2E-4685-B5F5-43B441772C27"
URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

# Ajusta aquí si quieres por fecha (ddmmaaaa) en vez de 'estado=activas'
PARAMS = {"estado": "activas", "ticket": API_KEY}
# Ejemplo por fecha exacta: PARAMS = {"fecha": "03102025", "ticket": API_KEY}

def parse_licitaciones(payload):
    """
    La API puede devolver:
    1) {"Listado": {"Licitacion": [ ... ]}}
    2) {"Listado": [ ... ]}
    3) [ ... ]  (lista directa)
    4) {"Licitacion": [ ... ]}  (raro pero posible)
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        # Caso clásico
        if "Listado" in payload:
            listado = payload["Listado"]
            if isinstance(listado, dict) and "Licitacion" in listado:
                return listado["Licitacion"]
            if isinstance(listado, list):
                return listado
        # Otros alias vistos a veces
        if "Licitacion" in payload and isinstance(payload["Licitacion"], list):
            return payload["Licitacion"]
        if "Resultados" in payload and isinstance(payload["Resultados"], list):
            return payload["Resultados"]

    # Si nada matchea, devolvemos lista vacía
    return []

def main():
    try:
        r = requests.get(URL, params=PARAMS, timeout=60)
        r.raise_for_status()
        data = r.json()

        licitaciones = parse_licitaciones(data)
        df = pd.DataFrame(licitaciones)

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "data")
        os.makedirs(out_dir, exist_ok=True)

        fecha = datetime.now().strftime("%Y%m%d")
        csv_file = os.path.join(out_dir, f"licitaciones_{fecha}.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo: {csv_file}")

        # Debug opcional: muestra 5 columnas claves si existen
        cols = [c for c in ["CodigoExterno","Nombre","Estado","FechaCierre","MontoEstimado"] if c in df.columns]
        if cols:
            print("👀 Muestra rápida:")
            print(df[cols].head(5).to_string(index=False))
        else:
            print(f"ℹ️ Claves disponibles: {list(df.columns)[:10]} ...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = "BB946777-2A2E-4685-B5F5-43B441772C27"
URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

# Ajusta aquí si quieres por fecha (ddmmaaaa) en vez de 'estado=activas'
PARAMS = {"estado": "activas", "ticket": API_KEY}
# Ejemplo por fecha exacta: PARAMS = {"fecha": "03102025", "ticket": API_KEY}

def parse_licitaciones(payload):
    """
    La API puede devolver:
    1) {"Listado": {"Licitacion": [ ... ]}}
    2) {"Listado": [ ... ]}
    3) [ ... ]  (lista directa)
    4) {"Licitacion": [ ... ]}  (raro pero posible)
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        # Caso clásico
        if "Listado" in payload:
            listado = payload["Listado"]
            if isinstance(listado, dict) and "Licitacion" in listado:
                return listado["Licitacion"]
            if isinstance(listado, list):
                return listado
        # Otros alias vistos a veces
        if "Licitacion" in payload and isinstance(payload["Licitacion"], list):
            return payload["Licitacion"]
        if "Resultados" in payload and isinstance(payload["Resultados"], list):
            return payload["Resultados"]

    # Si nada matchea, devolvemos lista vacía
    return []

def main():
    try:
        r = requests.get(URL, params=PARAMS, timeout=60)
        r.raise_for_status()
        data = r.json()

        licitaciones = parse_licitaciones(data)
        df = pd.DataFrame(licitaciones)

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "data")
        os.makedirs(out_dir, exist_ok=True)

        fecha = datetime.now().strftime("%Y%m%d")
        csv_file = os.path.join(out_dir, f"licitaciones_{fecha}.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo: {csv_file}")

        # Debug opcional: muestra 5 columnas claves si existen
        cols = [c for c in ["CodigoExterno","Nombre","Estado","FechaCierre","MontoEstimado"] if c in df.columns]
        if cols:
            print("👀 Muestra rápida:")
            print(df[cols].head(5).to_string(index=False))
        else:
            print(f"ℹ️ Claves disponibles: {list(df.columns)[:10]} ...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
# PARAMS = {"fecha": "03102025", "ticket": API_KEY}

import os
import time
import argparse
import requests
import pandas as pd
from datetime import datetime

API_KEY = "BB946777-2A2E-4685-B5F5-43B441772C27"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
UA = "Yesi-MP-Script/1.0 (+python requests)"

def parse_licitaciones(payload):
    """
    La API puede devolver:
      A) {"Listado": {"Licitacion": [ ... ]}}
      B) {"Listado": [ ... ]}
      C) {"Licitacion": [ ... ]}
      D) [ ... ]  (lista directa)
    Este parser devuelve siempre una list[dict].
    """
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

    return []

def fetch_with_retries(params, max_retries=5, backoff=1.5):
    """
    Reintenta ante 5xx con backoff exponencial.
    """
    headers = {"User-Agent": UA}
    last_err = None
    for i in range(max_retries):
        try:
            r = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            import os
            import time
            import argparse
            import requests
            import pandas as pd
            from datetime import datetime
            from typing import Any, Dict

            # Lee ticket desde variable de entorno si está presente; sino usa el valor embebido
            API_KEY = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
            BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
            UA = "Yesi-MP-Script/1.2 (+python requests)"


            def parse_licitaciones(payload: Any) -> list:
                """
                Normaliza los distintos formatos que puede devolver la API a una list[dict].
                Soporta:
                  - {"Listado": {"Licitacion": [ ... ]}}
                  - {"Listado": [ ... ]}
                  - {"Licitacion": [ ... ]}
                  - [ ... ]
                """
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


            def fetch_with_retries(params: Dict[str, str], max_retries: int = 5, backoff: float = 1.5) -> Any:
                """
                Realiza la petición a la API con reintentos exponenciales en errores 5xx o fallos transitorios.
                Devuelve el JSON parseado o lanza la excepción final.
                """
                headers = {"User-Agent": UA}
                last_err = None
                for i in range(max_retries):
                    try:
                        r = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
                        r.raise_for_status()
                        return r.json()
                    except requests.HTTPError as e:
                        last_err = e
                        code = getattr(e.response, "status_code", 0)
                        if 500 <= code < 600:
                            sleep_s = round((backoff ** i), 2)
                            print(f"⚠️  {e} → reintentando en {sleep_s}s... (intento {i+1}/{max_retries})")
                            time.sleep(sleep_s)
                            continue
                        raise
                    except Exception as e:
                        last_err = e
                        sleep_s = round((backoff ** i), 2)
                        print(f"⚠️  Error transitorio: {e} → reintentando en {sleep_s}s... (intento {i+1}/{max_retries})")
                        time.sleep(sleep_s)
                raise last_err


            def save_csv(df: pd.DataFrame, base_dir: str, prefix: str = "licitaciones") -> str:
                out_dir = os.path.join(base_dir, "data")
                os.makedirs(out_dir, exist_ok=True)
                fecha = datetime.now().strftime("%Y%m%d")
                csv_file = os.path.join(out_dir, f"{prefix}_{fecha}.csv")
                df.to_csv(csv_file, index=False, encoding="utf-8-sig")
                return csv_file


            def main() -> None:
                parser = argparse.ArgumentParser(description="Descarga licitaciones de Mercado Público (CLI unificada).")
                parser.add_argument("--fecha", help="Fecha ddmmaaaa (ej: 03102025). Si se usa, ignora --estado.")
                parser.add_argument("--estado", default="activas", help="Estado diario (activas, publicadas, cerradas, etc.). Default: activas")
                parser.add_argument("--ticket", help="Ticket/API key (sobrescribe MERCADO_PUBLICO_TICKET env var).")
                parser.add_argument("--max-retries", type=int, default=5, help="Reintentos ante 5xx. Default: 5")
                args = parser.parse_args()

                ticket = args.ticket or API_KEY

                if args.fecha:
                    params = {"fecha": args.fecha, "ticket": ticket}
                    prefix = f"licitaciones_fecha_{args.fecha}"
                    print(f"🔎 Consultando por fecha = {args.fecha} ...")
                else:
                    params = {"estado": args.estado, "ticket": ticket}
                    prefix = f"licitaciones_estado_{args.estado}"
                    print(f"🔎 Consultando por estado = {args.estado} ...")

                try:
                    payload = fetch_with_retries(params, max_retries=args.max_retries)
                    lic = parse_licitaciones(payload)
                    df = pd.DataFrame(lic)

                    base_dir = os.path.dirname(__file__)
                    csv_path = save_csv(df, base_dir, prefix=prefix)

                    print(f"✅ Filas guardadas: {len(df)}")
                    print(f"📄 Archivo: {csv_path}")

                    # Vista rápida de columnas útiles si existen
                    vista = [c for c in ("CodigoExterno", "Nombre", "Estado", "FechaCierre", "MontoEstimado") if c in df.columns]
                    if vista:
                        print("👀 Preview:")
                        print(df[vista].head(5).to_string(index=False))
                    else:
                        print(f"ℹ️ Columnas: {list(df.columns)[:10]} ...")

                except Exception as e:
                    print(f"❌ Error final: {e}")


            if __name__ == "__main__":
                main()
        prefix = f"licitaciones_fecha_{args.fecha}"
        print(f"🔎 Consultando por fecha = {args.fecha} ...")
    else:
        params = {"estado": args.estado, "ticket": API_KEY}
        prefix = f"licitaciones_estado_{args.estado}"
        print(f"🔎 Consultando por estado = {args.estado} ...")

    try:
        payload = fetch_with_retries(params)
        lic = parse_licitaciones(payload)
        df = pd.DataFrame(lic)

        base_dir = os.path.dirname(__file__)
        csv_path = save_csv(df, base_dir, prefix=prefix)

        print(f"✅ Filas guardadas: {len(df)}")
        print(f"📄 Archivo: {csv_path}")

        # Vista rápida de columnas útiles si existen
        vista = [c for c in ("CodigoExterno","Nombre","Estado","FechaCierre","MontoEstimado") if c in df.columns]
        if vista:
            print("👀 Preview:")
            print(df[vista].head(5).to_string(index=False))
        else:
            print(f"ℹ️ Columnas: {list(df.columns)[:10]} ...")

    except Exception as e:
        print(f"❌ Error final: {e}")

if __name__ == "__main__":
    main()
import os
import time
import argparse
import sqlite3
import requests
import pandas as pd
from datetime import datetime

API_KEY = "BB946777-2A2E-4685-B5F5-43B441772C27"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
UA = "Yesi-MP-Script/1.1 (+python requests)"

def parse_licitaciones(payload):
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
    return []

def fetch_with_retries(params, max_retries=5, backoff=1.5):
    headers = {"User-Agent": UA}
    last_err = None
    for i in range(max_retries):
        try:
            r = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            last_err = e
            code = getattr(e.response, "status_code", 0)
            if 500 <= code < 600:
                sleep_s = round((backoff ** i), 2)
                print(f"⚠️  {e} → reintento en {sleep_s}s...")
                time.sleep(sleep_s)
                continue
            raise
        except Exception as e:
            last_err = e
            print(f"⚠️  Error transitorio: {e} → reintentando...")
            time.sleep(backoff ** i)
    raise last_err

def ensure_dirs(base_dir):
    raw_dir   = os.path.join(base_dir, "data", "raw")
    clean_dir = os.path.join(base_dir, "data", "clean")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(clean_dir, exist_ok=True)
    return raw_dir, clean_dir

def normalize(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Aplana campos anidados típicos: Fechas.*, Comprador.*, Items.*
    df = df_raw.copy()

    # json_normalize cuando haya dicts/arrays dentro
    if any(df.applymap(lambda x: isinstance(x, (dict, list))).any()):
        df = pd.json_normalize(df_raw.to_dict(orient="records"), sep=".")

    # Montos a numérico
    for col in ["MontoEstimado", "Monto", "MontoTotal"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fechas clave (ajusta según columnas disponibles)
    date_cols = [
        "FechaCierre",
        "Fechas.FechaCierre",
        "Fechas.FechaPublicacion",
        "Fechas.FechaCreacion",
        "Fechas.FechaUltimaModificacion",
        "Fechas.FechaAperturaTecnica",
        "Fechas.FechaAperturaEconomica",
    ]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # Identificadores y metadatos útiles si existen
    keep_if_exist = [
        "CodigoExterno", "Nombre", "Estado", "Descripcion",
        "Comprador.NombreOrganismo", "Comprador.RutUnidad", "Comprador.CodigoOrganismo",
        "Categorias.Categoria.Categoria", "Items.Item.Cantidad",
        "UnidadTiempoDuracionContrato", "DuracionContrato",
        "Region", "SubSector", "Justificacion",
        "MontoEstimado", "Monto", "MontoTotal",
        "FechaCierre", "Fechas.FechaCierre", "Fechas.FechaPublicacion"
    ]
    cols = [c for c in keep_if_exist if c in df.columns]
    if cols:
        df = df[cols + [c for c in df.columns if c not in cols]]  # prioriza campos clave al inicio

    return df


def extract_fields(licitacion: dict) -> dict:
    """
    Extrae y aplana los campos solicitados de un dict de licitacion.
    Campos devueltos (claves de dict):
    """licitaciones.py

    CLI para descargar licitaciones desde la API publica de MercadoPublico,
    normalizar resultados y exportar tres CSV: raw, clean y requested (campos solicitados).

    Salida:
     - data/raw/licitaciones_*_raw_YYYYMMDD.csv
     - data/clean/licitaciones_*_clean_YYYYMMDD.csv
     - data/clean/licitaciones_*_requested_YYYYMMDD.csv
     - data/mp.sqlite (opcional)
    """

    import os
    import time
    import argparse
    import sqlite3
    import requests
    import pandas as pd
    from datetime import datetime
    from typing import Any, Dict


    API_KEY = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
    BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
    UA = "licitaciones-script/1.0"


    def parse_licitaciones(payload: Any) -> list:
        """Normaliza varias formas de respuesta de la API a una lista de dicts."""
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


    def fetch_with_retries(params: Dict[str, str], max_retries: int = 5, backoff: float = 1.5) -> Any:
        """Realiza la peticion a la API con reintentos exponenciales en errores transitorios (5xx).

        Lanza la ultima excepcion si se agotan los reintentos.
        """
        headers = {"User-Agent": UA}
        last_err = None
        for i in range(max_retries):
            try:
                r = requests.get(BASE_URL, params=params, headers=headers, timeout=60)
                r.raise_for_status()
                return r.json()
            except requests.HTTPError as e:
                last_err = e
                code = getattr(e.response, "status_code", 0)
                if 500 <= code < 600:
                    sleep_s = backoff ** i
                    print(f"Server error {code}, retrying in {sleep_s:.1f}s (attempt {i+1}/{max_retries})")
                    time.sleep(sleep_s)
                    continue
                raise
            except Exception as e:
                last_err = e
                sleep_s = backoff ** i
                print(f"Transient error: {e}, retrying in {sleep_s:.1f}s (attempt {i+1}/{max_retries})")
                time.sleep(sleep_s)
        raise last_err


    def ensure_dirs(base_dir: str):
        raw_dir = os.path.join(base_dir, "data", "raw")
        clean_dir = os.path.join(base_dir, "data", "clean")
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(clean_dir, exist_ok=True)
        return raw_dir, clean_dir


    def normalize(df_raw: pd.DataFrame) -> pd.DataFrame:
        """Aplana estructuras anidadas y normaliza columnas de monto y fecha."""
        df = df_raw.copy()
        try:
            if any(df.applymap(lambda x: isinstance(x, (dict, list))).any()):
                df = pd.json_normalize(df_raw.to_dict(orient="records"), sep=".")
        except Exception:
            pass

        for col in ["MontoEstimado", "Monto", "MontoTotal"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for c in list(df.columns):
            if "Fecha" in c:
                try:
                    df[c] = pd.to_datetime(df[c], errors="coerce")
                except Exception:
                    pass

        return df


    def extract_fields(licitacion: dict) -> dict:
        """Extrae los campos exactamente solicitados y los aplana.

        Campos solicitados (verbatim):
        FechaCierre, Descripcion, Estado, Comprador.NombreOrganismo, Comprador.NombreUnidad,
        Comprador.ComunaUnidad, Comprador.RegionUnidad, Comprador.NombreUsuario,
        Comprador.CargoUsuario, CodigoTipo, TipoConvocatoria, MontoEstimado, Modalidad,
        EmailResponsablePago
        """
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
        parser = argparse.ArgumentParser(description="Descarga y procesa licitaciones de MercadoPublico.")
        parser.add_argument("--fecha", help="Fecha ddmmaaaa (ej: 03102025). Si se usa, ignora --estado.")
        parser.add_argument("--estado", default="activas", help="Estado (activas, publicadas, cerradas). Default: activas")
        parser.add_argument("--ticket", help="Ticket/API key (sobrescribe variable de entorno)")
        parser.add_argument("--max-retries", type=int, default=5, help="Reintentos ante 5xx")
        args = parser.parse_args()

        ticket = args.ticket or API_KEY
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

            db_path = to_sqlite(df_clean, base_dir, table)

            print(f"Filas RAW:       {len(df_raw)}  -> {raw_path}")
            print(f"Filas CLEAN:     {len(df_clean)} -> {clean_path}")
            print(f"Filas REQUESTED: {len(df_requested)} -> {requested_path}")
            print(f"SQLite DB: {db_path} (tabla: {table})")

        except Exception as e:
            print(f"Error final: {e}")


    if __name__ == "__main__":
        main()


        except Exception as e:
            print(f"❌ Error final: {e}")


    if __name__ == "__main__":
        main()





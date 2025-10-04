"""
Licitaciones Refactorizado: Sistema optimizado para descarga y procesamiento de datos de Mercado Público.

Características principales:
- Evaluación previa de la API antes de ejecutar el script principal
- Lógica de negocio basada en definición de campos requeridos
- Manejo robusto de errores y reintentos
- Sistema de logging para trazabilidad
- Configuración centralizada
- Validación de datos según diccionario de negocio

Autor: Sistema ETL Optimizado
Versión: 2.0
"""

import os
import time
import argparse
import sqlite3
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Importar sistema de configuración
try:
    from config_env import cargar_config, CargadorConfiguracion, ConfiguracionAPI
    CONFIG_ENV_AVAILABLE = True
except ImportError:
    CONFIG_ENV_AVAILABLE = False
    print("⚠️  config_env.py no disponible. Usando configuración básica.")

# Cargar configuración desde variables de entorno
if CONFIG_ENV_AVAILABLE:
    try:
        config = cargar_config()
        logger = config.configurar_logging()
        print("✅ Configuración cargada desde variables de entorno")
    except Exception as e:
        print(f"⚠️  Error cargando configuración: {e}")
        print("📝 Usando configuración por defecto...")
        # Configuración básica como fallback
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('licitaciones.log'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        # Crear configuración básica
        config = None
else:
    # Configuración básica si no hay config_env.py
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('licitaciones.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    config = None

class EstadoLicitacion(Enum):
    """Estados válidos para consulta de licitaciones"""
    ACTIVAS = "activas"
    PUBLICADAS = "publicadas"
    CERRADAS = "cerradas"
    ADJUDICADAS = "adjudicadas"

# Configuración básica como fallback si no hay config_env.py
if not CONFIG_ENV_AVAILABLE or config is None:
    @dataclass
    class ConfiguracionAPI:
        """Configuración básica como fallback"""
        BASE_URL: str = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
        USER_AGENT: str = "ETL-Mercado-Publico/2.0"
        TIMEOUT: int = 60
        MAX_RETRIES: int = 6
        BACKOFF_FACTOR: float = 2.0
        RATE_LIMIT_HEADER: str = "Retry-After"
        DATA_BASE_DIR: str = "data"
        DATA_RAW_DIR: str = "data/raw"
        DATA_CLEAN_DIR: str = "data/clean"
        SQLITE_DB_NAME: str = "mp.sqlite"
        LOG_LEVEL: str = "INFO"
        LOG_FILE: str = "licitaciones.log"
        
        # Campos requeridos según diccionario de negocio
        CAMPOS_REQUERIDOS: List[str] = None
        
        def __post_init__(self):
            if self.CAMPOS_REQUERIDOS is None:
                self.CAMPOS_REQUERIDOS = [
                    "FechaCierre",
                    "Descripcion", 
                    "Estado",
                    "Comprador.NombreOrganismo",
                    "Comprador.NombreUnidad",
                    "Comprador.ComunaUnidad",
                    "Comprador.RegionUnidad",
                    "Comprador.NombreUsuario",
                    "Comprador.CargoUsuario",
                    "CodigoTipo",
                    "TipoConvocatoria",
                    "MontoEstimado",
                    "Modalidad",
                    "EmailResponsablePago"
                ]
        
        def obtener_ticket_seguro(self, mostrar_info: bool = False) -> str:
            """Obtiene el ticket de forma segura"""
            ticket = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
            if mostrar_info:
                return ticket
            else:
                return f"{ticket[:8]}..." if len(ticket) > 8 else "***"
        
        def obtener_nivel_log(self) -> int:
            return logging.INFO
        
        def obtener_ruta_sqlite(self) -> str:
            return os.path.join(self.DATA_BASE_DIR, self.SQLITE_DB_NAME)
        
        def es_modo_desarrollo(self) -> bool:
            return False
        
        def configurar_logging(self) -> logging.Logger:
            return logger

@dataclass
class ResultadoEvaluacionAPI:
    """Resultado de la evaluación previa de la API"""
    disponible: bool
    estructura_valida: bool
    campos_encontrados: List[str]
    total_registros: int
    mensaje: str
    tiempo_respuesta: float

class EvaluadorAPI:
    """Clase para evaluar el estado y estructura de la API antes del procesamiento principal"""
    
    def __init__(self, config: ConfiguracionAPI):
        self.config = config
        
    def evaluar_api(self, ticket: str, fecha: Optional[str] = None, estado: str = "activas") -> ResultadoEvaluacionAPI:
        """
        Evalúa la disponibilidad y estructura de la API de Mercado Público
        
        Args:
            ticket: API key para autenticación
            fecha: Fecha específica (formato ddmmaaaa) o None para usar estado
            estado: Estado de licitaciones si no se especifica fecha
            
        Returns:
            ResultadoEvaluacionAPI con información detallada
        """
        inicio = time.time()
        
        try:
            # Preparar parámetros de consulta
            params = {"ticket": ticket}
            if fecha:
                params["fecha"] = fecha
                logger.info(f"Evaluando API por fecha: {fecha}")
            else:
                params["estado"] = estado
                logger.info(f"Evaluando API por estado: {estado}")
            
            # Realizar petición de evaluación
            headers = {"User-Agent": self.config.USER_AGENT}
            response = requests.get(
                self.config.BASE_URL, 
                params=params, 
                headers=headers, 
                timeout=self.config.TIMEOUT
            )
            
            tiempo_respuesta = time.time() - inicio
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    licitaciones = self._parsear_licitaciones(data)
                    
                    if licitaciones:
                        # Analizar estructura de datos
                        campos_encontrados = self._analizar_campos(licitaciones[0])
                        estructura_valida = self._validar_estructura(campos_encontrados)
                        
                        return ResultadoEvaluacionAPI(
                            disponible=True,
                            estructura_valida=estructura_valida,
                            campos_encontrados=campos_encontrados,
                            total_registros=len(licitaciones),
                            mensaje=f"API disponible. {len(licitaciones)} registros encontrados. Estructura: {'válida' if estructura_valida else 'con advertencias'}",
                            tiempo_respuesta=tiempo_respuesta
                        )
                    else:
                        return ResultadoEvaluacionAPI(
                            disponible=True,
                            estructura_valida=False,
                            campos_encontrados=[],
                            total_registros=0,
                            mensaje="API disponible pero sin datos",
                            tiempo_respuesta=tiempo_respuesta
                        )
                except ValueError as e:
                    return ResultadoEvaluacionAPI(
                        disponible=False,
                        estructura_valida=False,
                        campos_encontrados=[],
                        total_registros=0,
                        mensaje=f"Error al parsear JSON: {e}",
                        tiempo_respuesta=tiempo_respuesta
                    )
            else:
                return ResultadoEvaluacionAPI(
                    disponible=False,
                    estructura_valida=False,
                    campos_encontrados=[],
                    total_registros=0,
                    mensaje=f"API no disponible. Status: {response.status_code}",
                    tiempo_respuesta=tiempo_respuesta
                )
                
        except requests.RequestException as e:
            tiempo_respuesta = time.time() - inicio
            return ResultadoEvaluacionAPI(
                disponible=False,
                estructura_valida=False,
                campos_encontrados=[],
                total_registros=0,
                mensaje=f"Error de conexión: {e}",
                tiempo_respuesta=tiempo_respuesta
            )
    
    def _parsear_licitaciones(self, payload: Any) -> List[Dict[str, Any]]:
        """Parsea la respuesta de la API para extraer licitaciones"""
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
    
    def _analizar_campos(self, licitacion: Dict[str, Any]) -> List[str]:
        """Analiza los campos disponibles en una licitación"""
        campos = []
        
        def extraer_campos(obj: Any, prefijo: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    campo_completo = f"{prefijo}.{key}" if prefijo else key
                    campos.append(campo_completo)
                    if isinstance(value, (dict, list)):
                        extraer_campos(value, campo_completo)
            elif isinstance(obj, list) and obj:
                extraer_campos(obj[0], prefijo)
        
        extraer_campos(licitacion)
        return campos
    
    def _validar_estructura(self, campos_encontrados: List[str]) -> bool:
        """Valida si la estructura contiene los campos requeridos"""
        campos_requeridos = self.config.CAMPOS_REQUERIDOS
        campos_faltantes = []
        
        for campo in campos_requeridos:
            if not any(campo in c for c in campos_encontrados):
                campos_faltantes.append(campo)
        
        if campos_faltantes:
            logger.warning(f"Campos requeridos faltantes: {campos_faltantes}")
            return False
        
        return True

class ProcesadorLicitaciones:
    """Clase principal para el procesamiento de licitaciones"""
    
    def __init__(self, config: ConfiguracionAPI):
        self.config = config
        self.evaluador = EvaluadorAPI(config)
    
    def obtener_ticket(self, ticket_explicito: Optional[str] = None) -> str:
        """Obtiene el ticket de API desde parámetros, configuración o variable de entorno"""
        if ticket_explicito:
            return ticket_explicito
        
        # Usar configuración cargada si está disponible
        if CONFIG_ENV_AVAILABLE and config and hasattr(config, 'TICKET') and config.TICKET:
            return config.TICKET
        
        # Fallback a variable de entorno
        ticket_env = os.environ.get("MERCADO_PUBLICO_TICKET")
        if ticket_env:
            return ticket_env
        
        # Último recurso: ticket por defecto (solo para desarrollo)
        logger.warning("⚠️  Usando ticket por defecto. Configura MERCADO_PUBLICO_TICKET para producción.")
        return "BB946777-2A2E-4685-B5F5-43B441772C27"
    
    def fetch_con_reintentos(self, params: Dict[str, str], max_retries: Optional[int] = None) -> Any:
        """Realiza petición con reintentos y manejo de rate limiting"""
        max_retries = max_retries or self.config.MAX_RETRIES
        headers = {"User-Agent": self.config.USER_AGENT}
        last_error = None
        
        for intento in range(1, max_retries + 1):
            try:
                response = requests.get(
                    self.config.BASE_URL, 
                    params=params, 
                    headers=headers, 
                    timeout=self.config.TIMEOUT
                )
                
                if response.status_code == 429:
                    retry_after = response.headers.get(self.config.RATE_LIMIT_HEADER)
                    wait_time = self._calcular_tiempo_espera(retry_after, intento)
                    logger.warning(f"Rate limit alcanzado. Esperando {wait_time}s (intento {intento}/{max_retries})")
                    time.sleep(wait_time)
                    last_error = Exception("HTTP 429 Rate limit")
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.HTTPError as e:
                last_error = e
                codigo = getattr(e.response, "status_code", 0)
                if 500 <= codigo < 600:
                    wait_time = min(60, int(self.config.BACKOFF_FACTOR ** intento))
                    logger.warning(f"Error 5xx ({codigo}). Reintentando en {wait_time}s (intento {intento}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise
                
            except requests.RequestException as e:
                last_error = e
                wait_time = min(60, int(self.config.BACKOFF_FACTOR ** intento))
                logger.warning(f"Error de red: {e}. Reintentando en {wait_time}s (intento {intento}/{max_retries})")
                time.sleep(wait_time)
                
        logger.error("Máximo de reintentos alcanzado")
        raise last_error
    
    def _calcular_tiempo_espera(self, retry_after: Optional[str], intento: int) -> int:
        """Calcula el tiempo de espera para rate limiting"""
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return min(60, int(self.config.BACKOFF_FACTOR ** intento))
    
    def normalizar_datos(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Normaliza los datos de licitaciones"""
        df = df_raw.copy()
        
        try:
            # Detectar y aplanar estructuras anidadas
            has_nested = any(df.applymap(lambda x: isinstance(x, (dict, list))).any())
            if has_nested:
                df = pd.json_normalize(df_raw.to_dict(orient="records"), sep=".")
                logger.info("Estructuras anidadas aplanadas")
        except Exception as e:
            logger.warning(f"Error al aplanar estructuras: {e}")
        
        # Normalizar montos
        for col in ["MontoEstimado", "Monto", "MontoTotal"]:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Normalizar fechas
        for col in df.columns:
            if "Fecha" in col:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass
        
        return df
    
    def extraer_campos_negocio(self, licitacion: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae campos según definición de negocio"""
        resultado = {
            "FechaCierre": licitacion.get("FechaCierre"),
            "Descripcion": licitacion.get("Descripcion") or licitacion.get("DescripcionLarga") or licitacion.get("Nombre"),
            "Estado": licitacion.get("Estado"),
            "CodigoTipo": licitacion.get("CodigoTipo"),
            "TipoConvocatoria": licitacion.get("TipoConvocatoria"),
            "MontoEstimado": licitacion.get("MontoEstimado") or licitacion.get("Monto"),
            "Modalidad": licitacion.get("Modalidad"),
            "EmailResponsablePago": licitacion.get("EmailResponsablePago"),
            "Comprador.NombreOrganismo": None,
            "Comprador.NombreUnidad": None,
            "Comprador.ComunaUnidad": None,
            "Comprador.RegionUnidad": None,
            "Comprador.NombreUsuario": None,
            "Comprador.CargoUsuario": None,
        }
        
        # Procesar información del comprador
        comprador = licitacion.get("Comprador") or {}
        if isinstance(comprador, list) and comprador:
            comprador = comprador[0]
        
        if isinstance(comprador, dict):
            resultado["Comprador.NombreOrganismo"] = comprador.get("NombreOrganismo")
            resultado["Comprador.NombreUnidad"] = comprador.get("NombreUnidad") or comprador.get("Unidad")
            resultado["Comprador.ComunaUnidad"] = comprador.get("ComunaUnidad")
            resultado["Comprador.RegionUnidad"] = comprador.get("RegionUnidad")
            resultado["Comprador.NombreUsuario"] = comprador.get("NombreUsuario") or comprador.get("NombreResponsable")
            resultado["Comprador.CargoUsuario"] = comprador.get("CargoUsuario") or comprador.get("CargoResponsable")
        
        return resultado
    
    def guardar_datos(self, df: pd.DataFrame, directorio: str, prefijo: str) -> str:
        """Guarda DataFrame como CSV"""
        os.makedirs(directorio, exist_ok=True)
        fecha = datetime.now().strftime("%Y%m%d")
        ruta = os.path.join(directorio, f"{prefijo}_{fecha}.csv")
        df.to_csv(ruta, index=False, encoding="utf-8-sig")
        return ruta
    
    def guardar_sqlite(self, df: pd.DataFrame, directorio_base: str, nombre_tabla: str) -> str:
        """Guarda DataFrame en base de datos SQLite"""
        ruta_db = self.config.obtener_ruta_sqlite()
        os.makedirs(os.path.dirname(ruta_db), exist_ok=True)
        
        with sqlite3.connect(ruta_db) as conn:
            df.to_sql(nombre_tabla, conn, if_exists="append", index=False)
        
        return ruta_db
    
    def procesar_licitaciones(self, ticket: str, fecha: Optional[str] = None, estado: str = "activas") -> Dict[str, Any]:
        """Proceso principal de descarga y procesamiento"""
        
        # 1. Evaluación previa de la API
        logger.info("Iniciando evaluación previa de la API...")
        evaluacion = self.evaluador.evaluar_api(ticket, fecha, estado)
        
        if not evaluacion.disponible:
            raise Exception(f"API no disponible: {evaluacion.mensaje}")
        
        logger.info(f"Evaluación completada: {evaluacion.mensaje}")
        
        if not evaluacion.estructura_valida:
            logger.warning("Estructura de datos con advertencias, continuando...")
        
        # 2. Descarga de datos
        logger.info("Descargando datos de licitaciones...")
        params = {"ticket": ticket}
        if fecha:
            params["fecha"] = fecha
        else:
            params["estado"] = estado
        
        payload = self.fetch_con_reintentos(params)
        licitaciones = self.evaluador._parsear_licitaciones(payload)
        
        if not licitaciones:
            raise Exception("No se encontraron licitaciones")
        
        # 3. Procesamiento de datos
        logger.info(f"Procesando {len(licitaciones)} licitaciones...")
        
        df_raw = pd.DataFrame(licitaciones)
        df_normalizado = self.normalizar_datos(df_raw)
        
        campos_negocio = [self.extraer_campos_negocio(item) for item in licitaciones]
        df_negocio = pd.DataFrame(campos_negocio)
        
        # Normalizar fechas y montos en datos de negocio
        if "FechaCierre" in df_negocio.columns:
            df_negocio["FechaCierre"] = pd.to_datetime(df_negocio["FechaCierre"], errors="coerce")
        if "MontoEstimado" in df_negocio.columns:
            df_negocio["MontoEstimado"] = pd.to_numeric(df_negocio["MontoEstimado"], errors="coerce")
        
        # 4. Guardado de resultados
        directorio_base = os.path.dirname(__file__)
        directorio_raw = os.path.join(directorio_base, self.config.DATA_RAW_DIR)
        directorio_clean = os.path.join(directorio_base, self.config.DATA_CLEAN_DIR)
        
        prefijo = f"licitaciones_fecha_{fecha}" if fecha else f"licitaciones_estado_{estado}"
        nombre_tabla = prefijo
        
        rutas = {
            "raw": self.guardar_datos(df_raw, directorio_raw, f"{prefijo}_raw"),
            "clean": self.guardar_datos(df_normalizado, directorio_clean, f"{prefijo}_clean"),
            "negocio": self.guardar_datos(df_negocio, directorio_clean, f"{prefijo}_requested")
        }
        
        try:
            rutas["sqlite"] = self.guardar_sqlite(df_normalizado, directorio_base, nombre_tabla)
        except Exception as e:
            logger.warning(f"No se pudo guardar en SQLite: {e}")
            rutas["sqlite"] = "No disponible"
        
        return {
            "evaluacion": evaluacion,
            "datos": {
                "raw": df_raw,
                "clean": df_normalizado,
                "negocio": df_negocio
            },
            "rutas": rutas,
            "estadisticas": {
                "total_registros": len(licitaciones),
                "tiempo_procesamiento": evaluacion.tiempo_respuesta
            }
        }

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Sistema optimizado para descarga de licitaciones de Mercado Público"
    )
    parser.add_argument("--fecha", help="Fecha ddmmaaaa (ej: 04102025). No usar con --estado")
    parser.add_argument("--estado", default="activas", 
                       choices=[e.value for e in EstadoLicitacion],
                       help="Estado de licitaciones. Default: activas")
    parser.add_argument("--ticket", help="Ticket/API key (sobrescribe configuración)")
    parser.add_argument("--max-retries", type=int, help="Máximo de reintentos (sobrescribe configuración)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging detallado")
    parser.add_argument("--config-file", help="Archivo .env personalizado")
    parser.add_argument("--show-config", action="store_true", help="Mostrar configuración cargada")
    
    args = parser.parse_args()
    
    # Cargar configuración
    global config
    try:
        if args.config_file:
            config = CargadorConfiguracion.cargar_configuracion(args.config_file)
        else:
            config = CargadorConfiguracion.cargar_configuracion()
        
        # Configurar logging
        logger = config.configurar_logging()
        
        # Ajustar nivel de logging si se solicita verbose
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            print("🔍 Modo verbose activado")
        
        # Mostrar configuración si se solicita
        if args.show_config:
            CargadorConfiguracion._mostrar_configuracion(config)
        
        # Sobrescribir configuración con argumentos de línea de comandos
        if args.max_retries is not None:
            config.MAX_RETRIES = args.max_retries
            logger.info(f"Max retries sobrescrito: {args.max_retries}")
        
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        print("📝 Usando configuración básica...")
        # Crear configuración básica como fallback
        config = ConfiguracionAPI()
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        if args.max_retries is not None:
            config.MAX_RETRIES = args.max_retries
    
    # Validaciones
    if args.fecha and args.estado != "activas":
        logger.warning("Fecha especificada, ignorando estado")
    
    procesador = ProcesadorLicitaciones(config)
    ticket = procesador.obtener_ticket(args.ticket)
    
    try:
        logger.info("Iniciando procesamiento de licitaciones...")
        resultado = procesador.procesar_licitaciones(ticket, args.fecha, args.estado)
        
        # Mostrar resultados
        print("\n" + "="*60)
        print("RESULTADOS DEL PROCESAMIENTO")
        print("="*60)
        print(f"📊 Total de registros: {resultado['estadisticas']['total_registros']}")
        print(f"⏱️  Tiempo de respuesta API: {resultado['evaluacion'].tiempo_respuesta:.2f}s")
        print(f"✅ API disponible: {resultado['evaluacion'].disponible}")
        print(f"📋 Estructura válida: {resultado['evaluacion'].estructura_valida}")
        
        print("\n📁 Archivos generados:")
        for tipo, ruta in resultado['rutas'].items():
            if ruta != "No disponible":
                filas = len(resultado['datos'][tipo]) if tipo != 'sqlite' else 'N/A'
                print(f"  {tipo.upper()}: {ruta} ({filas} filas)" if filas != 'N/A' else f"  {tipo.upper()}: {ruta}")
        
        print(f"\n📝 Mensaje: {resultado['evaluacion'].mensaje}")
        
    except Exception as e:
        logger.error(f"Error en procesamiento: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

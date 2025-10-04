"""
Sistema de configuración basado en variables de entorno.
Maneja la carga de configuración desde archivos .env y variables de sistema.
"""

import os
import logging
from typing import Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv no disponible. Usando solo variables de entorno del sistema.")

@dataclass
class ConfiguracionAPI:
    """Configuración centralizada de la API de Mercado Público usando variables de entorno"""
    
    # API Configuration
    BASE_URL: str = field(default_factory=lambda: os.getenv("MERCADO_PUBLICO_BASE_URL", "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"))
    USER_AGENT: str = field(default_factory=lambda: os.getenv("MERCADO_PUBLICO_USER_AGENT", "ETL-Mercado-Publico/2.0"))
    TICKET: str = field(default_factory=lambda: os.getenv("MERCADO_PUBLICO_TICKET", ""))
    
    # Connection Configuration
    TIMEOUT: int = field(default_factory=lambda: int(os.getenv("HTTP_TIMEOUT", "60")))
    MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "6")))
    BACKOFF_FACTOR: float = field(default_factory=lambda: float(os.getenv("BACKOFF_FACTOR", "2.0")))
    RATE_LIMIT_HEADER: str = field(default_factory=lambda: os.getenv("RATE_LIMIT_HEADER", "Retry-After"))
    
    # File Configuration
    DATA_BASE_DIR: str = field(default_factory=lambda: os.getenv("DATA_BASE_DIR", "data"))
    DATA_RAW_DIR: str = field(default_factory=lambda: os.getenv("DATA_RAW_DIR", "data/raw"))
    DATA_CLEAN_DIR: str = field(default_factory=lambda: os.getenv("DATA_CLEAN_DIR", "data/clean"))
    SQLITE_DB_NAME: str = field(default_factory=lambda: os.getenv("SQLITE_DB_NAME", "mp.sqlite"))
    
    # Logging Configuration
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: str = field(default_factory=lambda: os.getenv("LOG_FILE", "licitaciones.log"))
    LOG_DATE_FORMAT: str = field(default_factory=lambda: os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S"))
    
    # Processing Configuration
    BATCH_SIZE: int = field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "1000")))
    ENABLE_PARALLEL_PROCESSING: bool = field(default_factory=lambda: os.getenv("ENABLE_PARALLEL_PROCESSING", "false").lower() == "true")
    PARALLEL_WORKERS: int = field(default_factory=lambda: int(os.getenv("PARALLEL_WORKERS", "4")))
    
    # Validation Configuration
    ENABLE_STRICT_VALIDATION: bool = field(default_factory=lambda: os.getenv("ENABLE_STRICT_VALIDATION", "true").lower() == "true")
    FIELD_VALIDATION_TOLERANCE: float = field(default_factory=lambda: float(os.getenv("FIELD_VALIDATION_TOLERANCE", "10")))
    
    # Monitoring Configuration
    ENABLE_PERFORMANCE_METRICS: bool = field(default_factory=lambda: os.getenv("ENABLE_PERFORMANCE_METRICS", "true").lower() == "true")
    METRICS_REPORT_INTERVAL: int = field(default_factory=lambda: int(os.getenv("METRICS_REPORT_INTERVAL", "30")))
    
    # Security Configuration
    VERIFY_SSL: bool = field(default_factory=lambda: os.getenv("VERIFY_SSL", "true").lower() == "true")
    SSL_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("SSL_TIMEOUT", "30")))
    
    # Development Configuration
    DEVELOPMENT_MODE: bool = field(default_factory=lambda: os.getenv("DEVELOPMENT_MODE", "false").lower() == "true")
    DEBUG_MODE: bool = field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    SHOW_SENSITIVE_INFO: bool = field(default_factory=lambda: os.getenv("SHOW_SENSITIVE_INFO", "false").lower() == "true")
    
    # Business Logic - Campos requeridos según diccionario
    CAMPOS_REQUERIDOS: List[str] = field(default_factory=lambda: [
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
    ])
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        self._validar_configuracion()
        self._crear_directorios()
    
    def _validar_configuracion(self):
        """Valida la configuración cargada"""
        errores = []
        
        # Validar ticket
        if not self.TICKET:
            errores.append("MERCADO_PUBLICO_TICKET no está configurado")
        
        # Validar timeout
        if self.TIMEOUT <= 0:
            errores.append("HTTP_TIMEOUT debe ser mayor a 0")
        
        # Validar reintentos
        if self.MAX_RETRIES < 0:
            errores.append("MAX_RETRIES debe ser mayor o igual a 0")
        
        # Validar backoff factor
        if self.BACKOFF_FACTOR <= 0:
            errores.append("BACKOFF_FACTOR debe ser mayor a 0")
        
        # Validar nivel de log
        niveles_validos = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL.upper() not in niveles_validos:
            errores.append(f"LOG_LEVEL debe ser uno de: {niveles_validos}")
        
        # Validar tolerancia de validación
        if not (0 <= self.FIELD_VALIDATION_TOLERANCE <= 100):
            errores.append("FIELD_VALIDATION_TOLERANCE debe estar entre 0 y 100")
        
        if errores:
            raise ValueError(f"Errores de configuración: {'; '.join(errores)}")
    
    def _crear_directorios(self):
        """Crea los directorios necesarios si no existen"""
        directorios = [
            self.DATA_BASE_DIR,
            self.DATA_RAW_DIR,
            self.DATA_CLEAN_DIR,
            os.path.dirname(self.LOG_FILE) if os.path.dirname(self.LOG_FILE) else "."
        ]
        
        for directorio in directorios:
            if directorio and not os.path.exists(directorio):
                os.makedirs(directorio, exist_ok=True)
    
    def obtener_ticket_seguro(self, mostrar_info: bool = False) -> str:
        """Obtiene el ticket de forma segura, sin exponer información sensible"""
        if not self.TICKET:
            raise ValueError("MERCADO_PUBLICO_TICKET no está configurado. Configura la variable de entorno o crea un archivo .env")
        
        if mostrar_info and self.SHOW_SENSITIVE_INFO:
            return self.TICKET
        else:
            return f"{self.TICKET[:8]}..." if len(self.TICKET) > 8 else "***"
    
    def obtener_nivel_log(self) -> int:
        """Convierte el string de nivel de log a constante de logging"""
        return getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
    
    def obtener_ruta_sqlite(self) -> str:
        """Obtiene la ruta completa de la base de datos SQLite"""
        return os.path.join(self.DATA_BASE_DIR, self.SQLITE_DB_NAME)
    
    def es_modo_desarrollo(self) -> bool:
        """Verifica si está en modo desarrollo"""
        return self.DEVELOPMENT_MODE or self.DEBUG_MODE
    
    def configurar_logging(self) -> logging.Logger:
        """Configura el sistema de logging según la configuración"""
        logger = logging.getLogger(__name__)
        
        # Limpiar handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Configurar nivel
        logger.setLevel(self.obtener_nivel_log())
        
        # Formato
        formatter = logging.Formatter(
            f'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt=self.LOG_DATE_FORMAT
        )
        
        # Handler para archivo
        file_handler = logging.FileHandler(self.LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger

class CargadorConfiguracion:
    """Carga y gestiona la configuración desde diferentes fuentes"""
    
    @staticmethod
    def cargar_configuracion(archivo_env: Optional[str] = None, 
                           usar_variables_sistema: bool = True) -> ConfiguracionAPI:
        """
        Carga la configuración desde archivo .env y variables de entorno
        
        Args:
            archivo_env: Ruta al archivo .env (default: .env en directorio actual)
            usar_variables_sistema: Si usar variables de entorno del sistema
        
        Returns:
            ConfiguracionAPI configurada
        """
        
        # Cargar archivo .env si está disponible
        if DOTENV_AVAILABLE:
            archivos_env = []
            
            # Archivos .env a buscar en orden de prioridad
            if archivo_env:
                archivos_env.append(archivo_env)
            else:
                archivos_env.extend([
                    ".env",
                    ".env.local",
                    ".env.development",
                    ".env.production"
                ])
            
            # Intentar cargar cada archivo
            for archivo in archivos_env:
                if os.path.exists(archivo):
                    load_dotenv(archivo, override=False)  # No sobrescribir variables existentes
                    print(f"✅ Configuración cargada desde: {archivo}")
                    break
            else:
                if not usar_variables_sistema:
                    print("⚠️  No se encontró archivo .env y usar_variables_sistema=False")
        else:
            print("⚠️  python-dotenv no disponible, usando solo variables de entorno del sistema")
        
        # Cargar configuración
        try:
            config = ConfiguracionAPI()
            print(f"✅ Configuración cargada exitosamente")
            
            # Mostrar información de configuración (sin datos sensibles)
            if config.es_modo_desarrollo():
                CargadorConfiguracion._mostrar_configuracion(config)
            
            return config
            
        except ValueError as e:
            print(f"❌ Error en configuración: {e}")
            raise
    
    @staticmethod
    def _mostrar_configuracion(config: ConfiguracionAPI):
        """Muestra la configuración actual (solo en modo desarrollo)"""
        print("\n" + "="*60)
        print("🔧 CONFIGURACIÓN CARGADA")
        print("="*60)
        print(f"🌐 URL Base: {config.BASE_URL}")
        print(f"🤖 User Agent: {config.USER_AGENT}")
        print(f"🔑 Ticket: {config.obtener_ticket_seguro()}")
        print(f"⏱️  Timeout: {config.TIMEOUT}s")
        print(f"🔄 Max Retries: {config.MAX_RETRIES}")
        print(f"📈 Backoff Factor: {config.BACKOFF_FACTOR}")
        print(f"📁 Directorio Base: {config.DATA_BASE_DIR}")
        print(f"📊 Log Level: {config.LOG_LEVEL}")
        print(f"📝 Log File: {config.LOG_FILE}")
        print(f"🔧 Modo Desarrollo: {config.es_modo_desarrollo()}")
        print("="*60)
    
    @staticmethod
    def crear_archivo_env_ejemplo(ruta: str = ".env.ejemplo"):
        """Crea un archivo .env de ejemplo"""
        contenido = """# Configuración del Sistema ETL - Mercado Público
# Copia este archivo como .env y configura los valores

# API de Mercado Público
MERCADO_PUBLICO_TICKET=tu-api-key-aqui
MERCADO_PUBLICO_BASE_URL=https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json
MERCADO_PUBLICO_USER_AGENT=ETL-Mercado-Publico/2.0

# Configuración de conexión
HTTP_TIMEOUT=60
MAX_RETRIES=6
BACKOFF_FACTOR=2.0

# Configuración de archivos
DATA_BASE_DIR=data
DATA_RAW_DIR=data/raw
DATA_CLEAN_DIR=data/clean
SQLITE_DB_NAME=mp.sqlite

# Configuración de logging
LOG_LEVEL=INFO
LOG_FILE=licitaciones.log

# Configuración de desarrollo
DEVELOPMENT_MODE=false
DEBUG_MODE=false
SHOW_SENSITIVE_INFO=false
"""
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print(f"✅ Archivo de ejemplo creado: {ruta}")

# Función de conveniencia para cargar configuración
def cargar_config() -> ConfiguracionAPI:
    """Función de conveniencia para cargar la configuración"""
    return CargadorConfiguracion.cargar_configuracion()

if __name__ == "__main__":
    # Ejemplo de uso
    try:
        config = cargar_config()
        print("✅ Configuración cargada exitosamente")
        
        # Mostrar configuración segura
        print(f"🔑 Ticket: {config.obtener_ticket_seguro()}")
        print(f"🌐 URL: {config.BASE_URL}")
        print(f"📁 Directorio: {config.DATA_BASE_DIR}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Sugerencias:")
        print("1. Copia env.template como .env")
        print("2. Configura MERCADO_PUBLICO_TICKET")
        print("3. Ajusta otros parámetros según necesites")

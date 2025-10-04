# Sistema ETL Refactorizado - Mercado Público

## 🚀 Mejoras Implementadas

### Evaluación Previa de la API
- **Verificación de disponibilidad**: Antes de ejecutar el procesamiento principal, el sistema evalúa el estado de la API
- **Validación de estructura**: Verifica que los campos requeridos según el diccionario de negocio estén presentes
- **Análisis de rendimiento**: Mide tiempos de respuesta y detecta problemas potenciales

### Arquitectura Optimizada
- **Separación de responsabilidades**: Clases especializadas para evaluación, procesamiento y configuración
- **Configuración centralizada**: Todos los parámetros de la API en un solo lugar
- **Sistema de logging**: Trazabilidad completa de operaciones y errores

### Lógica de Negocio
- **Campos requeridos**: Validación basada en el diccionario de datos del proyecto
- **Procesamiento inteligente**: Manejo optimizado de estructuras anidadas y tipos de datos
- **Validación de datos**: Verificación de integridad antes del guardado

### Manejo Robusto de Errores
- **Rate limiting inteligente**: Respeta límites de la API con backoff exponencial
- **Reintentos adaptativos**: Manejo diferenciado de errores 5xx, 429 y errores de red
- **Recuperación graceful**: Continúa operación incluso con errores menores

## 📁 Estructura de Archivos

```
├── licitaciones_refactorizado.py    # Sistema principal refactorizado
├── test_refactorizado.py            # Script de pruebas
├── licitaciones.log                 # Logs del sistema
└── data/
    ├── raw/                         # Datos originales de la API
    ├── clean/                       # Datos normalizados
    └── mp.sqlite                    # Base de datos SQLite
```

## 🛠️ Uso del Sistema

### Pruebas Iniciales
```bash
# Verificar que el sistema funciona correctamente
python test_refactorizado.py
```

### Procesamiento Principal
```bash
# Por estado (default: activas)
python licitaciones_refactorizado.py --estado activas

# Por fecha específica
python licitaciones_refactorizado.py --fecha 04102025

# Con configuración personalizada
python licitaciones_refactorizado.py --estado activas --max-retries 10 --verbose
```

### Parámetros Disponibles
- `--fecha`: Fecha en formato ddmmaaaa (ej: 04102025)
- `--estado`: Estado de licitaciones (activas, publicadas, cerradas, adjudicadas)
- `--ticket`: API key personalizada (sobrescribe variable de entorno)
- `--max-retries`: Número máximo de reintentos (default: 6)
- `--verbose`: Logging detallado

## 🔧 Configuración

### Variable de Entorno
```bash
export MERCADO_PUBLICO_TICKET="tu-api-key-aqui"
```

### Configuración del Sistema
La clase `ConfiguracionAPI` permite personalizar:
- URL base de la API
- Timeout de peticiones
- Número de reintentos
- Factor de backoff
- Campos requeridos según diccionario

## 📊 Campos de Negocio Procesados

Según el diccionario de datos del proyecto:
- `FechaCierre`
- `Descripcion`
- `Estado`
- `Comprador.NombreOrganismo`
- `Comprador.NombreUnidad`
- `Comprador.ComunaUnidad`
- `Comprador.RegionUnidad`
- `Comprador.NombreUsuario`
- `Comprador.CargoUsuario`
- `CodigoTipo`
- `TipoConvocatoria`
- `MontoEstimado`
- `Modalidad`
- `EmailResponsablePago`

## 📈 Mejoras de Rendimiento

### Antes (Código Original)
- ❌ Código duplicado y confuso
- ❌ Sin evaluación previa de la API
- ❌ Manejo básico de errores
- ❌ Sin validación de estructura
- ❌ Sin logging

### Después (Código Refactorizado)
- ✅ Arquitectura limpia y modular
- ✅ Evaluación previa completa
- ✅ Manejo robusto de errores y rate limiting
- ✅ Validación de campos según diccionario
- ✅ Sistema de logging completo
- ✅ Configuración centralizada
- ✅ Mejor trazabilidad y debugging

## 🔍 Monitoreo y Logs

### Archivo de Log
El sistema genera logs detallados en `licitaciones.log`:
- Timestamps de todas las operaciones
- Información de evaluación de API
- Errores y reintentos
- Estadísticas de procesamiento

### Salida en Consola
- Estado de evaluación de la API
- Número de registros procesados
- Rutas de archivos generados
- Tiempos de respuesta
- Advertencias y errores

## 🚨 Manejo de Errores

### Tipos de Errores Manejados
1. **Rate Limiting (HTTP 429)**: Respeta headers Retry-After
2. **Errores 5xx**: Reintentos con backoff exponencial
3. **Errores de Red**: Reintentos automáticos
4. **Estructura Inválida**: Advertencias pero continúa procesamiento
5. **API No Disponible**: Falla rápida con mensaje claro

### Recuperación Automática
- Reintentos inteligentes con tiempos adaptativos
- Continuación de procesamiento con datos parciales
- Logging detallado para debugging

## 🎯 Beneficios del Refactoring

1. **Confiabilidad**: Evaluación previa evita fallos en medio del procesamiento
2. **Mantenibilidad**: Código modular y bien documentado
3. **Escalabilidad**: Fácil agregar nuevas funcionalidades
4. **Debugging**: Logs detallados para identificar problemas
5. **Eficiencia**: Manejo optimizado de rate limiting y errores
6. **Cumplimiento**: Validación de campos según definición de negocio

## 🔄 Migración desde Código Original

Para migrar del código original:
1. Ejecutar `test_refactorizado.py` para verificar compatibilidad
2. Usar `licitaciones_refactorizado.py` en lugar de `licitaciones.py`
3. Revisar logs en `licitaciones.log` para monitoreo
4. Ajustar configuración según necesidades específicas

## 📞 Soporte

En caso de problemas:
1. Revisar logs en `licitaciones.log`
2. Ejecutar con `--verbose` para más detalles
3. Verificar conectividad y API key
4. Consultar documentación de la API de Mercado Público

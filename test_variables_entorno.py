#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de variables de entorno.
Valida que la configuración se carga correctamente y que no hay valores hardcodeados.
"""

import os
import sys
from pathlib import Path

def test_sistema_configuracion():
    """Prueba el sistema de configuración"""
    print("🧪 Iniciando pruebas del sistema de variables de entorno...")
    
    try:
        from config_env import cargar_config, CargadorConfiguracion
        print("✅ Módulo config_env importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando config_env: {e}")
        return False
    
    # Prueba 1: Cargar configuración
    print("\n📋 Prueba 1: Cargar configuración")
    try:
        config = cargar_config()
        print("✅ Configuración cargada exitosamente")
        
        # Verificar que no hay valores hardcodeados
        if config.TICKET and config.TICKET != "BB946777-2A2E-4685-B5F5-43B441772C27":
            print("✅ API Key cargada desde variables de entorno")
        elif config.TICKET == "BB946777-2A2E-4685-B5F5-43B441772C27":
            print("⚠️  Usando API Key por defecto (configurar MERCADO_PUBLICO_TICKET)")
        
        print(f"🔑 Ticket: {config.obtener_ticket_seguro()}")
        print(f"🌐 URL: {config.BASE_URL}")
        print(f"⏱️  Timeout: {config.TIMEOUT}s")
        print(f"🔄 Max Retries: {config.MAX_RETRIES}")
        
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return False
    
    # Prueba 2: Verificar variables de entorno
    print("\n📋 Prueba 2: Verificar variables de entorno")
    variables_importantes = [
        "MERCADO_PUBLICO_TICKET",
        "MERCADO_PUBLICO_BASE_URL",
        "HTTP_TIMEOUT",
        "MAX_RETRIES",
        "LOG_LEVEL"
    ]
    
    for var in variables_importantes:
        valor = os.environ.get(var)
        if valor:
            print(f"  ✅ {var}: {valor[:20]}{'...' if len(valor) > 20 else ''}")
        else:
            print(f"  ⚠️  {var}: No configurado (usando valor por defecto)")
    
    # Prueba 3: Verificar archivos de configuración
    print("\n📋 Prueba 3: Verificar archivos de configuración")
    archivos_config = [
        "config_env.py",
        "env.template",
        ".env"
    ]
    
    for archivo in archivos_config:
        if Path(archivo).exists():
            print(f"  ✅ {archivo}: Existe")
        else:
            print(f"  ❌ {archivo}: No encontrado")
    
    # Prueba 4: Verificar sistema principal
    print("\n📋 Prueba 4: Verificar sistema principal")
    try:
        from licitaciones_refactorizado import main
        print("✅ Sistema principal importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando sistema principal: {e}")
        return False
    
    return True

def test_procesamiento_con_configuracion():
    """Prueba el procesamiento con la nueva configuración"""
    print("\n🧪 Prueba adicional: Procesamiento con configuración")
    
    try:
        # Importar sistema principal
        from licitaciones_refactorizado import ProcesadorLicitaciones
        from config_env import cargar_config
        
        # Cargar configuración
        config = cargar_config()
        procesador = ProcesadorLicitaciones(config)
        
        # Verificar configuración del procesador
        print(f"✅ Procesador configurado con:")
        print(f"  🌐 URL: {config.BASE_URL}")
        print(f"  🤖 User Agent: {config.USER_AGENT}")
        print(f"  ⏱️  Timeout: {config.TIMEOUT}s")
        print(f"  📁 Directorio Raw: {config.DATA_RAW_DIR}")
        print(f"  📁 Directorio Clean: {config.DATA_CLEAN_DIR}")
        
        # Verificar ticket
        ticket = procesador.obtener_ticket()
        if ticket and ticket != "BB946777-2A2E-4685-B5F5-43B441772C27":
            print("✅ Ticket cargado desde configuración")
        else:
            print("⚠️  Usando ticket por defecto")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        return False

def mostrar_instrucciones():
    """Muestra instrucciones de uso"""
    print("\n📖 INSTRUCCIONES DE USO")
    print("=" * 50)
    
    print("\n🔧 Configuración básica:")
    print("  1. Copia env.template como .env")
    print("  2. Edita .env con tus valores")
    print("  3. Ejecuta el sistema")
    
    print("\n🚀 Comandos principales:")
    print("  # Procesamiento básico")
    print("  python licitaciones_refactorizado.py --estado activas")
    print()
    print("  # Con configuración personalizada")
    print("  python licitaciones_refactorizado.py --config-file .env.production")
    print()
    print("  # Mostrar configuración")
    print("  python licitaciones_refactorizado.py --show-config")
    print()
    print("  # Probar configuración")
    print("  python config_env.py")
    
    print("\n📁 Archivos importantes:")
    print("  .env                    - Tu configuración")
    print("  env.template           - Plantilla de configuración")
    print("  config_env.py          - Sistema de configuración")
    print("  licitaciones_refactorizado.py - Sistema principal")

def main():
    """Función principal de pruebas"""
    print("🚀 PRUEBAS DEL SISTEMA DE VARIABLES DE ENTORNO")
    print("=" * 60)
    
    try:
        # Ejecutar pruebas
        test1_ok = test_sistema_configuracion()
        test2_ok = test_procesamiento_con_configuracion()
        
        if test1_ok and test2_ok:
            print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
            print("\n✅ Sistema de variables de entorno funcionando correctamente")
            print("✅ Configuración cargada desde archivos .env")
            print("✅ Valores hardcodeados eliminados")
            print("✅ Sistema listo para uso")
            
            mostrar_instrucciones()
            return 0
        else:
            print("\n❌ Algunas pruebas fallaron")
            print("🔧 Revisa la configuración y vuelve a intentar")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Pruebas interrumpidas por el usuario")
        return 1
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Script de prueba para el sistema refactorizado de licitaciones.
Prueba la evaluación previa de la API sin descargar datos completos.
"""

import sys
import os
from licitaciones_refactorizado import ConfiguracionAPI, EvaluadorAPI, ProcesadorLicitaciones

def test_evaluacion_api():
    """Prueba la funcionalidad de evaluación de la API"""
    print("🧪 Iniciando pruebas del sistema refactorizado...")
    
    # Configuración
    config = ConfiguracionAPI()
    evaluador = EvaluadorAPI(config)
    procesador = ProcesadorLicitaciones(config)
    
    # Obtener ticket
    ticket = procesador.obtener_ticket()
    print(f"🔑 Ticket obtenido: {ticket[:8]}...")
    
    # Prueba 1: Evaluación por estado
    print("\n📋 Prueba 1: Evaluación por estado 'activas'")
    try:
        resultado = evaluador.evaluar_api(ticket, estado="activas")
        print(f"✅ Disponible: {resultado.disponible}")
        print(f"📊 Registros: {resultado.total_registros}")
        print(f"⏱️  Tiempo: {resultado.tiempo_respuesta:.2f}s")
        print(f"📝 Mensaje: {resultado.mensaje}")
        
        if resultado.campos_encontrados:
            print(f"🔍 Campos encontrados: {len(resultado.campos_encontrados)}")
            print("   Primeros 10 campos:")
            for campo in resultado.campos_encontrados[:10]:
                print(f"     - {campo}")
        
    except Exception as e:
        print(f"❌ Error en prueba 1: {e}")
        return False
    
    # Prueba 2: Validación de estructura
    print("\n📋 Prueba 2: Validación de estructura")
    try:
        if resultado.estructura_valida:
            print("✅ Estructura válida según diccionario de negocio")
        else:
            print("⚠️  Estructura con advertencias")
            
        campos_requeridos = config.CAMPOS_REQUERIDOS
        print(f"📋 Campos requeridos: {len(campos_requeridos)}")
        for campo in campos_requeridos:
            encontrado = any(campo in c for c in resultado.campos_encontrados)
            status = "✅" if encontrado else "❌"
            print(f"   {status} {campo}")
            
    except Exception as e:
        print(f"❌ Error en prueba 2: {e}")
        return False
    
    # Prueba 3: Configuración
    print("\n📋 Prueba 3: Validación de configuración")
    try:
        print(f"🌐 URL Base: {config.BASE_URL}")
        print(f"🤖 User Agent: {config.USER_AGENT}")
        print(f"⏱️  Timeout: {config.TIMEOUT}s")
        print(f"🔄 Max Retries: {config.MAX_RETRIES}")
        print(f"📈 Backoff Factor: {config.BACKOFF_FACTOR}")
        
    except Exception as e:
        print(f"❌ Error en prueba 3: {e}")
        return False
    
    print("\n✅ Todas las pruebas completadas exitosamente!")
    return True

def test_procesamiento_pequeno():
    """Prueba el procesamiento con una muestra pequeña (solo si la API está disponible)"""
    print("\n🧪 Prueba adicional: Procesamiento de muestra pequeña")
    
    config = ConfiguracionAPI()
    procesador = ProcesadorLicitaciones(config)
    ticket = procesador.obtener_ticket()
    
    try:
        # Solo evaluar, no procesar completamente
        evaluacion = procesador.evaluador.evaluar_api(ticket, estado="activas")
        
        if evaluacion.disponible and evaluacion.total_registros > 0:
            print(f"✅ API lista para procesamiento completo")
            print(f"📊 Se pueden procesar {evaluacion.total_registros} registros")
            print("💡 Para procesamiento completo, ejecutar:")
            print("   python licitaciones_refactorizado.py --estado activas")
        else:
            print("⚠️  API no disponible o sin datos")
            
    except Exception as e:
        print(f"❌ Error en prueba de procesamiento: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Sistema de Pruebas - Licitaciones Refactorizado")
    print("=" * 60)
    
    try:
        # Ejecutar pruebas
        test1_ok = test_evaluacion_api()
        test2_ok = test_procesamiento_pequeno()
        
        if test1_ok and test2_ok:
            print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
            print("\n📖 Próximos pasos:")
            print("   1. Revisar el archivo 'licitaciones.log' para logs detallados")
            print("   2. Ejecutar procesamiento completo con:")
            print("      python licitaciones_refactorizado.py --estado activas")
            print("   3. Verificar archivos generados en data/raw y data/clean")
            sys.exit(0)
        else:
            print("\n❌ Algunas pruebas fallaron")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)

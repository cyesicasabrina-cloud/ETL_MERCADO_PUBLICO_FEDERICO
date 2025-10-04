#!/usr/bin/env python3
"""
Script de migración del sistema original al refactorizado.
Facilita la transición y verifica compatibilidad.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

def mostrar_banner():
    """Muestra el banner del script de migración"""
    print("=" * 70)
    print("🔄 SISTEMA DE MIGRACIÓN - LICITACIONES REFACTORIZADO")
    print("=" * 70)
    print("Este script facilita la migración del sistema original al refactorizado")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

def verificar_dependencias():
    """Verifica que las dependencias estén instaladas"""
    print("\n📦 Verificando dependencias...")
    
    dependencias = ['pandas', 'requests', 'openpyxl']
    faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - FALTANTE")
            faltantes.append(dep)
    
    if faltantes:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(faltantes)}")
        respuesta = input("¿Instalar automáticamente? (s/n): ").lower().strip()
        if respuesta in ['s', 'si', 'y', 'yes']:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + faltantes, check=True)
                print("✅ Dependencias instaladas correctamente")
                return True
            except subprocess.CalledProcessError:
                print("❌ Error al instalar dependencias")
                return False
        else:
            print("❌ No se pueden continuar las pruebas sin las dependencias")
            return False
    
    print("✅ Todas las dependencias están disponibles")
    return True

def crear_backup():
    """Crea backup del código original"""
    print("\n💾 Creando backup del sistema original...")
    
    archivos_originales = [
        'licitaciones.py',
        'requirements.txt',
        'README.md'
    ]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backup_original_{timestamp}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        for archivo in archivos_originales:
            if os.path.exists(archivo):
                shutil.copy2(archivo, backup_dir)
                print(f"  ✅ {archivo} -> {backup_dir}/")
        
        print(f"✅ Backup creado en: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

def ejecutar_pruebas():
    """Ejecuta las pruebas del sistema refactorizado"""
    print("\n🧪 Ejecutando pruebas del sistema refactorizado...")
    
    try:
        resultado = subprocess.run(
            [sys.executable, 'test_refactorizado.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if resultado.returncode == 0:
            print("✅ Pruebas ejecutadas exitosamente")
            print("📋 Resumen de pruebas:")
            print(resultado.stdout)
            return True
        else:
            print("❌ Las pruebas fallaron")
            print("📋 Error:")
            print(resultado.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Las pruebas tardaron demasiado (timeout)")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        return False

def comparar_archivos():
    """Compara archivos generados por ambos sistemas"""
    print("\n📊 Comparando archivos generados...")
    
    # Verificar si existen archivos del sistema original
    archivos_originales = [
        'data/licitaciones_20251004.csv'
    ]
    
    # Verificar archivos del sistema refactorizado
    archivos_refactorizado = [
        'data/raw/licitaciones_estado_activas_raw_20251004.csv',
        'data/clean/licitaciones_estado_activas_clean_20251004.csv',
        'data/clean/licitaciones_estado_activas_requested_20251004.csv'
    ]
    
    print("📁 Archivos del sistema original:")
    for archivo in archivos_originales:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"  ✅ {archivo} ({size:,} bytes)")
        else:
            print(f"  ❌ {archivo} - No encontrado")
    
    print("\n📁 Archivos del sistema refactorizado:")
    for archivo in archivos_refactorizado:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"  ✅ {archivo} ({size:,} bytes)")
        else:
            print(f"  ❌ {archivo} - No encontrado")

def mostrar_instrucciones():
    """Muestra instrucciones de uso del sistema refactorizado"""
    print("\n📖 INSTRUCCIONES DE USO DEL SISTEMA REFACTORIZADO")
    print("=" * 60)
    
    print("\n🔧 Comandos principales:")
    print("  # Pruebas del sistema")
    print("  python test_refactorizado.py")
    print()
    print("  # Procesamiento por estado")
    print("  python licitaciones_refactorizado.py --estado activas")
    print()
    print("  # Procesamiento por fecha")
    print("  python licitaciones_refactorizado.py --fecha 04102025")
    print()
    print("  # Con logging detallado")
    print("  python licitaciones_refactorizado.py --estado activas --verbose")
    
    print("\n📁 Estructura de archivos generados:")
    print("  data/raw/          - Datos originales de la API")
    print("  data/clean/        - Datos normalizados y de negocio")
    print("  data/mp.sqlite     - Base de datos SQLite")
    print("  licitaciones.log   - Logs del sistema")
    
    print("\n🔍 Monitoreo:")
    print("  # Ver logs en tiempo real")
    print("  tail -f licitaciones.log")
    print()
    print("  # Verificar archivos generados")
    print("  ls -la data/clean/")

def main():
    """Función principal del script de migración"""
    mostrar_banner()
    
    # Paso 1: Verificar dependencias
    if not verificar_dependencias():
        print("\n❌ No se puede continuar sin las dependencias necesarias")
        return 1
    
    # Paso 2: Crear backup
    backup_dir = crear_backup()
    if not backup_dir:
        print("\n⚠️  Continuando sin backup...")
    
    # Paso 3: Ejecutar pruebas
    if not ejecutar_pruebas():
        print("\n❌ Las pruebas fallaron. Revisa los errores antes de continuar.")
        respuesta = input("¿Continuar de todas formas? (s/n): ").lower().strip()
        if respuesta not in ['s', 'si', 'y', 'yes']:
            return 1
    
    # Paso 4: Comparar archivos
    comparar_archivos()
    
    # Paso 5: Mostrar instrucciones
    mostrar_instrucciones()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("🎉 MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print("✅ Sistema refactorizado listo para uso")
    print("✅ Backup del sistema original creado")
    print("✅ Pruebas ejecutadas exitosamente")
    print()
    print("📝 Próximos pasos:")
    print("  1. Revisar archivos generados en data/")
    print("  2. Monitorear logs en licitaciones.log")
    print("  3. Usar licitaciones_refactorizado.py en lugar de licitaciones.py")
    print("  4. Configurar variables de entorno si es necesario")
    
    if backup_dir:
        print(f"\n💾 Backup disponible en: {backup_dir}")
    
    print("\n🚀 ¡Sistema listo para producción!")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado durante la migración: {e}")
        sys.exit(1)

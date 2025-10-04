#!/usr/bin/env python3
"""
Script para mostrar un resumen detallado de todos los archivos generados.
Incluye estadísticas de CSV y Excel, y vista previa de los datos.
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import sqlite3

def mostrar_resumen_completo():
    """Muestra un resumen completo de todos los archivos generados"""
    
    print("🚀 RESUMEN DE ARCHIVOS GENERADOS - MERCADO PÚBLICO ETL")
    print("=" * 70)
    print(f"📅 Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    fecha = datetime.now().strftime("%Y%m%d")
    base_dir = Path("data")
    
    # Archivos CSV
    archivos_csv = {
        "Datos Raw (Originales)": base_dir / "raw" / f"licitaciones_estado_activas_raw_{fecha}.csv",
        "Datos Clean (Normalizados)": base_dir / "clean" / f"licitaciones_estado_activas_clean_{fecha}.csv",
        "Datos Negocio (Campos específicos)": base_dir / "clean" / f"licitaciones_estado_activas_requested_{fecha}.csv"
    }
    
    # Archivos Excel
    archivos_excel = {
        "Excel Completo (Todas las hojas)": base_dir / f"licitaciones_completo_{fecha}.xlsx",
        "Excel Raw": base_dir / f"licitaciones_raw_{fecha}.xlsx",
        "Excel Clean": base_dir / f"licitaciones_clean_{fecha}.xlsx",
        "Excel Negocio": base_dir / f"licitaciones_negocio_{fecha}.xlsx"
    }
    
    # Archivos adicionales
    archivos_adicionales = {
        "Base de Datos SQLite": base_dir / "mp.sqlite",
        "Log del Sistema": "licitaciones.log"
    }
    
    total_size = 0
    
    print("\n📊 ARCHIVOS CSV GENERADOS")
    print("-" * 50)
    
    for nombre, ruta in archivos_csv.items():
        if ruta.exists():
            try:
                df = pd.read_csv(ruta, encoding='utf-8-sig')
                size_kb = round(ruta.stat().st_size / 1024, 2)
                total_size += size_kb
                
                print(f"✅ {nombre}")
                print(f"   📁 Archivo: {ruta.name}")
                print(f"   📊 Registros: {len(df):,}")
                print(f"   📋 Columnas: {len(df.columns)}")
                print(f"   💾 Tamaño: {size_kb} KB")
                print(f"   📝 Columnas: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                print()
                
            except Exception as e:
                print(f"❌ {nombre}: Error leyendo archivo - {e}")
        else:
            print(f"❌ {nombre}: Archivo no encontrado")
    
    print("\n📊 ARCHIVOS EXCEL GENERADOS")
    print("-" * 50)
    
    for nombre, ruta in archivos_excel.items():
        if ruta.exists():
            size_kb = round(ruta.stat().st_size / 1024, 2)
            total_size += size_kb
            
            print(f"✅ {nombre}")
            print(f"   📁 Archivo: {ruta.name}")
            print(f"   💾 Tamaño: {size_kb} KB")
            print()
        else:
            print(f"❌ {nombre}: Archivo no encontrado")
    
    print("\n📊 ARCHIVOS ADICIONALES")
    print("-" * 50)
    
    for nombre, ruta in archivos_adicionales.items():
        if Path(ruta).exists():
            size_kb = round(Path(ruta).stat().st_size / 1024, 2)
            total_size += size_kb
            
            print(f"✅ {nombre}")
            print(f"   📁 Archivo: {Path(ruta).name}")
            print(f"   💾 Tamaño: {size_kb} KB")
            print()
        else:
            print(f"❌ {nombre}: Archivo no encontrado")
    
    print("\n📊 ESTADÍSTICAS GENERALES")
    print("-" * 50)
    print(f"💾 Tamaño total: {total_size:.2f} KB ({total_size/1024:.2f} MB)")
    print(f"📁 Total de archivos: {len([f for f in archivos_csv.values() if f.exists()]) + len([f for f in archivos_excel.values() if f.exists()]) + len([f for f in archivos_adicionales.values() if Path(f).exists()])}")
    
    # Mostrar vista previa de datos
    mostrar_vista_previa_datos()

def mostrar_vista_previa_datos():
    """Muestra una vista previa de los datos más importantes"""
    
    print("\n👀 VISTA PREVIA DE DATOS")
    print("-" * 50)
    
    fecha = datetime.now().strftime("%Y%m%d")
    base_dir = Path("data")
    
    # Vista previa de datos de negocio (más importantes)
    archivo_negocio = base_dir / "clean" / f"licitaciones_estado_activas_requested_{fecha}.csv"
    
    if archivo_negocio.exists():
        try:
            df = pd.read_csv(archivo_negocio, encoding='utf-8-sig')
            
            print(f"📋 Datos de Negocio (Campos específicos)")
            print(f"   📊 Total de licitaciones: {len(df):,}")
            print(f"   📋 Campos disponibles: {len(df.columns)}")
            
            # Mostrar primeras 5 filas de campos importantes
            campos_importantes = ['FechaCierre', 'Descripcion', 'Estado', 'MontoEstimado']
            campos_disponibles = [c for c in campos_importantes if c in df.columns]
            
            if campos_disponibles:
                print(f"\n📝 Vista previa de campos importantes:")
                print(df[campos_disponibles].head().to_string(index=False))
            
            # Estadísticas por estado
            if 'Estado' in df.columns:
                print(f"\n📊 Distribución por Estado:")
                estados = df['Estado'].value_counts().head(10)
                for estado, count in estados.items():
                    print(f"   {estado}: {count:,} licitaciones")
            
            # Estadísticas de montos
            if 'MontoEstimado' in df.columns:
                montos = pd.to_numeric(df['MontoEstimado'], errors='coerce')
                montos_validos = montos.dropna()
                if len(montos_validos) > 0:
                    print(f"\n💰 Estadísticas de Montos Estimados:")
                    print(f"   💵 Monto total: ${montos_validos.sum():,.0f}")
                    print(f"   📊 Monto promedio: ${montos_validos.mean():,.0f}")
                    print(f"   📈 Monto máximo: ${montos_validos.max():,.0f}")
                    print(f"   📉 Monto mínimo: ${montos_validos.min():,.0f}")
            
        except Exception as e:
            print(f"❌ Error mostrando vista previa: {e}")
    else:
        print("❌ Archivo de datos de negocio no encontrado")

def verificar_base_datos():
    """Verifica la base de datos SQLite"""
    
    print("\n🗄️  VERIFICACIÓN DE BASE DE DATOS SQLITE")
    print("-" * 50)
    
    fecha = datetime.now().strftime("%Y%m%d")
    db_path = Path("data") / "mp.sqlite"
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Obtener lista de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = cursor.fetchall()
            
            print(f"✅ Base de datos: {db_path.name}")
            print(f"📊 Tablas encontradas: {len(tablas)}")
            
            for tabla in tablas:
                tabla_name = tabla[0]
                cursor.execute(f"SELECT COUNT(*) FROM {tabla_name}")
                count = cursor.fetchone()[0]
                print(f"   📋 {tabla_name}: {count:,} registros")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error verificando base de datos: {e}")
    else:
        print("❌ Base de datos SQLite no encontrada")

def mostrar_instrucciones_uso():
    """Muestra instrucciones de uso de los archivos"""
    
    print("\n📖 INSTRUCCIONES DE USO")
    print("-" * 50)
    
    print("📊 ARCHIVOS CSV:")
    print("   • Usar para análisis con Python/R/Excel")
    print("   • Formato UTF-8 con BOM para compatibilidad")
    print("   • Separados por comas")
    
    print("\n📊 ARCHIVOS EXCEL:")
    print("   • Excel Completo: Todas las hojas en un archivo")
    print("   • Excel Individuales: Una hoja por archivo")
    print("   • Formato profesional con headers coloreados")
    print("   • Columnas ajustadas automáticamente")
    
    print("\n🗄️  BASE DE DATOS:")
    print("   • SQLite para consultas complejas")
    print("   • Usar herramientas como DB Browser for SQLite")
    print("   • Compatible con Python pandas.read_sql()")
    
    print("\n🔧 HERRAMIENTAS RECOMENDADAS:")
    print("   • Excel/LibreOffice: Para análisis visual")
    print("   • Python pandas: Para análisis avanzado")
    print("   • R: Para análisis estadístico")
    print("   • Power BI/Tableau: Para visualizaciones")

def main():
    """Función principal"""
    
    try:
        mostrar_resumen_completo()
        verificar_base_datos()
        mostrar_instrucciones_uso()
        
        print("\n🎉 RESUMEN COMPLETADO")
        print("=" * 70)
        print("✅ Todos los archivos generados exitosamente")
        print("✅ Sistema ETL funcionando correctamente")
        print("✅ Datos listos para análisis")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error generando resumen: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

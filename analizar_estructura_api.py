#!/usr/bin/env python3
"""
Script para analizar la estructura real de la API de Mercado Público
y verificar qué campos están disponibles vs. los campos del diccionario.
"""

import requests
import json
import pandas as pd
from datetime import datetime

def analizar_estructura_api():
    """Analiza la estructura real de la API"""
    
    print("🔍 ANÁLISIS DE ESTRUCTURA DE LA API DE MERCADO PÚBLICO")
    print("=" * 60)
    
    url = 'https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json'
    params = {
        'estado': 'activas',
        'ticket': 'BB946777-2A2E-4685-B5F5-43B441772C27'
    }
    
    try:
        print("📡 Consultando API...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API respondió correctamente")
            print(f"📊 Tamaño de respuesta: {len(response.text)} caracteres")
            
            # Analizar estructura
            if 'Listado' in data:
                listado = data['Listado']
                print(f"📋 'Listado' encontrado: {type(listado)}")
                
                if isinstance(listado, dict) and 'Licitacion' in listado:
                    licitaciones = listado['Licitacion']
                    print(f"📋 'Licitacion' encontrado: {len(licitaciones)} registros")
                    
                    if licitaciones:
                        primera = licitaciones[0]
                        print(f"\n🔍 ANÁLISIS DE PRIMERA LICITACIÓN")
                        print("-" * 40)
                        print(f"📊 Campos disponibles: {len(primera.keys())}")
                        
                        print(f"\n📝 CAMPOS DISPONIBLES:")
                        for i, (key, value) in enumerate(primera.items(), 1):
                            tipo = type(value).__name__
                            if isinstance(value, (dict, list)):
                                print(f"  {i:2d}. {key} ({tipo}) - {len(value) if hasattr(value, '__len__') else 'N/A'} elementos")
                            else:
                                valor_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                                print(f"  {i:2d}. {key} ({tipo}) - {valor_str}")
                        
                        # Analizar campos anidados
                        print(f"\n🔍 CAMPOS ANIDADOS DETALLADOS:")
                        for key, value in primera.items():
                            if isinstance(value, dict):
                                print(f"\n📁 {key}:")
                                for subkey, subvalue in value.items():
                                    tipo = type(subvalue).__name__
                                    valor_str = str(subvalue)[:30] + "..." if len(str(subvalue)) > 30 else str(subvalue)
                                    print(f"    - {subkey} ({tipo}): {valor_str}")
                            elif isinstance(value, list) and value:
                                print(f"\n📁 {key} (lista con {len(value)} elementos):")
                                if isinstance(value[0], dict):
                                    for subkey, subvalue in value[0].items():
                                        tipo = type(subvalue).__name__
                                        valor_str = str(subvalue)[:30] + "..." if len(str(subvalue)) > 30 else str(subvalue)
                                        print(f"    - {subkey} ({tipo}): {valor_str}")
                                else:
                                    print(f"    - Elemento tipo: {type(value[0]).__name__}")
                        
                        # Guardar estructura completa para análisis
                        with open('estructura_api_completa.json', 'w', encoding='utf-8') as f:
                            json.dump(primera, f, indent=2, ensure_ascii=False)
                        print(f"\n💾 Estructura completa guardada en: estructura_api_completa.json")
                        
                else:
                    print(f"❌ No se encontró 'Licitacion' en 'Listado'")
                    print(f"📋 Claves en 'Listado': {list(listado.keys()) if isinstance(listado, dict) else 'No es dict'}")
            else:
                print(f"❌ No se encontró 'Listado' en la respuesta")
                print(f"📋 Claves disponibles: {list(data.keys())}")
                
        else:
            print(f"❌ Error en API: {response.status_code}")
            print(f"📝 Respuesta: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def comparar_con_diccionario():
    """Compara los campos disponibles con el diccionario"""
    
    print(f"\n📋 COMPARACIÓN CON DICCIONARIO DE DATOS")
    print("-" * 50)
    
    # Leer diccionario
    try:
        with open('diccionarioDatos.txt', 'r', encoding='utf-8') as f:
            campos_requeridos = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"📊 Campos requeridos en diccionario: {len(campos_requeridos)}")
        for i, campo in enumerate(campos_requeridos, 1):
            print(f"  {i:2d}. {campo}")
        
        # Leer estructura de API
        try:
            with open('estructura_api_completa.json', 'r', encoding='utf-8') as f:
                estructura = json.load(f)
            
            campos_disponibles = list(estructura.keys())
            print(f"\n📊 Campos disponibles en API: {len(campos_disponibles)}")
            
            # Comparar
            print(f"\n🔍 ANÁLISIS DE COINCIDENCIAS:")
            campos_encontrados = []
            campos_faltantes = []
            
            for campo_requerido in campos_requeridos:
                # Extraer el nombre del campo (después del último /)
                campo_nombre = campo_requerido.split('/')[-1]
                
                if campo_nombre in campos_disponibles:
                    campos_encontrados.append(campo_requerido)
                    print(f"  ✅ {campo_requerido}")
                else:
                    campos_faltantes.append(campo_requerido)
                    print(f"  ❌ {campo_requerido}")
            
            print(f"\n📊 RESUMEN:")
            print(f"  ✅ Campos encontrados: {len(campos_encontrados)}")
            print(f"  ❌ Campos faltantes: {len(campos_faltantes)}")
            
            if campos_faltantes:
                print(f"\n💡 CAMPOS FALTANTES (posibles causas):")
                print(f"  1. La API puede requerir parámetros adicionales")
                print(f"  2. Los campos pueden estar en un endpoint diferente")
                print(f"  3. Los campos pueden requerir autenticación especial")
                print(f"  4. La estructura de la API puede haber cambiado")
                
        except FileNotFoundError:
            print(f"❌ No se encontró estructura_api_completa.json")
            
    except FileNotFoundError:
        print(f"❌ No se encontró diccionarioDatos.txt")

def analizar_endpoints_posibles():
    """Analiza posibles endpoints para obtener más campos"""
    
    print(f"\n🔍 ANÁLISIS DE ENDPOINTS POSIBLES")
    print("-" * 50)
    
    base_url = 'https://api.mercadopublico.cl/servicios/v1/publico'
    endpoints = [
        '/licitaciones.json',
        '/licitaciones/detalle.json',
        '/licitaciones/por_estado.json',
        '/licitaciones/por_fecha.json'
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            print(f"📡 Probando: {endpoint}")
            response = requests.get(url, params={'ticket': 'BB946777-2A2E-4685-B5F5-43B441772C27'}, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Disponible")
            else:
                print(f"   ❌ No disponible")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Función principal"""
    
    try:
        analizar_estructura_api()
        comparar_con_diccionario()
        analizar_endpoints_posibles()
        
        print(f"\n🎯 RECOMENDACIONES")
        print("-" * 50)
        print(f"1. Revisar la documentación PDF en carpeta 'documentacion'")
        print(f"2. Verificar si se requiere endpoint diferente para campos detallados")
        print(f"3. Considerar hacer consultas por ID específico de licitación")
        print(f"4. Revisar si los campos están en una respuesta diferente")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

if __name__ == "__main__":
    main()

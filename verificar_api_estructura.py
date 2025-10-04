#!/usr/bin/env python3
"""
Script para verificar y corregir las llamadas a la API de Mercado Público
según la documentación oficial con la estructura correcta de rutas.
"""

import requests
import json
import pandas as pd
from datetime import datetime

def probar_estructura_correcta():
    """Prueba la estructura correcta de la API según documentación"""
    
    print("🔍 VERIFICANDO ESTRUCTURA CORRECTA DE LA API")
    print("=" * 60)
    
    base_url = "https://api.mercadopublico.cl/servicios/v1/publico"
    ticket = "BB946777-2A2E-4685-B5F5-43B441772C27"
    
    # Tipos de licitación según documentación
    tipos_licitacion = {
        "L1": "Licitación Pública Menor a 100 UTM",
        "LE": "Licitación Pública igual o superior a 100 UTM e inferior a 1.000 UTM",
        "LP": "Licitación Pública igual o superior a 1.000 UTM e inferior a 2.000 UTM",
        "LQ": "Licitación Pública igual o superior a 2.000 UTM e inferior a 5.000 UTM",
        "LR": "Licitación Pública igual o superior a 5.000 UTM",
        "E2": "Licitación Privada Menor a 100 UTM",
        "CO": "Licitación Privada igual o superior a 100 UTM e inferior a 1000 UTM",
        "B2": "Licitación Privada igual o superior a 1000 UTM e inferior a 2000 UTM",
        "H2": "Licitación Privada igual o superior a 2000 UTM e inferior a 5000 UTM",
        "I2": "Licitación Privada Mayor a 5000 UTM",
        "LS": "Licitación Pública Servicios personales especializados"
    }
    
    # Estados posibles
    estados = ["activas", "publicadas", "cerradas", "adjudicadas"]
    
    print("📋 Estructura documentada:")
    print("Ruta: https://api.mercadopublico.cl/servicios/v1/publico/Licitaciones/<Listado>/<Licitacion>/<Tipo>")
    print("\nTipos de licitación disponibles:")
    for codigo, descripcion in tipos_licitacion.items():
        print(f"  {codigo}: {descripcion}")
    
    # Probar estructura actual (incorrecta)
    print(f"\n❌ ESTRUCTURA ACTUAL (INCORRECTA):")
    url_actual = f"{base_url}/licitaciones.json"
    print(f"URL: {url_actual}")
    
    try:
        response = requests.get(url_actual, params={'estado': 'activas', 'ticket': ticket}, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'Listado' in data:
                print(f"Campos disponibles: {len(data['Listado'][0].keys()) if data['Listado'] else 0}")
                print(f"Campos: {list(data['Listado'][0].keys()) if data['Listado'] else 'N/A'}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Probar estructura correcta según documentación
    print(f"\n✅ PROBANDO ESTRUCTURA CORRECTA:")
    
    # Primero obtener un código de licitación real
    try:
        response = requests.get(url_actual, params={'estado': 'activas', 'ticket': ticket}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data['Listado']:
                codigo_licitacion = data['Listado'][0]['CodigoExterno']
                print(f"Código de licitación obtenido: {codigo_licitacion}")
                
                # Probar estructura correcta
                for tipo in ["L1", "LE", "LP"]:  # Probar algunos tipos
                    url_correcta = f"{base_url}/Licitaciones/Listado/Licitacion/{tipo}"
                    print(f"\n📡 Probando: {url_correcta}")
                    
                    try:
                        response_correcta = requests.get(
                            url_correcta, 
                            params={'ticket': ticket, 'codigo': codigo_licitacion},
                            timeout=30
                        )
                        print(f"   Status: {response_correcta.status_code}")
                        
                        if response_correcta.status_code == 200:
                            data_correcta = response_correcta.json()
                            print(f"   ✅ Respuesta exitosa")
                            print(f"   Estructura: {list(data_correcta.keys()) if isinstance(data_correcta, dict) else type(data_correcta)}")
                            
                            # Guardar respuesta para análisis
                            with open(f'respuesta_correcta_{tipo}.json', 'w', encoding='utf-8') as f:
                                json.dump(data_correcta, f, indent=2, ensure_ascii=False)
                            print(f"   💾 Respuesta guardada en: respuesta_correcta_{tipo}.json")
                        else:
                            print(f"   ❌ Error: {response_correcta.status_code}")
                            print(f"   Respuesta: {response_correcta.text[:200]}...")
                            
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                
                # Probar con parámetros diferentes
                print(f"\n🔧 PROBANDO PARÁMETROS DIFERENTES:")
                
                parametros_variaciones = [
                    {'ticket': ticket, 'estado': 'activas'},
                    {'ticket': ticket, 'codigo': codigo_licitacion},
                    {'ticket': ticket, 'tipo': 'LE'},
                    {'ticket': ticket, 'fecha': '20251004'},
                    {'ticket': ticket}
                ]
                
                for i, params in enumerate(parametros_variaciones, 1):
                    url_test = f"{base_url}/Licitaciones/Listado/Licitacion/LE"
                    print(f"   🔧 Variación {i}: {list(params.keys())}")
                    
                    try:
                        response_test = requests.get(url_test, params=params, timeout=15)
                        print(f"      Status: {response_test.status_code}")
                        
                        if response_test.status_code == 200:
                            data_test = response_test.json()
                            if isinstance(data_test, dict):
                                campos = list(data_test.keys())
                                print(f"      ✅ {len(campos)} campos: {campos[:5]}{'...' if len(campos) > 5 else ''}")
                            elif isinstance(data_test, list):
                                print(f"      ✅ Lista con {len(data_test)} elementos")
                            else:
                                print(f"      ✅ Respuesta tipo: {type(data_test)}")
                        else:
                            print(f"      ❌ Error {response_test.status_code}")
                            
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                        
    except Exception as e:
        print(f"❌ Error obteniendo código de licitación: {e}")

def analizar_respuestas_correctas():
    """Analiza las respuestas de la estructura correcta"""
    
    print(f"\n🔍 ANÁLISIS DE RESPUESTAS CORRECTAS")
    print("-" * 50)
    
    archivos_respuesta = [
        'respuesta_correcta_L1.json',
        'respuesta_correcta_LE.json', 
        'respuesta_correcta_LP.json'
    ]
    
    for archivo in archivos_respuesta:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n📁 {archivo}:")
            if isinstance(data, dict):
                print(f"   Campos disponibles: {len(data.keys())}")
                print(f"   Campos: {list(data.keys())}")
                
                # Verificar si tiene campos del diccionario
                campos_diccionario = [
                    'Descripcion', 'Estado', 'Comprador', 'CodigoTipo',
                    'TipoConvocatoria', 'MontoEstimado', 'Modalidad'
                ]
                
                campos_encontrados = [c for c in campos_diccionario if c in data.keys()]
                if campos_encontrados:
                    print(f"   🎯 Campos del diccionario: {campos_encontrados}")
                    
                    # Mostrar muestra de datos
                    for campo in campos_encontrados[:3]:
                        valor = data.get(campo)
                        if isinstance(valor, (dict, list)):
                            print(f"      {campo}: {type(valor)} con {len(valor)} elementos")
                        else:
                            valor_str = str(valor)[:50] + "..." if len(str(valor)) > 50 else str(valor)
                            print(f"      {campo}: {valor_str}")
                
            elif isinstance(data, list):
                print(f"   Lista con {len(data)} elementos")
                if data:
                    print(f"   Primer elemento: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
            else:
                print(f"   Tipo de respuesta: {type(data)}")
                
        except FileNotFoundError:
            print(f"❌ {archivo}: No encontrado")
        except Exception as e:
            print(f"❌ {archivo}: Error - {e}")

def crear_solicitud_correcta():
    """Crea una función para hacer solicitudes con la estructura correcta"""
    
    print(f"\n🔧 CREANDO FUNCIÓN DE SOLICITUD CORRECTA")
    print("-" * 50)
    
    codigo_funcion = '''
def solicitar_licitaciones_correcto(tipo_licitacion="LE", estado="activas", ticket=None):
    """
    Solicita licitaciones usando la estructura correcta de la API
    
    Args:
        tipo_licitacion: Tipo según documentación (L1, LE, LP, LQ, LR, E2, CO, B2, H2, I2, LS)
        estado: Estado de las licitaciones (activas, publicadas, cerradas, adjudicadas)
        ticket: API key de Mercado Público
    
    Returns:
        dict: Respuesta de la API con estructura completa
    """
    
    if not ticket:
        ticket = os.environ.get("MERCADO_PUBLICO_TICKET", "BB946777-2A2E-4685-B5F5-43B441772C27")
    
    base_url = "https://api.mercadopublico.cl/servicios/v1/publico"
    url = f"{base_url}/Licitaciones/Listado/Licitacion/{tipo_licitacion}"
    
    params = {
        'ticket': ticket,
        'estado': estado
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Solicitud exitosa para tipo {tipo_licitacion}")
        print(f"📊 Campos disponibles: {len(data.keys()) if isinstance(data, dict) else 'Lista'}")
        
        return data
        
    except requests.RequestException as e:
        print(f"❌ Error en solicitud: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None
'''
    
    with open('api_correcta.py', 'w', encoding='utf-8') as f:
        f.write('import requests\nimport os\n\n')
        f.write(codigo_funcion)
    
    print("✅ Función creada en: api_correcta.py")

def main():
    """Función principal"""
    
    try:
        probar_estructura_correcta()
        analizar_respuestas_correctas()
        crear_solicitud_correcta()
        
        print(f"\n🎯 RECOMENDACIONES")
        print("-" * 50)
        print(f"1. Usar la estructura correcta: /Licitaciones/Listado/Licitacion/<Tipo>")
        print(f"2. Especificar el tipo de licitación según documentación")
        print(f"3. Probar diferentes tipos para obtener más campos")
        print(f"4. Revisar respuestas para encontrar campos del diccionario")
        print(f"5. Actualizar el sistema ETL para usar estructura correcta")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

if __name__ == "__main__":
    main()

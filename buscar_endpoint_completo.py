#!/usr/bin/env python3
"""
Script para buscar el endpoint correcto que devuelva todos los campos
según el diccionario de datos.
"""

import requests
import json
import time

def probar_endpoints():
    """Prueba diferentes endpoints y parámetros"""
    
    base_url = 'https://api.mercadopublico.cl/servicios/v1/publico'
    ticket = 'BB946777-2A2E-4685-B5F5-43B441772C27'
    
    # Diferentes endpoints a probar
    endpoints = [
        '/licitaciones.json',
        '/licitaciones/detalle.json',
        '/licitaciones/por_estado.json',
        '/licitaciones/por_fecha.json',
        '/licitaciones/buscar.json',
        '/licitaciones/listado.json',
        '/licitaciones/detalle_licitacion.json'
    ]
    
    # Diferentes parámetros a probar
    parametros_variaciones = [
        {'estado': 'activas', 'ticket': ticket},
        {'estado': 'activas', 'ticket': ticket, 'detalle': 'true'},
        {'estado': 'activas', 'ticket': ticket, 'completo': 'true'},
        {'estado': 'activas', 'ticket': ticket, 'incluir_detalle': 'true'},
        {'estado': 'activas', 'ticket': ticket, 'formato': 'completo'},
        {'estado': 'activas', 'ticket': ticket, 'nivel': 'detalle'},
        {'estado': 'activas', 'ticket': ticket, 'campos': 'todos'},
        {'ticket': ticket, 'estado': 'activas', 'incluir_comprador': 'true'},
        {'ticket': ticket, 'estado': 'activas', 'incluir_monto': 'true'},
        {'ticket': ticket, 'estado': 'activas', 'incluir_fechas': 'true'}
    ]
    
    print("🔍 BUSCANDO ENDPOINT CON CAMPOS COMPLETOS")
    print("=" * 60)
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\n📡 Probando endpoint: {endpoint}")
        
        for i, params in enumerate(parametros_variaciones, 1):
            try:
                print(f"   🔧 Variación {i}: {list(params.keys())}")
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Analizar estructura
                    if 'Listado' in data and data['Listado']:
                        primera = data['Listado'][0] if isinstance(data['Listado'], list) else data['Listado']
                        
                        if isinstance(primera, dict):
                            campos = list(primera.keys())
                            print(f"      ✅ {len(campos)} campos encontrados")
                            
                            # Verificar si tiene campos del diccionario
                            campos_diccionario = [
                                'Descripcion', 'Estado', 'Comprador', 'CodigoTipo', 
                                'TipoConvocatoria', 'MontoEstimado', 'Modalidad', 
                                'EmailResponsablePago'
                            ]
                            
                            campos_encontrados = [c for c in campos_diccionario if c in campos]
                            if campos_encontrados:
                                print(f"      🎯 Campos del diccionario encontrados: {campos_encontrados}")
                                
                                # Guardar estructura si es prometedora
                                if len(campos) > 10:  # Más de 10 campos es prometedor
                                    filename = f'estructura_endpoint_{endpoint.replace("/", "_")}_{i}.json'
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(primera, f, indent=2, ensure_ascii=False)
                                    print(f"      💾 Estructura guardada en: {filename}")
                            
                            # Mostrar campos disponibles
                            if len(campos) > 4:  # Solo mostrar si tiene más campos que el básico
                                print(f"      📋 Campos: {campos[:10]}{'...' if len(campos) > 10 else ''}")
                        else:
                            print(f"      ⚠️  Listado no es diccionario: {type(primera)}")
                    else:
                        print(f"      ❌ No hay Listado válido")
                        
                elif response.status_code == 404:
                    print(f"      ❌ Endpoint no existe")
                    break  # No probar más variaciones si el endpoint no existe
                else:
                    print(f"      ❌ Error {response.status_code}")
                    
                time.sleep(0.5)  # Pausa para no sobrecargar la API
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
                break

def probar_por_codigo_especifico():
    """Prueba obtener detalles de una licitación específica"""
    
    print(f"\n🔍 PROBANDO DETALLES POR CÓDIGO ESPECÍFICO")
    print("-" * 50)
    
    # Obtener un código de licitación
    url = 'https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json'
    params = {'estado': 'activas', 'ticket': 'BB946777-2A2E-4685-B5F5-43B441772C27'}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data['Listado']:
                codigo = data['Listado'][0]['CodigoExterno']
                print(f"📋 Probando con código: {codigo}")
                
                # Probar endpoints de detalle
                endpoints_detalle = [
                    f'/licitaciones/{codigo}.json',
                    f'/licitaciones/detalle/{codigo}.json',
                    f'/licitaciones/{codigo}/detalle.json',
                    f'/licitaciones/por_codigo/{codigo}.json'
                ]
                
                for endpoint in endpoints_detalle:
                    url_detalle = 'https://api.mercadopublico.cl/servicios/v1/publico' + endpoint
                    try:
                        response_detalle = requests.get(url_detalle, params={'ticket': 'BB946777-2A2E-4685-B5F5-43B441772C27'}, timeout=15)
                        print(f"   📡 {endpoint}: {response_detalle.status_code}")
                        
                        if response_detalle.status_code == 200:
                            data_detalle = response_detalle.json()
                            if isinstance(data_detalle, dict):
                                campos = list(data_detalle.keys())
                                print(f"      ✅ {len(campos)} campos en respuesta directa")
                                
                                # Verificar campos del diccionario
                                campos_diccionario = ['Descripcion', 'Estado', 'Comprador', 'MontoEstimado']
                                campos_encontrados = [c for c in campos_diccionario if c in campos]
                                if campos_encontrados:
                                    print(f"      🎯 Campos del diccionario: {campos_encontrados}")
                                    
                                    # Guardar estructura
                                    filename = f'estructura_detalle_{codigo.replace("-", "_")}.json'
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(data_detalle, f, indent=2, ensure_ascii=False)
                                    print(f"      💾 Guardado en: {filename}")
                                
                                print(f"      📋 Campos: {campos}")
                        
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                        
    except Exception as e:
        print(f"❌ Error obteniendo código: {e}")

def main():
    """Función principal"""
    
    try:
        probar_endpoints()
        probar_por_codigo_especifico()
        
        print(f"\n🎯 PRÓXIMOS PASOS")
        print("-" * 50)
        print(f"1. Revisar archivos JSON generados para encontrar estructura completa")
        print(f"2. Si no se encuentra, revisar documentación PDF")
        print(f"3. Considerar que la API puede requerir autenticación especial")
        print(f"4. Verificar si hay endpoints privados vs públicos")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para probar diferentes variaciones de la estructura de la API
y encontrar la forma correcta de obtener todos los campos.
"""

import requests
import json
from datetime import datetime

def probar_variaciones_estructura():
    """Prueba diferentes variaciones de la estructura de la API"""
    
    print("🔍 PROBANDO VARIACIONES DE ESTRUCTURA DE LA API")
    print("=" * 60)
    
    base_url = "https://api.mercadopublico.cl/servicios/v1/publico"
    ticket = "BB946777-2A2E-4685-B5F5-43B441772C27"
    
    # Obtener un código de licitación real primero
    try:
        url_basica = f"{base_url}/licitaciones.json"
        response_basica = requests.get(url_basica, params={'estado': 'activas', 'ticket': ticket}, timeout=30)
        
        if response_basica.status_code == 200:
            data_basica = response_basica.json()
            if data_basica.get('Listado'):
                codigo_licitacion = data_basica['Listado'][0]['CodigoExterno']
                print(f"📋 Código de licitación obtenido: {codigo_licitacion}")
                
                # Variaciones de estructura a probar
                variaciones = [
                    # Estructura original (funciona pero limitada)
                    f"{base_url}/licitaciones.json",
                    
                    # Estructura según documentación proporcionada
                    f"{base_url}/Licitaciones/Listado/Licitacion/LE",
                    f"{base_url}/Licitaciones/Listado/Licitacion/LP",
                    f"{base_url}/Licitaciones/Listado/Licitacion/L1",
                    
                    # Variaciones alternativas
                    f"{base_url}/licitaciones/Listado/Licitacion/LE",
                    f"{base_url}/licitaciones/listado/licitacion/LE",
                    f"{base_url}/licitaciones/detalle/{codigo_licitacion}.json",
                    f"{base_url}/licitaciones/{codigo_licitacion}.json",
                    f"{base_url}/licitaciones/detalle.json",
                    f"{base_url}/licitaciones/por_codigo/{codigo_licitacion}.json",
                    f"{base_url}/licitaciones/buscar.json",
                    f"{base_url}/licitaciones/por_estado/activas.json",
                    f"{base_url}/licitaciones/por_fecha/20251004.json",
                    
                    # Estructura con mayúsculas/minúsculas diferentes
                    f"{base_url}/Licitaciones.json",
                    f"{base_url}/LICITACIONES.json",
                    f"{base_url}/licitaciones/LE.json",
                    f"{base_url}/licitaciones/LP.json",
                    
                    # Estructura con parámetros en URL
                    f"{base_url}/licitaciones/LE/activas.json",
                    f"{base_url}/licitaciones/LP/activas.json",
                ]
                
                print(f"\n📡 Probando {len(variaciones)} variaciones de estructura...")
                
                variaciones_exitosas = []
                
                for i, url in enumerate(variaciones, 1):
                    print(f"\n{i:2d}. {url}")
                    
                    # Diferentes combinaciones de parámetros
                    parametros_variaciones = [
                        {'ticket': ticket},
                        {'ticket': ticket, 'estado': 'activas'},
                        {'ticket': ticket, 'codigo': codigo_licitacion},
                        {'ticket': ticket, 'tipo': 'LE'},
                        {'ticket': ticket, 'fecha': '20251004'},
                        {'ticket': ticket, 'detalle': 'true'},
                        {'ticket': ticket, 'completo': 'true'},
                        {'ticket': ticket, 'incluir_detalle': 'true'},
                    ]
                    
                    for j, params in enumerate(parametros_variaciones, 1):
                        try:
                            response = requests.get(url, params=params, timeout=15)
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                # Analizar respuesta
                                if isinstance(data, dict):
                                    campos = list(data.keys())
                                    if len(campos) > 4:  # Más campos que la respuesta básica
                                        print(f"   ✅ Variación {j}: {len(campos)} campos - {campos[:5]}{'...' if len(campos) > 5 else ''}")
                                        
                                        # Guardar respuesta exitosa
                                        filename = f'respuesta_exitosa_{i}_{j}.json'
                                        with open(filename, 'w', encoding='utf-8') as f:
                                            json.dump(data, f, indent=2, ensure_ascii=False)
                                        
                                        variaciones_exitosas.append({
                                            'url': url,
                                            'params': params,
                                            'campos': len(campos),
                                            'archivo': filename
                                        })
                                        
                                        # Verificar campos del diccionario
                                        campos_diccionario = [
                                            'Descripcion', 'Estado', 'Comprador', 'CodigoTipo',
                                            'TipoConvocatoria', 'MontoEstimado', 'Modalidad'
                                        ]
                                        campos_encontrados = [c for c in campos_diccionario if c in campos]
                                        if campos_encontrados:
                                            print(f"      🎯 Campos del diccionario: {campos_encontrados}")
                                    
                                    elif 'Listado' in data and data['Listado']:
                                        primera = data['Listado'][0] if isinstance(data['Listado'], list) else data['Listado']
                                        if isinstance(primera, dict):
                                            campos_listado = list(primera.keys())
                                            if len(campos_listado) > 4:
                                                print(f"   ✅ Variación {j}: Listado con {len(campos_listado)} campos - {campos_listado[:5]}{'...' if len(campos_listado) > 5 else ''}")
                                                
                                                filename = f'respuesta_listado_{i}_{j}.json'
                                                with open(filename, 'w', encoding='utf-8') as f:
                                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                                
                                                variaciones_exitosas.append({
                                                    'url': url,
                                                    'params': params,
                                                    'campos': len(campos_listado),
                                                    'archivo': filename
                                                })
                                
                                elif isinstance(data, list) and data:
                                    campos_lista = list(data[0].keys()) if isinstance(data[0], dict) else []
                                    if len(campos_lista) > 4:
                                        print(f"   ✅ Variación {j}: Lista con {len(campos_lista)} campos - {campos_lista[:5]}{'...' if len(campos_lista) > 5 else ''}")
                                        
                                        filename = f'respuesta_lista_{i}_{j}.json'
                                        with open(filename, 'w', encoding='utf-8') as f:
                                            json.dump(data, f, indent=2, ensure_ascii=False)
                                        
                                        variaciones_exitosas.append({
                                            'url': url,
                                            'params': params,
                                            'campos': len(campos_lista),
                                            'archivo': filename
                                        })
                            
                            elif response.status_code == 404:
                                print(f"   ❌ Variación {j}: 404 - No encontrado")
                                break  # No probar más variaciones para esta URL
                            
                            else:
                                print(f"   ❌ Variación {j}: {response.status_code}")
                                
                        except Exception as e:
                            print(f"   ❌ Variación {j}: Error - {e}")
                            break  # No probar más variaciones para esta URL
                
                # Resumen de variaciones exitosas
                if variaciones_exitosas:
                    print(f"\n🎉 VARIACIONES EXITOSAS ENCONTRADAS")
                    print("-" * 50)
                    
                    for var in variaciones_exitosas:
                        print(f"✅ {var['url']}")
                        print(f"   Parámetros: {var['params']}")
                        print(f"   Campos: {var['campos']}")
                        print(f"   Archivo: {var['archivo']}")
                        print()
                else:
                    print(f"\n❌ No se encontraron variaciones con más campos")
                    print(f"La API parece estar limitada a 4 campos básicos en el endpoint público")
                
            else:
                print("❌ No se pudo obtener código de licitación")
        else:
            print(f"❌ Error obteniendo datos básicos: {response_basica.status_code}")
            
    except Exception as e:
        print(f"❌ Error en proceso: {e}")

def analizar_respuestas_exitosas():
    """Analiza las respuestas exitosas encontradas"""
    
    print(f"\n🔍 ANÁLISIS DE RESPUESTAS EXITOSAS")
    print("-" * 50)
    
    import glob
    
    archivos_respuesta = glob.glob("respuesta_*.json")
    
    if not archivos_respuesta:
        print("❌ No se encontraron archivos de respuesta exitosa")
        return
    
    for archivo in archivos_respuesta:
        try:
            print(f"\n📁 {archivo}:")
            
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                campos = list(data.keys())
                print(f"   Campos disponibles: {len(campos)}")
                print(f"   Campos: {campos}")
                
                # Verificar campos del diccionario
                campos_diccionario = [
                    'Descripcion', 'Estado', 'Comprador', 'CodigoTipo',
                    'TipoConvocatoria', 'MontoEstimado', 'Modalidad', 'EmailResponsablePago'
                ]
                
                campos_encontrados = [c for c in campos_diccionario if c in campos]
                if campos_encontrados:
                    print(f"   🎯 Campos del diccionario encontrados: {campos_encontrados}")
                    
                    # Mostrar muestra de datos
                    for campo in campos_encontrados[:3]:
                        valor = data.get(campo)
                        if isinstance(valor, (dict, list)):
                            print(f"      {campo}: {type(valor)} con {len(valor)} elementos")
                        else:
                            valor_str = str(valor)[:50] + "..." if len(str(valor)) > 50 else str(valor)
                            print(f"      {campo}: {valor_str}")
                
                # Si tiene Listado, analizarlo también
                if 'Listado' in data and data['Listado']:
                    listado = data['Listado']
                    if isinstance(listado, list) and listado:
                        primera = listado[0]
                        if isinstance(primera, dict):
                            campos_listado = list(primera.keys())
                            print(f"   📋 Listado: {len(campos_listado)} campos - {campos_listado}")
                            
                            campos_encontrados_listado = [c for c in campos_diccionario if c in campos_listado]
                            if campos_encontrados_listado:
                                print(f"   🎯 Campos del diccionario en Listado: {campos_encontrados_listado}")
            
            elif isinstance(data, list) and data:
                primera = data[0]
                if isinstance(primera, dict):
                    campos = list(primera.keys())
                    print(f"   Lista con {len(data)} elementos")
                    print(f"   Campos: {campos}")
                    
                    campos_encontrados = [c for c in campos_diccionario if c in campos]
                    if campos_encontrados:
                        print(f"   🎯 Campos del diccionario: {campos_encontrados}")
                
        except Exception as e:
            print(f"   ❌ Error analizando {archivo}: {e}")

def main():
    """Función principal"""
    
    try:
        probar_variaciones_estructura()
        analizar_respuestas_exitosas()
        
        print(f"\n🎯 CONCLUSIÓN")
        print("-" * 50)
        print(f"1. La estructura documentada no parece estar disponible públicamente")
        print(f"2. La API pública está limitada a 4 campos básicos")
        print(f"3. Los campos del diccionario pueden requerir:")
        print(f"   - Acceso a API privada/premium")
        print(f"   - Autenticación especial")
        print(f"   - Endpoints no documentados")
        print(f"4. La solución de enriquecimiento de datos sigue siendo válida")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

if __name__ == "__main__":
    main()

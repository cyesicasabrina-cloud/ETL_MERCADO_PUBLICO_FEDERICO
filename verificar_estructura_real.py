#!/usr/bin/env python3
"""
Script para verificar la estructura real de la API
"""

import requests
import json

def verificar_estructura():
    url = 'https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json'
    params = {
        'estado': 'activas',
        'ticket': 'BB946777-2A2E-4685-B5F5-43B441772C27'
    }

    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    print('ESTRUCTURA REAL DE LA API:')
    print('=' * 40)
    print(f'Claves principales: {list(data.keys())}')
    print(f'Tipo de Listado: {type(data["Listado"])}')
    print(f'Elementos en Listado: {len(data["Listado"])}')

    if data['Listado']:
        primera = data['Listado'][0]
        print(f'\nCampos en primera licitación: {len(primera.keys())}')
        print('Campos disponibles:')
        for key in primera.keys():
            valor = primera[key]
            tipo = type(valor).__name__
            if isinstance(valor, (dict, list)):
                print(f'  - {key} ({tipo}) - {len(valor) if hasattr(valor, "__len__") else "N/A"} elementos')
            else:
                valor_str = str(valor)[:50] + "..." if len(str(valor)) > 50 else str(valor)
                print(f'  - {key} ({tipo}): {valor_str}')
        
        # Guardar estructura completa
        with open('estructura_real.json', 'w', encoding='utf-8') as f:
            json.dump(primera, f, indent=2, ensure_ascii=False)
        print(f'\nEstructura guardada en: estructura_real.json')

if __name__ == "__main__":
    verificar_estructura()

import requests
import os


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

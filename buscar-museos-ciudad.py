#!/usr/bin/env python3
import os
import argparse
import requests
import time
import random
import csv
import json
from urllib.parse import quote

# ---------------- CONFIGURACIÓN POR DEFECTO ----------------
DEFAULT_API_KEY_FILE = 'google_api_key.txt'
DEFAULT_OUTPUT_DIR = 'datos_museos'
DEFAULT_DELAY_BETWEEN_CALLS = (1.0, 2.0)
DEFAULT_RADIUS = 25000  # 25km radio de búsqueda
URL_TEXT_SEARCH = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
URL_PLACE_DETAILS = 'https://maps.googleapis.com/maps/api/place/details/json'
# -----------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Busca museos en una ciudad española y extrae información detallada.'
    )
    parser.add_argument(
        'ciudad', 
        help='Nombre de la ciudad española donde buscar museos'
    )
    parser.add_argument(
        '--api-key-file', default=DEFAULT_API_KEY_FILE,
        help='Archivo con la clave de API de Google Places'
    )
    parser.add_argument(
        '--output-dir', default=DEFAULT_OUTPUT_DIR,
        help='Directorio donde se guardarán los datos'
    )
    parser.add_argument(
        '--formato', choices=['csv', 'json', 'ambos'], default='csv',
        help='Formato de salida de los datos'
    )
    parser.add_argument(
        '--min-delay', type=float, default=DEFAULT_DELAY_BETWEEN_CALLS[0],
        help='Delay mínimo entre peticiones (segundos)'
    )
    parser.add_argument(
        '--max-delay', type=float, default=DEFAULT_DELAY_BETWEEN_CALLS[1],
        help='Delay máximo entre peticiones (segundos)'
    )
    parser.add_argument(
        '--radio', type=int, default=DEFAULT_RADIUS,
        help='Radio de búsqueda en metros desde el centro de la ciudad'
    )
    return parser.parse_args()


def load_api_key(filepath):
    if not os.path.isfile(filepath):
        raise RuntimeError(f"No se encontró el archivo de API key: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        key = f.read().strip()
    if not key:
        raise RuntimeError(f"El archivo {filepath} está vacío.")
    return key


def get_city_coordinates(ciudad, api_key):
    """Obtiene las coordenadas del centro de la ciudad"""
    query = f"{ciudad}, España"
    params = {
        'query': query,
        'key': api_key,
        'fields': 'geometry'
    }
    
    try:
        resp = requests.get(URL_TEXT_SEARCH, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get('results', [])
        
        if results:
            location = results[0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            raise RuntimeError(f"No se pudo encontrar la ciudad: {ciudad}")
            
    except requests.RequestException as e:
        raise RuntimeError(f"Error obteniendo coordenadas de {ciudad}: {e}")


def search_museums_by_text(ciudad, api_key):
    """Busca museos usando búsqueda por texto directamente"""
    queries = [
        f"museos en {ciudad} España",
        f"museum {ciudad} Spain",
        f"museo {ciudad}"
    ]
    
    all_museums = []
    seen_place_ids = set()
    
    for query in queries:
        print(f"   🔍 Consultando: {query}")
        params = {
            'query': query,
            'key': api_key
        }
        
        try:
            resp = requests.get(URL_TEXT_SEARCH, params=params, timeout=15)
            print(f"   📊 Status: {resp.status_code}")
            
            if resp.status_code != 200:
                print(f"   ❌ Error HTTP: {resp.text[:200]}")
                continue
                
            data = resp.json()
            
            # Debug: mostrar status de la API
            status = data.get('status', 'UNKNOWN')
            print(f"   📈 API Status: {status}")
            
            if status == 'REQUEST_DENIED':
                print(f"   ❌ Solicitud denegada: {data.get('error_message', 'Sin mensaje')}")
                continue
            elif status == 'INVALID_REQUEST':
                print(f"   ❌ Solicitud inválida: {data.get('error_message', 'Sin mensaje')}")
                continue
            
            results = data.get('results', [])
            print(f"   📍 Resultados encontrados: {len(results)}")
            
            for result in results:
                place_id = result.get('place_id')
                name = result.get('name', 'Sin nombre')
                address = result.get('formatted_address', '').lower()
                
                if place_id and place_id not in seen_place_ids:
                    # Filtrar por ciudad en la dirección o nombre
                    if ciudad.lower() in address or ciudad.lower() in name.lower():
                        all_museums.append(result)
                        seen_place_ids.add(place_id)
                        print(f"     ✅ Añadido: {name}")
                        
        except requests.RequestException as e:
            print(f"   ⚠️ Error en búsqueda: {query} - {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Error JSON: {e}")
            continue
            
        # Delay entre consultas diferentes
        time.sleep(1)
    
    return all_museums


def search_museums_in_city(lat, lng, radius, api_key):
    """Busca museos en un radio específico desde las coordenadas de la ciudad"""
    params = {
        'location': f"{lat},{lng}",
        'radius': radius,
        'type': 'museum',
        'key': api_key
    }
    
    all_museums = []
    next_page_token = None
    
    while True:
        if next_page_token:
            params['pagetoken'] = next_page_token
        
        try:
            resp = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', 
                              params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get('results', [])
            all_museums.extend(results)
            
            next_page_token = data.get('next_page_token')
            if not next_page_token:
                break
                
            # Delay obligatorio para next_page_token
            time.sleep(2)
            
        except requests.RequestException as e:
            print(f"⚠️ Error en búsqueda de museos: {e}")
            break
    
    return all_museums


def get_place_details(place_id, api_key):
    """Obtiene detalles completos de un lugar específico"""
    fields = [
        'name', 'formatted_address', 'address_components', 'international_phone_number',
        'website', 'rating', 'user_ratings_total', 'opening_hours',
        'geometry', 'types', 'url', 'vicinity'
    ]
    
    params = {
        'place_id': place_id,
        'fields': ','.join(fields),
        'key': api_key,
        'language': 'es'
    }
    
    try:
        resp = requests.get(URL_PLACE_DETAILS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get('result', {})
    except requests.RequestException as e:
        print(f"⚠️ Error obteniendo detalles del lugar {place_id}: {e}")
        return {}


def extract_email_from_website(website_url):
    """Intenta extraer email de la página web (simplificado)"""
    # Esta función podría expandirse para hacer scraping de la web
    # Por ahora retorna None ya que Google Places API no proporciona emails
    return None


def extract_street_info(address_components):
    """Extrae información de calle y número de los componentes de dirección"""
    street_number = None
    street_name = None
    
    if not address_components:
        return None, None
    
    for component in address_components:
        types = component.get('types', [])
        
        if 'street_number' in types:
            street_number = component.get('long_name')
        elif 'route' in types:
            street_name = component.get('long_name')
    
    # Combinar calle y número si ambos están disponibles
    if street_name and street_number:
        return f"{street_name}, {street_number}"
    elif street_name:
        return street_name
    elif street_number:
        return street_number
    else:
        return None


def process_museum_data(museo_raw, detalles, ciudad):
    """Procesa y estructura los datos del museo"""
    # Extraer información de calle
    address_components = detalles.get('address_components', [])
    calle = extract_street_info(address_components)
    
    direccion_completa = detalles.get('formatted_address', museo_raw.get('vicinity', 'N/A'))
    
    museo_data = {
        'nombre': detalles.get('name', museo_raw.get('name', 'N/A')),
        'ciudad': ciudad,
        'direccion_completa': direccion_completa,
        'calle': calle if calle else 'N/A',
        'telefono': detalles.get('international_phone_number', 'N/A'),
        'email': 'N/A',  # Google Places API no proporciona emails
        'pagina_web': detalles.get('website', 'N/A'),
        'valoracion': detalles.get('rating', museo_raw.get('rating', 'N/A')),
        'num_valoraciones': detalles.get('user_ratings_total', 
                                       museo_raw.get('user_ratings_total', 'N/A')),
        'google_maps_url': detalles.get('url', 'N/A'),
        'tipos': ', '.join(detalles.get('types', museo_raw.get('types', []))),
        'estado': 'Abierto' if museo_raw.get('business_status') == 'OPERATIONAL' else 'Desconocido'
    }
    
    # Intentar extraer horarios
    horarios = detalles.get('opening_hours', {})
    if horarios:
        museo_data['horarios'] = '; '.join(horarios.get('weekday_text', []))
    else:
        museo_data['horarios'] = 'N/A'
    
    return museo_data


def save_to_csv(museos_data, filepath):
    """Guarda los datos en formato CSV"""
    if not museos_data:
        return
        
    fieldnames = [
        'nombre', 'ciudad', 'direccion_completa', 'calle', 'telefono', 'email', 'pagina_web',
        'valoracion', 'num_valoraciones', 'horarios', 'google_maps_url',
        'tipos', 'estado'
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(museos_data)


def save_to_json(museos_data, filepath):
    """Guarda los datos en formato JSON"""
    with open(filepath, 'w', encoding='utf-8') as jsonfile:
        json.dump(museos_data, jsonfile, ensure_ascii=False, indent=2)


def main():
    args = parse_args()
    api_key = load_api_key(args.api_key_file)
    ciudad = args.ciudad
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"🏛️ BUSCADOR DE MUSEOS - {ciudad.upper()}")
    print("✅ API OK: clave cargada correctamente.")
    print(f"🔍 Buscando museos en {ciudad}...")
    
    # Intentar primero con coordenadas, si falla usar búsqueda por texto
    try:
        lat, lng = get_city_coordinates(ciudad, api_key)
        print(f"📍 Coordenadas: {lat:.4f}, {lng:.4f}")
        print(f"🔍 Buscando en radio de {args.radio/1000:.1f}km...")
        museos_encontrados = search_museums_in_city(lat, lng, args.radio, api_key)
    except Exception as e:
        print(f"⚠️ No se pudieron obtener coordenadas: {e}")
        print(f"🔍 Usando búsqueda por texto directo...")
        museos_encontrados = search_museums_by_text(ciudad, api_key)
    
    if not museos_encontrados:
        print("❌ No se encontraron museos en la ciudad especificada.")
        return
    
    print(f"🎯 Encontrados {len(museos_encontrados)} museos")
    print("📋 Obteniendo información detallada...")
    
    museos_data = []
    
    for i, museo in enumerate(museos_encontrados, 1):
        place_id = museo.get('place_id')
        nombre = museo.get('name', 'Desconocido')
        
        print(f"   {i:2d}/{len(museos_encontrados)} - {nombre}")
        
        # Obtener detalles completos
        detalles = get_place_details(place_id, api_key)
        
        # Procesar datos
        museo_procesado = process_museum_data(museo, detalles, ciudad)
        museos_data.append(museo_procesado)
        
        # Delay entre peticiones
        time.sleep(random.uniform(args.min_delay, args.max_delay))
    
    # Guardar resultados
    ciudad_safe = ciudad.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    
    if args.formato in ['csv', 'ambos']:
        csv_path = os.path.join(args.output_dir, f"museos_{ciudad_safe}.csv")
        save_to_csv(museos_data, csv_path)
        print(f"✅ Datos guardados en CSV: {csv_path}")
    
    if args.formato in ['json', 'ambos']:
        json_path = os.path.join(args.output_dir, f"museos_{ciudad_safe}.json")
        save_to_json(museos_data, json_path)
        print(f"✅ Datos guardados en JSON: {json_path}")
    
    print("\n📊 RESUMEN:")
    print(f"   • Ciudad: {ciudad}")
    print(f"   • Museos encontrados: {len(museos_data)}")
    print(f"   • Con teléfono: {sum(1 for m in museos_data if m['telefono'] != 'N/A')}")
    print(f"   • Con página web: {sum(1 for m in museos_data if m['pagina_web'] != 'N/A')}")
    print(f"   • Con valoraciones: {sum(1 for m in museos_data if m['valoracion'] != 'N/A')}")
    
    print("\n🔝 TOP 3 MUSEOS MEJOR VALORADOS:")
    museos_valorados = [m for m in museos_data if m['valoracion'] != 'N/A']
    museos_valorados.sort(key=lambda x: float(x['valoracion']), reverse=True)
    
    for i, museo in enumerate(museos_valorados[:3], 1):
        print(f"   {i}. {museo['nombre']} - ⭐ {museo['valoracion']} ({museo['num_valoraciones']} reseñas)")
    
    print("\n🏁 ¡BÚSQUEDA COMPLETADA!")


if __name__ == '__main__':
    main()
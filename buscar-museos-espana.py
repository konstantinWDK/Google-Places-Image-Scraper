#!/usr/bin/env python3
import os
import argparse
import requests
import time
import random
import csv
import json
import re
from urllib.parse import quote

# ---------------- CONFIGURACIÓN POR DEFECTO ----------------
DEFAULT_API_KEY_FILE = 'google_api_key.txt'
DEFAULT_OUTPUT_DIR = 'datos_museos'
DEFAULT_DELAY_BETWEEN_CALLS = (2.0, 4.0)
DEFAULT_BATCH_DELAY = (10.0, 20.0)
URL_TEXT_SEARCH = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
URL_PLACE_DETAILS = 'https://maps.googleapis.com/maps/api/place/details/json'

# Principales ciudades y provincias de España para búsqueda sistemática
CIUDADES_ESPANA = [
    "Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza", "Málaga", "Murcia", "Palma de Mallorca",
    "Las Palmas de Gran Canaria", "Bilbao", "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón",
    "Granada", "A Coruña", "Vitoria-Gasteiz", "Elche", "Oviedo", "Santa Cruz de Tenerife", "Badalona",
    "Cartagena", "Terrassa", "Jerez de la Frontera", "Sabadell", "Móstoles", "Alcalá de Henares",
    "Pamplona", "Fuenlabrada", "Almería", "Leganés", "Donostia-San Sebastián", "Burgos", "Santander",
    "Castellón de la Plana", "Getafe", "Albacete", "Alcorcón", "Logroño", "Badajoz", "Salamanca",
    "Huelva", "Marbella", "Lleida", "Tarragona", "León", "Dos Hermanas", "Torrejón de Ardoz",
    "Parla", "Mataró", "Cádiz", "Santa Coloma de Gramenet", "Algeciras", "Jaén", "Alcobendas",
    "Ourense", "Reus", "Telde", "Barakaldo", "Lugo", "Santiago de Compostela", "Cáceres", "Lorca",
    "Coslada", "Talavera de la Reina", "El Puerto de Santa María", "Cornellà de Llobregat",
    "Avilés", "Palencia", "Galdakao", "Molina de Segura", "Guadalajara", "Melilla", "Ceuta"
]

PROVINCIAS_ESPANA = [
    "Álava", "Albacete", "Alicante", "Almería", "Asturias", "Ávila", "Badajoz", "Barcelona",
    "Burgos", "Cáceres", "Cádiz", "Cantabria", "Castellón", "Ciudad Real", "Córdoba", "A Coruña",
    "Cuenca", "Girona", "Granada", "Guadalajara", "Gipuzkoa", "Huelva", "Huesca", "Jaén",
    "León", "Lleida", "Lugo", "Madrid", "Málaga", "Murcia", "Navarra", "Ourense", "Palencia",
    "Las Palmas", "Pontevedra", "La Rioja", "Salamanca", "Segovia", "Sevilla", "Soria",
    "Tarragona", "Teruel", "Toledo", "Valencia", "Valladolid", "Bizkaia", "Zamora", "Zaragoza"
]
# -----------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Extrae TODOS los museos de España con información detallada.'
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
        '--modo', choices=['ciudades', 'provincias', 'ambos'], default='ciudades',
        help='Modo de búsqueda: por ciudades principales, provincias o ambos'
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
        '--batch-delay-min', type=float, default=DEFAULT_BATCH_DELAY[0],
        help='Delay mínimo entre ciudades (segundos)'
    )
    parser.add_argument(
        '--batch-delay-max', type=float, default=DEFAULT_BATCH_DELAY[1],
        help='Delay máximo entre ciudades (segundos)'
    )
    parser.add_argument(
        '--limite-por-ciudad', type=int, default=50,
        help='Límite máximo de museos por ciudad'
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


def parse_spanish_address(formatted_address):
    """Parsea una dirección española en calle, ciudad y código postal"""
    if not formatted_address:
        return "N/A", "N/A", "N/A"
    
    # Patrón para direcciones españolas: buscar código postal (5 dígitos)
    cp_pattern = r'\b(\d{5})\b'
    cp_match = re.search(cp_pattern, formatted_address)
    codigo_postal = cp_match.group(1) if cp_match else "N/A"
    
    # Dividir por comas
    partes = [p.strip() for p in formatted_address.split(',')]
    
    if len(partes) >= 3:
        # Formato típico: "Calle, CP Ciudad, Provincia/País"
        calle = partes[0]
        
        # Buscar la parte que contiene la ciudad (usualmente después del CP)
        ciudad = "N/A"
        for parte in partes[1:]:
            # Eliminar el código postal de la parte para obtener la ciudad
            ciudad_limpia = re.sub(r'\b\d{5}\b', '', parte).strip()
            if ciudad_limpia and ciudad_limpia.lower() not in ['spain', 'españa']:
                ciudad = ciudad_limpia
                break
                
    elif len(partes) == 2:
        calle = partes[0]
        # Intentar extraer ciudad de la segunda parte
        ciudad_con_cp = partes[1]
        ciudad = re.sub(r'\b\d{5}\b', '', ciudad_con_cp).strip()
        if not ciudad or ciudad.lower() in ['spain', 'españa']:
            ciudad = "N/A"
    else:
        calle = formatted_address
        ciudad = "N/A"
    
    return calle, ciudad, codigo_postal


def search_museums_in_location(location, api_key, limite=50):
    """Busca museos en una ubicación específica"""
    queries = [
        f"museos en {location} España",
        f"museum {location} Spain",
        f"museo arte {location}",
        f"centro cultural {location}",
        f"fundación museo {location}"
    ]
    
    all_museums = []
    seen_place_ids = set()
    
    for query in queries:
        print(f"      🔍 Consultando: {query}")
        params = {
            'query': query,
            'key': api_key,
            'language': 'es',
            'region': 'es'
        }
        
        try:
            resp = requests.get(URL_TEXT_SEARCH, params=params, timeout=15)
            
            if resp.status_code != 200:
                print(f"      ❌ Error HTTP {resp.status_code}")
                continue
                
            data = resp.json()
            status = data.get('status', 'UNKNOWN')
            
            if status == 'REQUEST_DENIED':
                print(f"      ❌ API: {data.get('error_message', 'Sin mensaje')}")
                return []
            elif status not in ['OK', 'ZERO_RESULTS']:
                print(f"      ⚠️ API Status: {status}")
                continue
            
            results = data.get('results', [])
            print(f"      📍 Resultados: {len(results)}")
            
            for result in results:
                place_id = result.get('place_id')
                name = result.get('name', 'Sin nombre')
                address = result.get('formatted_address', '').lower()
                types = result.get('types', [])
                
                # Filtros para asegurar que es realmente un museo
                museum_types = ['museum', 'art_gallery', 'tourist_attraction', 'cultural_center']
                is_museum = any(t in types for t in museum_types)
                
                # Palabras clave que indican museo
                museum_keywords = ['museo', 'museum', 'fundación', 'centro cultural', 'galería', 'arte']
                has_museum_keyword = any(keyword in name.lower() for keyword in museum_keywords)
                
                if place_id and place_id not in seen_place_ids and (is_museum or has_museum_keyword):
                    # Verificar que está en España
                    if 'españa' in address or 'spain' in address or location.lower() in address:
                        all_museums.append(result)
                        seen_place_ids.add(place_id)
                        print(f"        ✅ Añadido: {name}")
                        
                        if len(all_museums) >= limite:
                            print(f"        🛑 Límite alcanzado ({limite})")
                            return all_museums
                        
        except Exception as e:
            print(f"      ⚠️ Error: {e}")
            continue
            
        # Delay entre queries
        time.sleep(random.uniform(1, 2))
    
    return all_museums


def get_place_details(place_id, api_key):
    """Obtiene detalles completos de un lugar específico"""
    fields = [
        'name', 'formatted_address', 'international_phone_number',
        'website', 'opening_hours', 'types', 'url'
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
    except Exception as e:
        print(f"      ⚠️ Error detalles {place_id}: {e}")
        return {}


def process_museum_data(museo_raw, detalles):
    """Procesa y estructura los datos del museo"""
    nombre = detalles.get('name', museo_raw.get('name', 'N/A'))
    direccion_completa = detalles.get('formatted_address', museo_raw.get('formatted_address', 'N/A'))
    
    # Parsear dirección española
    calle, ciudad, codigo_postal = parse_spanish_address(direccion_completa)
    
    museo_data = {
        'nombre': nombre,
        'calle': calle,
        'ciudad': ciudad,
        'codigo_postal': codigo_postal,
        'telefono': detalles.get('international_phone_number', 'N/A'),
        'email': 'N/A',  # Google Places API no proporciona emails
        'pagina_web': detalles.get('website', 'N/A'),
        'tipos': ', '.join(detalles.get('types', museo_raw.get('types', []))),
        'direccion_completa': direccion_completa
    }
    
    # Procesar horarios
    horarios = detalles.get('opening_hours', {})
    if horarios and 'weekday_text' in horarios:
        museo_data['horarios'] = '; '.join(horarios['weekday_text'])
    else:
        museo_data['horarios'] = 'N/A'
    
    return museo_data


def save_to_csv(museos_data, filepath):
    """Guarda los datos en formato CSV"""
    if not museos_data:
        return
        
    fieldnames = [
        'nombre', 'calle', 'ciudad', 'codigo_postal', 'telefono', 'email', 
        'pagina_web', 'horarios', 'tipos', 'direccion_completa'
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(museos_data)


def main():
    args = parse_args()
    api_key = load_api_key(args.api_key_file)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("🏛️ EXTRACTOR DE MUSEOS DE ESPAÑA")
    print("✅ API OK: clave cargada correctamente.")
    print(f"📂 Directorio de salida: {args.output_dir}")
    print(f"🎯 Modo: {args.modo}")
    print(f"📊 Límite por ubicación: {args.limite_por_ciudad}\n")
    
    # Seleccionar ubicaciones según el modo
    ubicaciones = []
    if args.modo in ['ciudades', 'ambos']:
        ubicaciones.extend(CIUDADES_ESPANA)
    if args.modo in ['provincias', 'ambos']:
        ubicaciones.extend([f"provincia de {p}" for p in PROVINCIAS_ESPANA])
    
    # Eliminar duplicados manteniendo orden
    ubicaciones = list(dict.fromkeys(ubicaciones))
    
    print(f"🗺️ Procesando {len(ubicaciones)} ubicaciones...")
    
    todos_los_museos = []
    ubicaciones_procesadas = 0
    museos_encontrados_total = 0
    
    for i, ubicacion in enumerate(ubicaciones, 1):
        print(f"\n📍 {i}/{len(ubicaciones)} - Procesando: {ubicacion}")
        
        museos_ubicacion = search_museums_in_location(ubicacion, api_key, args.limite_por_ciudad)
        ubicaciones_procesadas += 1
        
        if not museos_ubicacion:
            print(f"   ❌ No se encontraron museos en {ubicacion}")
            continue
        
        print(f"   🎯 Obteniendo detalles de {len(museos_ubicacion)} museos...")
        
        for j, museo in enumerate(museos_ubicacion, 1):
            place_id = museo.get('place_id')
            nombre = museo.get('name', 'Desconocido')
            
            print(f"     {j:2d}/{len(museos_ubicacion)} - {nombre}")
            
            # Obtener detalles completos
            detalles = get_place_details(place_id, api_key)
            
            # Procesar datos
            museo_procesado = process_museum_data(museo, detalles)
            todos_los_museos.append(museo_procesado)
            museos_encontrados_total += 1
            
            # Delay entre peticiones de detalles
            time.sleep(random.uniform(args.min_delay, args.max_delay))
        
        # Delay entre ubicaciones
        if i < len(ubicaciones):
            delay_ubicacion = random.uniform(args.batch_delay_min, args.batch_delay_max)
            print(f"   ⏳ Esperando {delay_ubicacion:.1f}s antes de la siguiente ubicación...")
            time.sleep(delay_ubicacion)
    
    # Eliminar duplicados por nombre y dirección
    print(f"\n🔄 Eliminando duplicados...")
    museos_unicos = []
    seen_combinations = set()
    
    for museo in todos_los_museos:
        key = (museo['nombre'].lower(), museo['ciudad'].lower(), museo['calle'].lower())
        if key not in seen_combinations:
            museos_unicos.append(museo)
            seen_combinations.add(key)
    
    duplicados_eliminados = len(todos_los_museos) - len(museos_unicos)
    print(f"   🗑️ Eliminados {duplicados_eliminados} duplicados")
    
    # Guardar resultados
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(args.output_dir, f"museos_espana_{timestamp}.csv")
    save_to_csv(museos_unicos, csv_path)
    
    print(f"\n✅ Datos guardados en: {csv_path}")
    
    # Estadísticas finales
    print(f"\n📊 ESTADÍSTICAS FINALES:")
    print(f"   • Ubicaciones procesadas: {ubicaciones_procesadas}/{len(ubicaciones)}")
    print(f"   • Museos encontrados (total): {museos_encontrados_total}")
    print(f"   • Museos únicos: {len(museos_unicos)}")
    print(f"   • Con teléfono: {sum(1 for m in museos_unicos if m['telefono'] != 'N/A')}")
    print(f"   • Con página web: {sum(1 for m in museos_unicos if m['pagina_web'] != 'N/A')}")
    print(f"   • Con código postal: {sum(1 for m in museos_unicos if m['codigo_postal'] != 'N/A')}")
    
    # Top ciudades con más museos
    ciudades_count = {}
    for museo in museos_unicos:
        ciudad = museo['ciudad']
        if ciudad != 'N/A':
            ciudades_count[ciudad] = ciudades_count.get(ciudad, 0) + 1
    
    if ciudades_count:
        print(f"\n🏆 TOP 10 CIUDADES CON MÁS MUSEOS:")
        top_ciudades = sorted(ciudades_count.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (ciudad, count) in enumerate(top_ciudades, 1):
            print(f"   {i:2d}. {ciudad}: {count} museos")
    
    print(f"\n🏁 ¡EXTRACCIÓN COMPLETADA!")
    print(f"📁 Archivo generado: {csv_path}")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
import os
import argparse
import requests
import time
import random
import re
import unicodedata
from io import BytesIO
from PIL import Image

# ---------------- CONFIGURACIÓN POR DEFECTO ----------------
DEFAULT_API_KEY_FILE         = 'google_api_key.txt'
DEFAULT_LIST_FILE            = 'museos-sitios.txt'
DEFAULT_OUTPUT_DIR           = 'imagenes_museos'
DEFAULT_MAX_PHOTOS_PER_PLACE = 3
DEFAULT_DELAY_BETWEEN_CALLS  = (1.0, 2.5)
DEFAULT_BATCH_SIZE           = 3
DEFAULT_BATCH_DELAY_RANGE    = (8.0, 15.0)
URL_TEXT_SEARCH              = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
URL_PLACE_PHOTO              = 'https://maps.googleapis.com/maps/api/place/photo'
# -----------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Descarga imágenes de museos desde Google Places con configuración optimizada.'
    )
    parser.add_argument(
        '--api-key-file', default=DEFAULT_API_KEY_FILE,
        help='Archivo con la clave de API de Google Places'
    )
    parser.add_argument(
        '--list-file', default=DEFAULT_LIST_FILE,
        help='Archivo con lista de museos a buscar (uno por línea)'
    )
    parser.add_argument(
        '--output-dir', default=DEFAULT_OUTPUT_DIR,
        help='Directorio donde se guardarán las imágenes de museos'
    )
    parser.add_argument(
        '--max-photos', type=int, default=DEFAULT_MAX_PHOTOS_PER_PLACE,
        help='Número máximo de fotos a descargar por museo'
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
        '--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
        help='Número de museos a procesar por lote'
    )
    parser.add_argument(
        '--batch-delay-min', type=float,
        default=DEFAULT_BATCH_DELAY_RANGE[0],
        help='Delay mínimo entre lotes (segundos)'
    )
    parser.add_argument(
        '--batch-delay-max', type=float,
        default=DEFAULT_BATCH_DELAY_RANGE[1],
        help='Delay máximo entre lotes (segundos)'
    )
    parser.add_argument(
        '--add-search-terms', action='store_true',
        help='Añadir términos "museo" o "museum" a la búsqueda automáticamente'
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


def load_museos_from_file(filepath):
    if not os.path.isfile(filepath):
        raise RuntimeError(f"No se encontró el archivo de lista: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def normalize_term(term):
    nfkd = unicodedata.normalize('NFD', term)
    no_diac = ''.join(c for c in nfkd if not unicodedata.combining(c))
    safe = re.sub(r'[^A-Za-z0-9]+', '_', no_diac).strip('_')
    return safe


def enhance_search_term(term, add_search_terms):
    """Mejora el término de búsqueda para museos"""
    if not add_search_terms:
        return term
    
    term_lower = term.lower()
    if 'museo' not in term_lower and 'museum' not in term_lower:
        # Detectar idioma probable y añadir término apropiado
        if any(word in term_lower for word in ['madrid', 'barcelona', 'sevilla', 'valencia', 'bilbao']):
            return f"{term} museo"
        else:
            return f"{term} museum"
    return term


def get_photo_references_by_title(title, api_key, max_photos):
    params = {
        'query': title,
        'key': api_key,
        'type': 'museum'  # Filtro específico para museos
    }
    try:
        resp = requests.get(URL_TEXT_SEARCH, params=params, timeout=15)
        resp.raise_for_status()
        results = resp.json().get('results', [])
    except requests.RequestException as e:
        print(f"⚠️ Error búsqueda '{title}': {e}")
        return []

    refs = []
    places_info = []
    
    for place in results:
        place_name = place.get('name', 'Desconocido')
        rating = place.get('rating', 'N/A')
        
        for photo in place.get('photos', []):
            ref = photo.get('photo_reference')
            if ref:
                refs.append(ref)
                places_info.append({
                    'name': place_name,
                    'rating': rating,
                    'ref': ref
                })
                if len(refs) >= max_photos:
                    break
        if len(refs) >= max_photos:
            break
    
    if places_info:
        print(f"📍 Encontrado: {places_info[0]['name']} (⭐ {places_info[0]['rating']})")
    
    return refs


def fetch_image_data(photo_ref, api_key, max_width=1600):
    """Descarga imagen con mayor resolución para museos"""
    params = {
        'photoreference': photo_ref, 
        'maxwidth': max_width, 
        'key': api_key
    }
    try:
        r = requests.get(URL_PLACE_PHOTO, params=params, timeout=20)
        r.raise_for_status()
        return r.content
    except requests.RequestException as e:
        print(f"⚠️ Error descargando imagen: {e}")
        return None


def select_featured_museum(refs, api_key):
    """Selecciona la mejor imagen para museo basada en criterios específicos"""
    best_ref = None
    best_data = None
    best_score = 0
    
    for ref in refs:
        data = fetch_image_data(ref, api_key)
        if data:
            try:
                img = Image.open(BytesIO(data))
                w, h = img.size
                
                # Criterios de puntuación para museos
                score = 0
                
                # Preferir imágenes horizontales (fachadas, interiores amplios)
                if w >= h:
                    score += 2
                
                # Preferir resoluciones altas
                if w * h > 800000:  # > 800k píxeles
                    score += 3
                elif w * h > 400000:  # > 400k píxeles
                    score += 1
                
                # Evitar imágenes muy cuadradas (posibles logos)
                ratio = max(w, h) / min(w, h)
                if 1.2 <= ratio <= 2.5:
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_ref = ref
                    best_data = data
                    
            except Exception as e:
                print(f"⚠️ Error procesando imagen: {e}")
                continue
    
    # Fallback a la primera imagen si no se encontró una óptima
    if not best_data and refs:
        best_ref = refs[0]
        best_data = fetch_image_data(best_ref, api_key)
    
    return best_ref, best_data


def save_image(data, output_dir, filename):
    path = os.path.join(output_dir, filename)
    with open(path, 'wb') as f:
        f.write(data)
    
    # Información del archivo guardado
    size_kb = len(data) / 1024
    try:
        img = Image.open(BytesIO(data))
        w, h = img.size
        print(f"✅ Guardada: {filename} ({w}x{h}, {size_kb:.1f}KB)")
    except:
        print(f"✅ Guardada: {filename} ({size_kb:.1f}KB)")


def main():
    args = parse_args()
    api_key = load_api_key(args.api_key_file)
    museos = load_museos_from_file(args.list_file)
    os.makedirs(args.output_dir, exist_ok=True)

    print("🏛️ SCRAPER DE MUSEOS - Google Places API")
    print("✅ API OK: clave cargada correctamente.")
    print(f"📂 Directorio de salida: {args.output_dir}")
    print(f"🖼️ Máximo {args.max_photos} fotos por museo\n")
    
    total = len(museos)
    museos_procesados = 0
    museos_exitosos = 0
    
    for idx in range(0, total, args.batch_size):
        batch = museos[idx:idx + args.batch_size]
        lote_num = idx // args.batch_size + 1
        total_lotes = (total + args.batch_size - 1) // args.batch_size
        
        print(f"🔄 Procesando lote {lote_num}/{total_lotes}: {len(batch)} museos")

        for museo in batch:
            safe = normalize_term(museo)
            search_term = enhance_search_term(museo, args.add_search_terms)
            
            print(f"🏛️ Procesando: {museo}")
            if search_term != museo:
                print(f"   🔍 Búsqueda: {search_term}")

            refs = get_photo_references_by_title(search_term, api_key, args.max_photos)
            museos_procesados += 1
            
            if not refs:
                print(f"❌ No se encontraron fotos para '{museo}'\n")
                continue

            # Imagen destacada del museo
            featured_ref, featured_data = select_featured_museum(refs, api_key)
            if featured_data:
                save_image(featured_data, args.output_dir, f"{safe}-principal.jpg")
                museos_exitosos += 1

            # Resto de fotos del museo
            count = 1
            for ref in refs:
                if ref == featured_ref:
                    continue
                data = fetch_image_data(ref, api_key)
                if not data:
                    continue
                count += 1
                save_image(data, args.output_dir, f"{safe}-{count}.jpg")
                time.sleep(random.uniform(args.min_delay, args.max_delay))
            
            print()

        # Delay entre lotes si quedan más por procesar
        if idx + args.batch_size < total:
            delay_lote = random.uniform(args.batch_delay_min, args.batch_delay_max)
            print(f"⏳ Esperando {delay_lote:.2f}s antes del siguiente lote...\n")
            time.sleep(delay_lote)

    print("🏁 ¡PROCESO COMPLETADO!")
    print(f"📊 Estadísticas:")
    print(f"   • Museos procesados: {museos_procesados}/{total}")
    print(f"   • Museos con imágenes: {museos_exitosos}/{total}")
    print(f"   • Tasa de éxito: {(museos_exitosos/total*100):.1f}%")

if __name__ == '__main__':
    main()
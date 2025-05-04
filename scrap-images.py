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
DEFAULT_LIST_FILE            = 'nombres-sitios.txt'
DEFAULT_OUTPUT_DIR           = 'imagenes_gplaces'
DEFAULT_MAX_PHOTOS_PER_PLACE = 1
DEFAULT_DELAY_BETWEEN_CALLS  = (0.5, 1.5)
DEFAULT_BATCH_SIZE           = 5
DEFAULT_BATCH_DELAY_RANGE    = (5.0, 10.0)
URL_TEXT_SEARCH              = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
URL_PLACE_PHOTO              = 'https://maps.googleapis.com/maps/api/place/photo'
# -----------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Descarga imágenes de Google Places en lotes para evitar bloqueos.'
    )
    parser.add_argument(
        '--api-key-file', default=DEFAULT_API_KEY_FILE,
        help='Archivo con la clave de API de Google Places'
    )
    parser.add_argument(
        '--list-file', default=DEFAULT_LIST_FILE,
        help='Archivo con lista de términos a buscar (uno por línea)'
    )
    parser.add_argument(
        '--output-dir', default=DEFAULT_OUTPUT_DIR,
        help='Directorio donde se guardarán las imágenes'
    )
    parser.add_argument(
        '--max-photos', type=int, default=DEFAULT_MAX_PHOTOS_PER_PLACE,
        help='Número máximo de fotos a descargar por lugar'
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
        help='Número de términos a procesar por lote'
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
    return parser.parse_args()


def load_api_key(filepath):
    if not os.path.isfile(filepath):
        raise RuntimeError(f"No se encontró el archivo de API key: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        key = f.read().strip()
    if not key:
        raise RuntimeError(f"El archivo {filepath} está vacío.")
    return key


def load_espacios_from_file(filepath):
    if not os.path.isfile(filepath):
        raise RuntimeError(f"No se encontró el archivo de lista: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def normalize_term(term):
    nfkd = unicodedata.normalize('NFD', term)
    no_diac = ''.join(c for c in nfkd if not unicodedata.combining(c))
    safe = re.sub(r'[^A-Za-z0-9]+', '_', no_diac).strip('_')
    return safe


def get_photo_references_by_title(title, api_key, max_photos):
    params = {'query': title, 'key': api_key}
    try:
        resp = requests.get(URL_TEXT_SEARCH, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get('results', [])
    except requests.RequestException as e:
        print(f"⚠️ Error búsqueda '{title}': {e}")
        return []

    refs = []
    for place in results:
        for photo in place.get('photos', []):
            ref = photo.get('photo_reference')
            if ref:
                refs.append(ref)
                if len(refs) >= max_photos:
                    return refs
    return refs


def fetch_image_data(photo_ref, api_key):
    params = {'photoreference': photo_ref, 'maxwidth': 1200, 'key': api_key}
    try:
        r = requests.get(URL_PLACE_PHOTO, params=params, timeout=15)
        r.raise_for_status()
        return r.content
    except requests.RequestException:
        return None


def select_featured(refs, api_key):
    for ref in refs:
        data = fetch_image_data(ref, api_key)
        if data:
            try:
                img = Image.open(BytesIO(data))
                w, h = img.size
                if w >= h:
                    return ref, data
            except Exception:
                pass
    # fallback to first
    ref = refs[0]
    return ref, fetch_image_data(ref, api_key)


def save_image(data, output_dir, filename):
    path = os.path.join(output_dir, filename)
    with open(path, 'wb') as f:
        f.write(data)
    print(f"✅ Guardada: {path}")


def main():
    args = parse_args()
    api_key = load_api_key(args.api_key_file)
    espacios = load_espacios_from_file(args.list_file)
    os.makedirs(args.output_dir, exist_ok=True)

    print("✅ API OK: clave cargada correctamente.\n")
    total = len(espacios)
    for idx in range(0, total, args.batch_size):
        batch = espacios[idx:idx + args.batch_size]
        lote_num = idx // args.batch_size + 1
        print(f"🔄 Procesando lote {lote_num}/{(total + args.batch_size - 1)//args.batch_size}: {len(batch)} términos")

        for termino in batch:
            safe = normalize_term(termino)
            print(f"🔍 Procesando: {termino}")

            refs = get_photo_references_by_title(termino, api_key, args.max_photos)
            if not refs:
                print(f"❌ No se encontraron fotos para '{termino}'\n")
                continue

            # Imagen destacada
            featured_ref, featured_data = select_featured(refs, api_key)
            if featured_data:
                save_image(featured_data, args.output_dir, f"{safe}-portada.jpg")

            # Resto de fotos
            count = 1
            for ref in refs:
                if ref == featured_ref:
                    continue
                data = fetch_image_data(ref, api_key)
                if not data:
                    continue
                count += 1
                save_image(data, args.output_dir, f"{safe}_{count}.jpg")
                time.sleep(random.uniform(args.min_delay, args.max_delay))
            print()

        # Delay entre lotes si quedan más por procesar
        if idx + args.batch_size < total:
            delay_lote = random.uniform(args.batch_delay_min, args.batch_delay_max)
            print(f"⏳ Esperando {delay_lote:.2f} s antes del siguiente lote...\n")
            time.sleep(delay_lote)

    print("🏁 ¡Proceso completado!")

if __name__ == '__main__':
    main()

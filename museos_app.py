#!/usr/bin/env python3
"""
Aplicación de consola interactiva para scraping de museos
"""
import os
import csv
import json
import requests
import time
import random
import re
from datetime import datetime

class MuseosScraperApp:
    def __init__(self):
        self.api_key = ""
        self.results = []
        
        # Ciudades principales españolas
        self.cities = [
            "Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza", "Málaga",
            "Murcia", "Palma de Mallorca", "Las Palmas de Gran Canaria", "Bilbao",
            "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón", "Granada",
            "A Coruña", "Vitoria-Gasteiz", "Elche", "Oviedo", "Santa Cruz de Tenerife",
            "Badalona", "Cartagena", "Terrassa", "Jerez de la Frontera", "Sabadell",
            "Móstoles", "Alcalá de Henares", "Pamplona", "Fuenlabrada", "Almería",
            "Leganés", "Donostia-San Sebastián", "Burgos", "Santander", "Castellón",
            "Getafe", "Albacete", "Alcorcón", "Logroño", "Badajoz", "Salamanca",
            "Huelva", "Marbella", "Lleida", "Tarragona", "León", "Dos Hermanas",
            "Cádiz", "Santa Coloma de Gramenet", "Algeciras", "Jaén", "Ourense",
            "Reus", "Telde", "Lugo", "Santiago de Compostela", "Cáceres"
        ]
        
        # Campos disponibles
        self.available_fields = {
            'nombre': 'Nombre del museo',
            'calle': 'Calle',
            'direccion_completa': 'Dirección completa',
            'ciudad': 'Ciudad',
            'localidad': 'Localidad/Barrio',
            'codigo_postal': 'Código postal',
            'tipos': 'Tipos de museo',
            'telefono': 'Teléfono',
            'pagina_web': 'Página web',
            'horarios': 'Horarios'
        }
        
        self.load_api_key()
    
    def load_api_key(self):
        try:
            if os.path.exists('google_api_key.txt'):
                with open('google_api_key.txt', 'r') as f:
                    self.api_key = f.read().strip()
        except Exception:
            pass
    
    def save_api_key(self):
        try:
            with open('google_api_key.txt', 'w') as f:
                f.write(self.api_key.strip())
            print("✅ API Key guardada correctamente")
        except Exception as e:
            print(f"❌ Error guardando API Key: {e}")
    
    def show_header(self):
        print("\n" + "="*60)
        print("🏛️  SCRAPER DE MUSEOS DE ESPAÑA")
        print("="*60)
    
    def show_main_menu(self):
        print("\n📋 MENÚ PRINCIPAL:")
        print("1. ⚙️  Configurar API Key")
        print("2. 🏙️  Seleccionar ciudad y buscar museos")
        print("3. 📊 Ver resultados actuales")
        print("4. 📥 Exportar resultados")
        print("5. 🗑️  Limpiar resultados")
        print("0. 🚪 Salir")
        
        choice = input("\n👉 Selecciona una opción (0-5): ").strip()
        return choice
    
    def configure_api_key(self):
        print("\n⚙️ CONFIGURACIÓN API KEY")
        print("-" * 30)
        
        if self.api_key:
            print(f"API Key actual: {self.api_key[:10]}...")
            print("1. Mantener API Key actual")
            print("2. Cambiar API Key")
            choice = input("👉 Selecciona (1-2): ").strip()
            if choice == "1":
                return
        
        new_key = input("🔑 Ingresa tu Google Places API Key: ").strip()
        if new_key:
            self.api_key = new_key
            self.save_api_key()
        else:
            print("❌ API Key no puede estar vacía")
    
    def select_city_and_search(self):
        if not self.api_key:
            print("❌ Primero debes configurar tu API Key")
            return
        
        print("\n🏙️ SELECCIONAR CIUDADES")
        print("-" * 30)
        
        # Mostrar ciudades en columnas
        for i, city in enumerate(self.cities, 1):
            print(f"{i:2d}. {city:<25}", end="")
            if i % 3 == 0:
                print()
        if len(self.cities) % 3 != 0:
            print()
        
        print(f"\n📝 Opciones de selección:")
        print("• Un número: ciudad individual (ej: 1)")
        print("• Varios números separados por comas: múltiples ciudades (ej: 1,5,10)")
        print("• Rango con guión: ciudades consecutivas (ej: 1-5)")
        
        try:
            selection = input(f"\n👉 Selecciona ciudades (1-{len(self.cities)}): ").strip()
            selected_cities = self.parse_city_selection(selection)
            
            if selected_cities:
                print(f"\n✅ Ciudades seleccionadas: {', '.join(selected_cities)}")
                self.configure_search(selected_cities)
            else:
                print("❌ Selección inválida")
        except ValueError:
            print("❌ Por favor ingresa números válidos")
    
    def parse_city_selection(self, selection):
        """Parsea la selección de ciudades del usuario"""
        selected_cities = []
        
        try:
            # Dividir por comas
            parts = [part.strip() for part in selection.split(',')]
            
            for part in parts:
                if '-' in part:
                    # Rango (ej: 1-5)
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        if 1 <= i <= len(self.cities):
                            city = self.cities[i - 1]
                            if city not in selected_cities:
                                selected_cities.append(city)
                else:
                    # Número individual
                    i = int(part)
                    if 1 <= i <= len(self.cities):
                        city = self.cities[i - 1]
                        if city not in selected_cities:
                            selected_cities.append(city)
            
            return selected_cities
            
        except ValueError:
            return []
    
    def configure_search(self, cities):
        # Manejar tanto ciudad individual como lista de ciudades
        if isinstance(cities, str):
            cities = [cities]
        
        cities_str = ", ".join(cities)
        print(f"\n🔍 CONFIGURAR BÚSQUEDA EN: {cities_str.upper()}")
        print("-" * (25 + len(cities_str)))
        
        # Seleccionar campos
        print("📋 Selecciona los campos a extraer:")
        print("(Presiona Enter para seleccionar todos)")
        
        selected_fields = []
        for key, description in self.available_fields.items():
            response = input(f"¿Incluir {description}? (s/N): ").strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                selected_fields.append(key)
        
        # Si no se selecciona nada, incluir todos
        if not selected_fields:
            selected_fields = list(self.available_fields.keys())
            print("✅ Seleccionados todos los campos")
        
        # Configurar límites
        try:
            max_museos_per_city = int(input("🎯 Máximo museos por ciudad (por defecto 20): ") or "20")
        except ValueError:
            max_museos_per_city = 20
        
        try:
            delay = float(input("⏱️ Delay entre peticiones en segundos (por defecto 2.0): ") or "2.0")
        except ValueError:
            delay = 2.0
        
        # Confirmar búsqueda
        print(f"\n📋 RESUMEN DE BÚSQUEDA:")
        print(f"   Ciudades: {', '.join(cities)}")
        print(f"   Campos: {len(selected_fields)} seleccionados")
        print(f"   Máximo museos por ciudad: {max_museos_per_city}")
        print(f"   Total máximo estimado: {max_museos_per_city * len(cities)}")
        print(f"   Delay: {delay}s")
        
        confirm = input("\n¿Iniciar búsqueda? (S/n): ").strip().lower()
        if confirm not in ['n', 'no']:
            self.search_multiple_cities(cities, selected_fields, max_museos_per_city, delay)
    
    def search_multiple_cities(self, cities, selected_fields, max_museos_per_city, delay):
        """Busca museos en múltiples ciudades"""
        print(f"\n🚀 INICIANDO BÚSQUEDA EN {len(cities)} CIUDADES")
        print("=" * 60)
        
        self.results = []  # Limpiar resultados anteriores
        total_found = 0
        
        for i, city in enumerate(cities, 1):
            print(f"\n🏙️ CIUDAD {i}/{len(cities)}: {city.upper()}")
            print("-" * 40)
            
            city_results = []
            try:
                # Usar el método existente pero capturar resultados
                old_results = self.results.copy()
                self.search_museums(city, selected_fields, max_museos_per_city, delay, append_results=True)
                
                # Obtener solo los resultados nuevos de esta ciudad
                city_results = self.results[len(old_results):]
                total_found += len(city_results)
                
                print(f"✅ {city}: {len(city_results)} museos encontrados")
                
            except Exception as e:
                print(f"❌ Error en {city}: {e}")
                continue
        
        # Guardar resultados con nombre de archivo basado en ciudades
        if self.results:
            filename = self.generate_filename(cities)
            self.save_results_to_file(filename)
            
            print(f"\n🎉 ¡BÚSQUEDA MÚLTIPLE COMPLETADA!")
            print(f"   Total ciudades procesadas: {len(cities)}")
            print(f"   Total museos encontrados: {total_found}")
            print(f"   Archivo generado: {filename}")
        else:
            print(f"\n❌ No se encontraron museos en ninguna ciudad")
    
    def generate_filename(self, cities):
        """Genera nombre de archivo basado en las ciudades seleccionadas"""
        # Asegurar que existe la carpeta
        os.makedirs('datos_museos', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if len(cities) == 1:
            # Una sola ciudad
            city_name = cities[0].lower().replace(' ', '_').replace('-', '_')
            filename = f"datos_museos/museos_{city_name}_{timestamp}.csv"
        elif len(cities) <= 3:
            # Pocas ciudades, usar nombres completos
            cities_str = "_".join([c.lower().replace(' ', '_').replace('-', '_') for c in cities])
            filename = f"datos_museos/museos_{cities_str}_{timestamp}.csv"
        else:
            # Muchas ciudades, usar formato genérico
            filename = f"datos_museos/museos_{len(cities)}ciudades_{timestamp}.csv"
        
        return filename
    
    def save_results_to_file(self, filename):
        """Guarda los resultados en el archivo especificado"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if self.results:
                    fieldnames = list(self.available_fields.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.results)
                    print(f"✅ Archivo guardado: {filename}")
                else:
                    print("❌ No hay resultados para guardar")
        except Exception as e:
            print(f"❌ Error guardando archivo: {e}")
    
    def search_museums(self, city, selected_fields, max_museos, delay, append_results=False):
        print(f"\n🚀 INICIANDO BÚSQUEDA EN {city.upper()}")
        print("=" * 50)
        
        if not append_results:
            self.results = []  # Limpiar resultados anteriores solo si no es parte de búsqueda múltiple
        
        try:
            # Búsquedas múltiples
            queries = [
                f"museos en {city} España",
                f"museum {city} Spain",
                f"museo arte {city}",
                f"centro cultural {city}",
                f"fundación museo {city}"
            ]
            
            all_place_ids = set()
            
            for i, query in enumerate(queries, 1):
                print(f"\n🔍 Búsqueda {i}/{len(queries)}: {query}")
                
                params = {
                    'query': query,
                    'key': self.api_key,
                    'language': 'es',
                    'region': 'es'
                }
                
                try:
                    resp = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', 
                                      params=params, timeout=15)
                    
                    if resp.status_code != 200:
                        print(f"   ❌ Error HTTP {resp.status_code}")
                        continue
                        
                    data = resp.json()
                    status = data.get('status', 'UNKNOWN')
                    
                    if status == 'REQUEST_DENIED':
                        print(f"   ❌ API denegada: {data.get('error_message', 'Sin mensaje')}")
                        return
                    elif status not in ['OK', 'ZERO_RESULTS']:
                        print(f"   ⚠️ Status: {status}")
                        continue
                    
                    results = data.get('results', [])
                    print(f"   📍 Encontrados: {len(results)} resultados")
                    
                    # Filtrar resultados relevantes
                    for result in results:
                        place_id = result.get('place_id')
                        if place_id and place_id not in all_place_ids:
                            types = result.get('types', [])
                            museum_types = ['museum', 'art_gallery', 'tourist_attraction', 'cultural_center']
                            
                            if any(t in types for t in museum_types):
                                address = result.get('formatted_address', '').lower()
                                if city.lower() in address or 'españa' in address:
                                    all_place_ids.add(place_id)
                                    
                                    if len(all_place_ids) >= max_museos:
                                        break
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
            
            # Obtener detalles
            place_ids = list(all_place_ids)[:max_museos]
            print(f"\n📋 Obteniendo detalles de {len(place_ids)} museos...")
            
            for i, place_id in enumerate(place_ids, 1):
                print(f"   {i:2d}/{len(place_ids)} - Procesando museo...", end=" ")
                
                try:
                    details = self.get_place_details(place_id)
                    if details:
                        museo_data = self.process_museum_data(details, city)
                        self.results.append(museo_data)
                        print(f"✅ {museo_data['nombre']}")
                    else:
                        print("❌ Sin detalles")
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
            
            print(f"\n🎉 ¡BÚSQUEDA COMPLETADA!")
            print(f"   Total museos encontrados: {len(self.results)}")
            
        except Exception as e:
            print(f"❌ Error durante la búsqueda: {e}")
    
    def get_place_details(self, place_id):
        fields = [
            'name', 'formatted_address', 'address_components', 'international_phone_number',
            'website', 'opening_hours', 'types', 'url'
        ]
        
        params = {
            'place_id': place_id,
            'fields': ','.join(fields),
            'key': self.api_key,
            'language': 'es'
        }
        
        try:
            resp = requests.get('https://maps.googleapis.com/maps/api/place/details/json', 
                              params=params, timeout=15)
            resp.raise_for_status()
            return resp.json().get('result', {})
        except Exception:
            return {}
    
    def extract_street_info(self, address_components):
        """Extrae información de calle y número de los componentes de dirección"""
        street_number = None
        street_name = None
        
        if not address_components:
            return None
        
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
    
    def process_museum_data(self, details, ciudad_buscada):
        # Parsear dirección
        direccion_completa = details.get('formatted_address', 'N/A')
        calle, ciudad, localidad, codigo_postal = self.parse_spanish_address(direccion_completa)
        
        # Intentar obtener calle más precisa desde address_components
        address_components = details.get('address_components', [])
        calle_precisa = self.extract_street_info(address_components)
        if calle_precisa:
            calle = calle_precisa
        
        if ciudad == 'N/A':
            ciudad = ciudad_buscada
        
        # Procesar horarios
        horarios = details.get('opening_hours', {})
        horarios_texto = 'N/A'
        if horarios and 'weekday_text' in horarios:
            horarios_texto = '; '.join(horarios['weekday_text'])
        
        # Procesar tipos
        tipos = ', '.join(details.get('types', []))
        
        return {
            'nombre': details.get('name', 'N/A'),
            'calle': calle,
            'direccion_completa': direccion_completa,
            'ciudad': ciudad,
            'localidad': localidad,
            'codigo_postal': codigo_postal,
            'tipos': tipos,
            'telefono': details.get('international_phone_number', 'N/A'),
            'pagina_web': details.get('website', 'N/A'),
            'horarios': horarios_texto
        }
    
    def parse_spanish_address(self, direccion_completa):
        if not direccion_completa or direccion_completa == 'N/A':
            return "N/A", "N/A", "N/A", "N/A"
        
        # Extraer código postal
        cp_pattern = r'\b(\d{5})\b'
        cp_match = re.search(cp_pattern, direccion_completa)
        codigo_postal = cp_match.group(1) if cp_match else "N/A"
        
        # Eliminar España del final
        addr = re.sub(r',\s*España\s*$', '', direccion_completa, flags=re.IGNORECASE)
        
        # Dividir por comas
        partes = [p.strip() for p in addr.split(',')]
        
        # Inicializar variables
        calle = "N/A"
        ciudad = "N/A"
        localidad = "N/A"
        
        # Ciudades principales españolas ampliada
        ciudades_principales = [
            'Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Zaragoza', 'Málaga',
            'Vigo', 'Gijón', 'Granada', 'Bilbao', 'Alicante', 'Córdoba', 'Valladolid',
            'Murcia', 'Palma', 'Las Palmas', 'Santa Cruz', 'Vitoria', 'Gasteiz',
            'Oviedo', 'Pamplona', 'Santander', 'Burgos', 'Salamanca', 'León',
            'Cádiz', 'Huelva', 'Jaén', 'Almería', 'Albacete', 'Castellón',
            'Logroño', 'Badajoz', 'Cáceres', 'Lleida', 'Tarragona', 'Ourense',
            'Lugo', 'A Coruña', 'Coruña', 'Santiago', 'Pontevedra', 'Elche',
            'Cartagena', 'Jerez', 'Marbella', 'Donostia', 'San Sebastián'
        ]
        
        if len(partes) >= 2:
            # Buscar la calle real (generalmente la segunda parte después del nombre del museo)
            calle_parts = []
            start_index = 1
            
            # Palabras clave que indican dirección de calle
            calle_keywords = ['calle', 'avenida', 'plaza', 'paseo', 'ronda', 'carrera', 'camino', 'travesía', 'carrer', 'etorb']
            
            # Buscar la primera parte que contiene palabras clave de calle
            found_street = False
            for i in range(1, len(partes)):
                parte = partes[i].strip()
                
                # Si contiene palabras clave de calle
                if any(keyword in parte.lower() for keyword in calle_keywords):
                    calle_parts.append(parte)
                    found_street = True
                    
                    # Buscar números en las siguientes partes hasta encontrar ciudad
                    j = i + 1
                    while j < len(partes):
                        siguiente_parte = partes[j].strip()
                        # Si es un número o rango de números, añadir a la calle
                        if re.match(r'^(\d+[A-Za-z]?(\s*-\s*\d+[A-Za-z]?)?|s/n|S/N|sin número)$', siguiente_parte, re.IGNORECASE):
                            calle_parts.append(siguiente_parte)
                            j += 1
                        else:
                            # Si no es número, parar y marcar donde empezar a buscar ciudad
                            break
                    start_index = j
                    break
            
            # Si no encontramos calle con palabras clave, usar enfoque más simple
            if not found_street:
                # Tomar la segunda parte como calle
                calle_parts = [partes[1]]
                
                # Si la tercera parte parece ser un número, añadirla
                if len(partes) > 2:
                    tercera_parte = partes[2].strip()
                    if re.match(r'^(\d+[A-Za-z]?(\s*-\s*\d+[A-Za-z]?)?|s/n|S/N|sin número)$', tercera_parte, re.IGNORECASE):
                        calle_parts.append(tercera_parte)
                        start_index = 3
                    else:
                        start_index = 2
                else:
                    start_index = 2
            
            # Unir las partes de la calle
            calle = ', '.join(calle_parts) if calle_parts else partes[1]
            
            # Buscar ciudad en las partes restantes
            for i in range(start_index, len(partes)):
                parte = partes[i].strip()
                parte_limpia = re.sub(r'\b\d{5}\b', '', parte).strip()
                
                if not parte_limpia:
                    continue
                
                # Verificar si es una ciudad principal
                es_ciudad = False
                for ciudad_ref in ciudades_principales:
                    if ciudad_ref.lower() in parte_limpia.lower():
                        ciudad = parte_limpia
                        es_ciudad = True
                        break
                
                # Si no es ciudad y aún no tenemos localidad, asignar como localidad
                if not es_ciudad and localidad == "N/A":
                    # Filtrar partes que claramente no son localidades
                    provincias = ['Andalucía', 'Cataluña', 'Madrid', 'Valencia', 'Galicia', 
                                'País Vasco', 'Castilla y León', 'Castilla-La Mancha', 
                                'Aragón', 'Extremadura', 'Asturias', 'Murcia', 'Navarra', 
                                'Cantabria', 'La Rioja', 'Islas Baleares', 'Canarias']
                    
                    es_provincia = any(prov.lower() in parte_limpia.lower() for prov in provincias)
                    
                    if not es_provincia and len(parte_limpia) > 1:
                        localidad = parte_limpia
        else:
            # Solo una parte - probablemente solo el nombre del lugar
            calle = partes[0] if partes else "N/A"
        
        return calle, ciudad, localidad, codigo_postal
    
    def show_results(self):
        if not self.results:
            print("\n❌ No hay resultados para mostrar")
            return
        
        print(f"\n📊 RESULTADOS ({len(self.results)} museos)")
        print("=" * 60)
        
        for i, museo in enumerate(self.results, 1):
            print(f"\n{i:2d}. {museo['nombre']}")
            print(f"    📍 {museo['calle']}, {museo['ciudad']}")
            if museo['direccion_completa'] != 'N/A':
                print(f"    🗺️ {museo['direccion_completa']}")
            if museo['localidad'] != 'N/A':
                print(f"    🏘️ {museo['localidad']}")
            if museo['codigo_postal'] != 'N/A':
                print(f"    📮 {museo['codigo_postal']}")
            if museo['telefono'] != 'N/A':
                print(f"    📞 {museo['telefono']}")
            if museo['pagina_web'] != 'N/A':
                print(f"    🌐 {museo['pagina_web']}")
            if museo['tipos'] != 'N/A':
                print(f"    🏷️ {museo['tipos']}")
        
        input("\n👉 Presiona Enter para continuar...")
    
    def export_results(self):
        if not self.results:
            print("\n❌ No hay resultados para exportar")
            return
        
        print("\n📥 EXPORTAR RESULTADOS")
        print("-" * 25)
        print("1. 📄 Exportar a CSV")
        print("2. 📋 Mostrar en formato copiable")
        print("0. 🔙 Volver")
        
        choice = input("👉 Selecciona opción (0-2): ").strip()
        
        if choice == "1":
            self.export_to_csv()
        elif choice == "2":
            self.show_copyable_format()
    
    def export_to_csv(self):
        os.makedirs('datos_museos', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"datos_museos/museos_exportacion_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(self.available_fields.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"✅ Exportado a {filename}")
            print(f"📊 {len(self.results)} museos guardados")
            
        except Exception as e:
            print(f"❌ Error exportando: {e}")
    
    def show_copyable_format(self):
        print("\n📋 FORMATO COPIABLE (separado por tabulaciones)")
        print("=" * 60)
        
        # Encabezados
        headers = [self.available_fields[field] for field in self.available_fields.keys()]
        print('\t'.join(headers))
        
        # Datos
        for museo in self.results:
            values = [museo.get(field, 'N/A') for field in self.available_fields.keys()]
            print('\t'.join(values))
        
        print(f"\n✅ {len(self.results)} museos listos para copiar")
        input("👉 Presiona Enter para continuar...")
    
    def clear_results(self):
        if not self.results:
            print("\n❌ No hay resultados para limpiar")
            return
        
        confirm = input(f"\n🗑️ ¿Limpiar {len(self.results)} resultados? (s/N): ").strip().lower()
        if confirm in ['s', 'si', 'sí', 'y', 'yes']:
            self.results = []
            print("✅ Resultados limpiados")
    
    def run(self):
        self.show_header()
        
        while True:
            choice = self.show_main_menu()
            
            if choice == "1":
                self.configure_api_key()
            elif choice == "2":
                self.select_city_and_search()
            elif choice == "3":
                self.show_results()
            elif choice == "4":
                self.export_results()
            elif choice == "5":
                self.clear_results()
            elif choice == "0":
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")

def main():
    app = MuseosScraperApp()
    app.run()

if __name__ == '__main__':
    main()
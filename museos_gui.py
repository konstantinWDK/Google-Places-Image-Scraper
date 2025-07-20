#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import time
import random
import re
import csv
import os
from datetime import datetime
import unicodedata

class MuseosScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏛️ Scraper de Museos - España")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.api_key = tk.StringVar()
        self.selected_city = tk.StringVar()
        self.scraping = False
        self.results = []
        
        # Campos disponibles
        self.available_fields = {
            'nombre': 'Nombre del museo',
            'calle': 'Calle',
            'ciudad': 'Ciudad',
            'localidad': 'Localidad/Barrio',
            'codigo_postal': 'Código postal',
            'tipos': 'Tipos de museo',
            'telefono': 'Teléfono',
            'pagina_web': 'Página web',
            'horarios': 'Horarios'
        }
        
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
        
        self.setup_ui()
        self.load_api_key()
    
    def setup_ui(self):
        # Crear notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña de configuración
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ Configuración")
        self.setup_config_tab(config_frame)
        
        # Pestaña de resultados
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="📊 Resultados")
        self.setup_results_tab(results_frame)
    
    def setup_config_tab(self, parent):
        # Frame principal con scroll
        canvas = tk.Canvas(parent, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # API Key Section
        api_frame = ttk.LabelFrame(scrollable_frame, text="🔑 Configuración API", padding=15)
        api_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(api_frame, text="Google Places API Key:").pack(anchor='w')
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=60, show="*")
        api_entry.pack(fill='x', pady=(5, 10))
        
        api_buttons_frame = ttk.Frame(api_frame)
        api_buttons_frame.pack(fill='x')
        ttk.Button(api_buttons_frame, text="💾 Guardar API Key", 
                  command=self.save_api_key).pack(side='left', padx=(0, 10))
        ttk.Button(api_buttons_frame, text="📁 Cargar desde archivo", 
                  command=self.load_api_key_file).pack(side='left')
        
        # Ciudad Selection
        city_frame = ttk.LabelFrame(scrollable_frame, text="🏙️ Seleccionar Ciudad", padding=15)
        city_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(city_frame, text="Ciudad española:").pack(anchor='w')
        city_combo = ttk.Combobox(city_frame, textvariable=self.selected_city, 
                                 values=self.cities, state="readonly", width=40)
        city_combo.pack(anchor='w', pady=(5, 0))
        city_combo.set("Madrid")  # Por defecto
        
        # Campos a extraer
        fields_frame = ttk.LabelFrame(scrollable_frame, text="📋 Campos a Extraer", padding=15)
        fields_frame.pack(fill='x', padx=10, pady=10)
        
        # Variables para checkboxes
        self.field_vars = {}
        
        # Crear checkboxes en dos columnas
        fields_grid = ttk.Frame(fields_frame)
        fields_grid.pack(fill='x')
        
        row = 0
        col = 0
        for field_key, field_name in self.available_fields.items():
            self.field_vars[field_key] = tk.BooleanVar(value=True)  # Todos marcados por defecto
            cb = ttk.Checkbutton(fields_grid, text=field_name, 
                               variable=self.field_vars[field_key])
            cb.grid(row=row, column=col, sticky='w', padx=10, pady=2)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        # Botones de selección rápida
        quick_buttons_frame = ttk.Frame(fields_frame)
        quick_buttons_frame.pack(fill='x', pady=(10, 0))
        ttk.Button(quick_buttons_frame, text="✅ Seleccionar todos", 
                  command=self.select_all_fields).pack(side='left', padx=(0, 10))
        ttk.Button(quick_buttons_frame, text="❌ Deseleccionar todos", 
                  command=self.deselect_all_fields).pack(side='left')
        
        # Configuración de scraping
        scraping_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Configuración de Scraping", padding=15)
        scraping_frame.pack(fill='x', padx=10, pady=10)
        
        # Límite de museos
        limit_frame = ttk.Frame(scraping_frame)
        limit_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(limit_frame, text="Máximo museos a buscar:").pack(side='left')
        self.limit_var = tk.IntVar(value=20)
        limit_spinbox = ttk.Spinbox(limit_frame, from_=5, to=100, 
                                   textvariable=self.limit_var, width=10)
        limit_spinbox.pack(side='left', padx=(10, 0))
        
        # Delay entre peticiones
        delay_frame = ttk.Frame(scraping_frame)
        delay_frame.pack(fill='x')
        ttk.Label(delay_frame, text="Delay entre peticiones (seg):").pack(side='left')
        self.delay_var = tk.DoubleVar(value=2.0)
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0.5, to=10.0, increment=0.5,
                                   textvariable=self.delay_var, width=10)
        delay_spinbox.pack(side='left', padx=(10, 0))
        
        # Botón de inicio
        start_frame = ttk.Frame(scrollable_frame)
        start_frame.pack(fill='x', padx=10, pady=20)
        
        self.start_button = ttk.Button(start_frame, text="🚀 Iniciar Scraping", 
                                      command=self.start_scraping)
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(start_frame, text="⏹️ Detener", 
                                     command=self.stop_scraping, state='disabled')
        self.stop_button.pack(side='left')
        
        # Barra de progreso
        self.progress_var = tk.StringVar(value="Listo para comenzar")
        ttk.Label(start_frame, textvariable=self.progress_var).pack(side='left', padx=(20, 0))
        
        # Configurar canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_results_tab(self, parent):
        # Frame superior con botones
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="📋 Copiar Todo", 
                  command=self.copy_all_results).pack(side='left', padx=(0, 10))
        ttk.Button(buttons_frame, text="📥 Exportar CSV", 
                  command=self.export_csv).pack(side='left', padx=(0, 10))
        ttk.Button(buttons_frame, text="🗑️ Limpiar", 
                  command=self.clear_results).pack(side='left', padx=(0, 10))
        
        # Información
        self.info_var = tk.StringVar(value="Sin resultados")
        ttk.Label(buttons_frame, textvariable=self.info_var).pack(side='right')
        
        # Tabla de resultados
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Crear Treeview con scrollbars
        self.tree = ttk.Treeview(table_frame)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Posicionar elementos
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Configurar columnas iniciales
        self.setup_tree_columns()
    
    def setup_tree_columns(self):
        # Obtener campos seleccionados
        selected_fields = [field for field, var in self.field_vars.items() if var.get()]
        
        if not selected_fields:
            selected_fields = ['nombre', 'ciudad']  # Mínimo por defecto
        
        # Configurar columnas
        self.tree["columns"] = selected_fields
        self.tree["show"] = "headings"
        
        for field in selected_fields:
            self.tree.heading(field, text=self.available_fields.get(field, field))
            self.tree.column(field, width=150, minwidth=100)
    
    def load_api_key(self):
        try:
            if os.path.exists('google_api_key.txt'):
                with open('google_api_key.txt', 'r') as f:
                    self.api_key.set(f.read().strip())
        except Exception as e:
            print(f"Error cargando API key: {e}")
    
    def save_api_key(self):
        try:
            with open('google_api_key.txt', 'w') as f:
                f.write(self.api_key.get().strip())
            messagebox.showinfo("Éxito", "API Key guardada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando API Key: {e}")
    
    def load_api_key_file(self):
        try:
            filename = filedialog.askopenfilename(
                title="Seleccionar archivo API Key",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r') as f:
                    self.api_key.set(f.read().strip())
                messagebox.showinfo("Éxito", "API Key cargada desde archivo")
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando archivo: {e}")
    
    def select_all_fields(self):
        for var in self.field_vars.values():
            var.set(True)
    
    def deselect_all_fields(self):
        for var in self.field_vars.values():
            var.set(False)
    
    def start_scraping(self):
        # Validaciones
        if not self.api_key.get().strip():
            messagebox.showerror("Error", "Por favor ingresa una API Key válida")
            return
        
        if not self.selected_city.get():
            messagebox.showerror("Error", "Por favor selecciona una ciudad")
            return
        
        selected_fields = [field for field, var in self.field_vars.items() if var.get()]
        if not selected_fields:
            messagebox.showerror("Error", "Por favor selecciona al menos un campo")
            return
        
        # Configurar UI para scraping
        self.scraping = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.results = []
        self.clear_results()
        self.setup_tree_columns()
        
        # Iniciar scraping en hilo separado
        threading.Thread(target=self.scrape_museums, daemon=True).start()
    
    def stop_scraping(self):
        self.scraping = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_var.set("Scraping detenido")
    
    def scrape_museums(self):
        try:
            city = self.selected_city.get()
            api_key = self.api_key.get().strip()
            max_results = self.limit_var.get()
            delay = self.delay_var.get()
            
            self.progress_var.set(f"Buscando museos en {city}...")
            
            # Búsquedas múltiples para mejor cobertura
            queries = [
                f"museos en {city} España",
                f"museum {city} Spain",
                f"museo arte {city}",
                f"centro cultural {city}",
                f"fundación museo {city}"
            ]
            
            all_place_ids = set()
            
            for i, query in enumerate(queries):
                if not self.scraping:
                    break
                
                self.progress_var.set(f"Búsqueda {i+1}/{len(queries)}: {query}")
                
                # Búsqueda inicial
                params = {
                    'query': query,
                    'key': api_key,
                    'language': 'es',
                    'region': 'es'
                }
                
                try:
                    resp = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', 
                                      params=params, timeout=15)
                    
                    if resp.status_code != 200:
                        continue
                        
                    data = resp.json()
                    status = data.get('status', 'UNKNOWN')
                    
                    if status == 'REQUEST_DENIED':
                        messagebox.showerror("Error API", f"API denegada: {data.get('error_message', 'Sin mensaje')}")
                        self.stop_scraping()
                        return
                    elif status not in ['OK', 'ZERO_RESULTS']:
                        continue
                    
                    results = data.get('results', [])
                    
                    for result in results:
                        place_id = result.get('place_id')
                        if place_id and place_id not in all_place_ids:
                            # Filtrar por tipos relevantes
                            types = result.get('types', [])
                            museum_types = ['museum', 'art_gallery', 'tourist_attraction', 'cultural_center']
                            
                            if any(t in types for t in museum_types):
                                address = result.get('formatted_address', '').lower()
                                if city.lower() in address or 'españa' in address:
                                    all_place_ids.add(place_id)
                                    
                                    if len(all_place_ids) >= max_results:
                                        break
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"Error en búsqueda {query}: {e}")
                    continue
            
            # Obtener detalles de cada museo
            place_ids = list(all_place_ids)[:max_results]
            
            for i, place_id in enumerate(place_ids):
                if not self.scraping:
                    break
                
                self.progress_var.set(f"Obteniendo detalles {i+1}/{len(place_ids)}...")
                
                try:
                    details = self.get_place_details(place_id, api_key)
                    if details:
                        museo_data = self.process_museum_data(details, city)
                        self.add_result_to_table(museo_data)
                        self.results.append(museo_data)
                
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"Error obteniendo detalles {place_id}: {e}")
                    continue
            
            # Finalizar
            if self.scraping:
                self.progress_var.set(f"✅ Completado: {len(self.results)} museos encontrados")
                self.info_var.set(f"Total: {len(self.results)} museos en {city}")
            
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el scraping: {e}")
            self.stop_scraping()
    
    def get_place_details(self, place_id, api_key):
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
            resp = requests.get('https://maps.googleapis.com/maps/api/place/details/json', 
                              params=params, timeout=15)
            resp.raise_for_status()
            return resp.json().get('result', {})
        except Exception:
            return {}
    
    def process_museum_data(self, details, ciudad_buscada):
        # Parsear dirección
        direccion_completa = details.get('formatted_address', 'N/A')
        calle, ciudad, localidad, codigo_postal = self.parse_spanish_address(direccion_completa)
        
        # Si la ciudad parseada está vacía, usar la ciudad buscada
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
    
    def add_result_to_table(self, museo_data):
        # Obtener campos seleccionados
        selected_fields = [field for field, var in self.field_vars.items() if var.get()]
        
        # Crear valores para las columnas seleccionadas
        values = [museo_data.get(field, 'N/A') for field in selected_fields]
        
        # Añadir a la tabla
        self.tree.insert('', 'end', values=values)
        
        # Scroll automático al final
        self.tree.see(self.tree.get_children()[-1])
        
        # Actualizar contador
        current_count = len(self.tree.get_children())
        self.info_var.set(f"Museos encontrados: {current_count}")
    
    def copy_all_results(self):
        if not self.results:
            messagebox.showwarning("Advertencia", "No hay resultados para copiar")
            return
        
        try:
            # Obtener campos seleccionados
            selected_fields = [field for field, var in self.field_vars.items() if var.get()]
            
            # Crear texto para copiar
            lines = []
            
            # Encabezados
            headers = [self.available_fields.get(field, field) for field in selected_fields]
            lines.append('\t'.join(headers))
            
            # Datos
            for museo in self.results:
                values = [museo.get(field, 'N/A') for field in selected_fields]
                lines.append('\t'.join(values))
            
            # Copiar al portapapeles
            text = '\n'.join(lines)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            
            messagebox.showinfo("Éxito", f"Copiados {len(self.results)} museos al portapapeles")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error copiando datos: {e}")
    
    def export_csv(self):
        if not self.results:
            messagebox.showwarning("Advertencia", "No hay resultados para exportar")
            return
        
        try:
            # Seleccionar archivo
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Guardar resultados como CSV"
            )
            
            if filename:
                # Obtener campos seleccionados
                selected_fields = [field for field, var in self.field_vars.items() if var.get()]
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=selected_fields)
                    writer.writeheader()
                    
                    for museo in self.results:
                        # Escribir solo campos seleccionados
                        filtered_museo = {field: museo.get(field, 'N/A') for field in selected_fields}
                        writer.writerow(filtered_museo)
                
                messagebox.showinfo("Éxito", f"Exportados {len(self.results)} museos a {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando CSV: {e}")
    
    def clear_results(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Limpiar resultados
        self.results = []
        self.info_var.set("Sin resultados")

def main():
    root = tk.Tk()
    app = MuseosScraperGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
# 🏛️ Scraper de Museos de España

Aplicación para extraer información de museos españoles usando Google Places API.

## 📁 Archivos disponibles

### 🖥️ Aplicación con interfaz gráfica (GUI)
- **`museos_gui.py`** - Aplicación con interfaz gráfica completa
- **`check_gui.py`** - Verificador de dependencias para GUI

### 💻 Aplicación de consola
- **`museos_app.py`** - Aplicación interactiva de consola (recomendada)

### 🛠️ Scripts de línea de comandos
- **`buscar-museos-ciudad.py`** - Script para buscar museos por ciudad
- **`buscar-museos-espana.py`** - Script para extraer todos los museos de España

## 🚀 Uso recomendado

### Opción 1: Aplicación de consola (más compatible)
```bash
python3 museos_app.py
```

### Opción 2: Aplicación GUI (si tienes tkinter)
```bash
python3 check_gui.py
```

## ⚙️ Configuración inicial

1. **Obtener API Key de Google Places:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Habilita la API de Places
   - Crea una API Key
   - Configura las restricciones (opcional)

2. **Guardar API Key:**
   - Crea un archivo `google_api_key.txt`
   - Pega tu API Key en el archivo
   - O configúrala desde la aplicación

## 📊 Datos extraídos

La aplicación puede extraer los siguientes campos:

- ✅ **Nombre del museo**
- ✅ **Calle** - Dirección de la calle
- ✅ **Ciudad** - Ciudad principal
- ✅ **Localidad** - Barrio/distrito (cuando esté disponible)
- ✅ **Código postal** - CP de 5 dígitos
- ✅ **Tipos de museo** - Categorías del museo
- ✅ **Teléfono** - Número internacional
- ✅ **Página web** - URL oficial
- ✅ **Horarios** - Horarios de apertura

## 🏙️ Ciudades disponibles

Más de 50 ciudades españolas principales:
- Madrid, Barcelona, Valencia, Sevilla
- Zaragoza, Málaga, Bilbao, Granada
- Vigo, Gijón, A Coruña, Salamanca
- Y muchas más...

## 📥 Formatos de exportación

- **CSV** - Para Excel/LibreOffice
- **Formato copiable** - Para pegar directamente
- **Tabla en pantalla** - Para visualización

## 🎯 Características

### ✨ Funcionalidades principales
- 🔍 Búsqueda inteligente por ciudad
- 📋 Selección flexible de campos
- ⚙️ Configuración de límites y delays
- 📊 Visualización en tiempo real
- 📥 Múltiples formatos de exportación
- 📋 Funcionalidad de copia

### 🛡️ Características técnicas
- ⏱️ Control de velocidad para evitar bloqueos
- 🔄 Múltiples queries por ciudad
- 🧹 Filtrado inteligente de resultados
- 📍 Parsing avanzado de direcciones españolas
- ❌ Manejo robusto de errores

## 🚨 Solución de problemas

### Error de API Key
```
❌ API denegada: This IP, site or mobile application is not authorized
```
**Solución:** Configura la API Key sin restricciones de IP en Google Cloud Console

### Sin resultados
```
❌ No se encontraron museos
```
**Posibles causas:**
- Ciudad mal escrita
- API Key sin permisos
- Límites de cuota excedidos

### Error de tkinter
```
❌ tkinter no disponible
```
**Solución:** Usar `museos_app.py` (aplicación de consola)

## 📝 Ejemplo de uso

```bash
# Lanzar aplicación
python3 museos_app.py

# Seleccionar:
# 1. Configurar API Key
# 2. Seleccionar ciudad (ej: Madrid)
# 3. Elegir campos a extraer
# 4. Configurar límites (ej: 20 museos)
# 5. Iniciar búsqueda
# 6. Exportar resultados
```

## 📋 Dependencias

- `requests` - Para llamadas a la API
- `tkinter` - Solo para GUI (opcional)

```bash
pip install requests
```

## 🔧 Archivos generados

- `museos_YYYYMMDD_HHMMSS.csv` - Resultados en CSV
- `google_api_key.txt` - Tu API Key guardada

## ⚠️ Notas importantes

- **Cuotas de API:** Google Places tiene límites diarios
- **Velocidad:** Usa delays apropiados para evitar bloqueos
- **Calidad:** No todos los museos tienen información completa
- **Cobertura:** Funciona mejor en ciudades grandes

## 🆘 Soporte

Si tienes problemas:
1. Verifica tu API Key
2. Revisa las restricciones en Google Cloud
3. Asegúrate de tener cuota disponible
4. Usa la aplicación de consola como alternativa
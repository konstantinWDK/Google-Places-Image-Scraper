Google Places Image Scraper

Descripcion:
Repositorio para un script en Python (`scrap-images.py`) que descarga imágenes de Google Places por lotes para evitar bloqueos de la API.

Ajustes principales:
- Tamaño de lote (--batch-size): número de términos a procesar por lote (por defecto 5).
- Retardo entre peticiones (--min-delay, --max-delay): intervalo aleatorio en segundos entre cada llamada.
- Retardo entre lotes (--batch-delay-min, --batch-delay-max): intervalo aleatorio en segundos al cambiar de lote.
- Fotos máximas por lugar (--max-photos): número de imágenes a descargar por término.
- Rutas de archivos y directorios: especificables con --api-key-file, --list-file, --output-dir.

Dependencias necesarias:
- Python 3.6 o superior
- requests
- Pillow

Obtener clave API de Google Places:
1) Ir a https://console.cloud.google.com/
2) Crear o seleccionar un proyecto.
3) En APIs y servicios > Biblioteca, habilitar Places API.
4) En APIs y servicios > Credenciales, crear clave de API.
5) (Opcional) Restringir la clave por IP o dominio.
6) Guardar la clave en un archivo de texto (por ejemplo google_api_key.txt).

Estructura del repositorio:
    scrap-images.py         # Script principal
    nombres-sitios.txt            # Términos a buscar (uno por línea)
    google_api_key.txt      # Clave API (no incluir en el repositorio)
    .gitignore              # Archivos a ignorar

Uso del script:
1) Clonar el repositorio:
       git clone https://github.com/konstantinWDK/Google-Places-Image-Scraper.git
       cd Google-Places-Image-Scraper
2) Ejecutar con opciones:
       python scrap-images.py \
         --api-key-file google_api_key.txt \
         --list-file nombres-sitios.txt \
         --output-dir imagenes_salida \
         --max-photos 2 \
         --min-delay 0.5 \
         --max-delay 1.5 \
         --batch-size 5 \
         --batch-delay-min 5 \
         --batch-delay-max 10

Argumentos disponibles y valores por defecto:
- --api-key-file      google_api_key.txt
- --list-file         nombres-sitios.txt
- --output-dir        imagenes_gplaces
- --max-photos        1
- --min-delay         0.5
- --max-delay         1.5
- --batch-size        5
- --batch-delay-min   5.0
- --batch-delay-max   10.0

Notas:
- No subir google_api_key.txt al repositorio público.
- Ajustar retardos y tamaño de lote según cuota y necesidades.

Contribuciones:
Las contribuciones son bienvenidas. Abrir un issue o pull request.

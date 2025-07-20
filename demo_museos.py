#!/usr/bin/env python3
"""
Demostración del Scraper de Museos
"""
import os
from museos_app import MuseosScraperApp

def demo():
    print("🎬 DEMOSTRACIÓN - SCRAPER DE MUSEOS")
    print("=" * 50)
    
    # Verificar API Key
    if not os.path.exists('google_api_key.txt'):
        print("❌ No se encontró google_api_key.txt")
        print("📝 Crea el archivo con tu API Key de Google Places")
        return
    
    with open('google_api_key.txt', 'r') as f:
        api_key = f.read().strip()
    
    if not api_key:
        print("❌ El archivo google_api_key.txt está vacío")
        return
    
    print(f"✅ API Key encontrada: {api_key[:10]}...")
    
    # Crear instancia del scraper
    app = MuseosScraperApp()
    
    # Configuración de demo
    demo_city = "Vigo"  # Ciudad pequeña para demo rápida
    demo_fields = ['nombre', 'calle', 'ciudad', 'telefono', 'pagina_web']
    max_museos = 5  # Pocos museos para demo
    delay = 1.0
    
    print(f"\n🏛️ Demostración con {demo_city}")
    print(f"📋 Campos: {', '.join(demo_fields)}")
    print(f"🎯 Máximo: {max_museos} museos")
    print(f"⏱️ Delay: {delay}s")
    
    input("\n👉 Presiona Enter para comenzar la demostración...")
    
    # Ejecutar búsqueda
    try:
        app.search_museums(demo_city, demo_fields, max_museos, delay)
        
        if app.results:
            print(f"\n🎉 ¡Demo completada!")
            print(f"📊 Encontrados {len(app.results)} museos:")
            
            for i, museo in enumerate(app.results, 1):
                print(f"\n{i}. {museo['nombre']}")
                print(f"   📍 {museo['calle']}, {museo['ciudad']}")
                if museo['telefono'] != 'N/A':
                    print(f"   📞 {museo['telefono']}")
                if museo['pagina_web'] != 'N/A':
                    print(f"   🌐 {museo['pagina_web']}")
            
            # Exportar demo
            print(f"\n📥 Exportando demo...")
            app.export_to_csv()
            
        else:
            print("\n❌ No se encontraron museos en la demo")
            
    except Exception as e:
        print(f"\n❌ Error en la demo: {e}")
    
    print(f"\n✨ Fin de la demostración")
    print(f"🚀 Para usar la aplicación completa ejecuta: python3 museos_app.py")

if __name__ == '__main__':
    demo()
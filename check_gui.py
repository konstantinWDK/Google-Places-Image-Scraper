#!/usr/bin/env python3
"""
Script para verificar si tkinter está disponible y lanzar la GUI
"""
import sys

def check_requirements():
    missing = []
    
    try:
        import tkinter
        print("✅ tkinter disponible")
    except ImportError:
        missing.append("tkinter")
        print("❌ tkinter no disponible")
    
    try:
        import requests
        print("✅ requests disponible")
    except ImportError:
        missing.append("requests")
        print("❌ requests no disponible")
    
    if missing:
        print(f"\n❌ Faltan dependencias: {', '.join(missing)}")
        print("\nPara instalar:")
        if "requests" in missing:
            print("pip install requests")
        if "tkinter" in missing:
            print("sudo apt-get install python3-tk  # En Ubuntu/Debian")
            print("# o")
            print("# Reinstalar Python con soporte GUI")
        return False
    else:
        print("\n✅ Todas las dependencias están disponibles")
        return True

def launch_gui():
    try:
        from museos_gui import main
        print("🚀 Lanzando aplicación GUI...")
        main()
    except Exception as e:
        print(f"❌ Error lanzando GUI: {e}")
        return False
    return True

if __name__ == '__main__':
    print("🔍 Verificando dependencias...")
    
    if check_requirements():
        launch_gui()
    else:
        print("\n⚠️ No se puede lanzar la aplicación. Instala las dependencias faltantes.")
        sys.exit(1)
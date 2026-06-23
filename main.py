#!/usr/bin/env python3
"""
Sistema de Monitoreo Distribuido
Refactorizado sin clases - usando match-case con selección interactiva
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import time
import signal

# Importar el sistema de menús basado en funciones
from ui.menu_system import run_menu_system

def signal_handler(sig, frame):
    """Maneja la señal SIGINT (Ctrl+C) para salir del programa limpiamente"""
    print("\n\n👋 Saliendo del sistema de monitoreo...")
    sys.exit(0)

def verificar_instalacion():
    """Verifica que el sistema esté correctamente instalado"""
    archivos_requeridos = [
        'config.json',
        'core/config_manager.py', 
        'ui/config_interface.py',
        'ui/dashboard.py',
        'requirements.txt'
    ]
    
    faltantes = []
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            faltantes.append(archivo)
    
    if faltantes:
        print(f"❌ Archivos faltantes: {', '.join(faltantes)}")
        print("📝 Asegúrate de haber clonado el repositorio completo")
        print("🔄 Si faltan dependencias, ejecuta:")
        print("   pip install -r requirements.txt")
        return False
    
    # Verificar directorios
    os.makedirs("logs", exist_ok=True)
    os.makedirs("keys", exist_ok=True)
    
    return True

def mostrar_banner():
    """Muestra el banner del sistema"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     SISTEMA DE MONITOREO DISTRIBUIDO                         ║
║                   Tecnicatura en Infraestructura - Python                    ║
║                                                                              ║
║  🖥️  Monitoreo remoto SSH    📊 Métricas CPU/Mem/Temp                         ║
║  🚨 Sistema de alertas       📋 Tablero interactivo                          ║
║  ⚙️  Umbrales configurables  📈 Reportes detallados                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Función principal del programa"""
    try:
        # Configurar manejador de señales
        signal.signal(signal.SIGINT, signal_handler)
        
        # Verificar instalación
        if not verificar_instalacion():
            return
        
        # Mostrar banner
        mostrar_banner()
        time.sleep(2)
        
        print("🚀 Iniciando Sistema de Monitoreo Distribuido...")
        time.sleep(1)
        
        # Ejecutar sistema de menús con selección interactiva
        run_menu_system()
        
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 Sistema de monitoreo finalizado")

if __name__ == "__main__":
    main()
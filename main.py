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

# Plantilla mínima para config.json
_CONFIG_TEMPLATE = """{{
  "equipos": [
    {{
      "nombre": "Equipo-Local",
      "ip": "localhost",
      "user": "local",
      "ssh_key_path": "",
      "port": 22,
      "tipo": "local",
      "ssh_activo": false,
      "ping_activo": true
    }}
  ],
  "monitoreo": {{
    "intervalo_segundos": 30,
    "temp_limite": 50.0,
    "cpu_limite": 80.0,
    "memoria_limite": 85.0,
    "reintentos": 3
  }},
  "logging": {{
    "directorio": "./logs",
    "archivo_principal": "monitor_distribuido.log",
    "max_bytes": 10485760,
    "backup_count": 5
  }},
  "alertas": {{
    "email_activo": false,
    "notificaciones_desktop": true,
    "voz_activa": false
  }},
  "umbrales_por_equipo": {{}},
  "agente_ping": {{
    "activo": true,
    "intervalo_segundos": 30,
    "timeout_ping": 3,
    "dispositivos_criticos": []
  }}
}}"""

def verificar_instalacion():
    """Verifica que el sistema esté correctamente instalado"""
    ok = True

    # --- Archivos de código fuente (deben existir en el repo) ---
    archivos_codigo = [
        'core/config_manager.py',
        'ui/config_interface.py',
        'ui/dashboard.py',
        'requirements.txt',
    ]
    faltantes_codigo = [f for f in archivos_codigo if not os.path.exists(f)]
    if faltantes_codigo:
        print("❌ Archivos del repositorio faltantes:")
        for f in faltantes_codigo:
            print(f"   • {f}")
        print("   → Asegúrate de haber clonado el repositorio completo:")
        print("     git clone https://github.com/ignacio-istea/Proyecto_final.git")
        ok = False

    # --- config.json (ignorado en .gitignore, debe crearse manualmente) ---
    if not os.path.exists('config.json'):
        print()
        print("⚠️  Archivo 'config.json' no encontrado (está en .gitignore, no se versiona).")
        print("   → Créalo manualmente en la raíz del proyecto.")
        print("   → Plantilla mínima para copiar y pegar:")
        print("   ─" * 30)
        print(_CONFIG_TEMPLATE)
        print("   ─" * 30)
        print("   Guárdalo como 'config.json' y edita los equipos según tu red.")
        ok = False

    # --- Directorio keys/ (ignorado en .gitignore) ---
    if not os.path.exists('keys'):
        print()
        print("⚠️  Directorio 'keys/' no encontrado (está en .gitignore, no se versiona).")
        print("   → Créalo y coloca dentro las claves SSH de tus equipos:")
        print("     mkdir keys")
        print("     cp /ruta/a/tu/clave.pem keys/")
        print("   → Si no usas SSH, puedes dejarlo vacío: mkdir keys")
    else:
        # El directorio existe pero puede estar vacío — solo informar
        claves = [f for f in os.listdir('keys') if f.endswith(('.pem', '.key', '.pub', 'id_ed25519', 'id_rsa'))]
        if not claves:
            print()
            print("ℹ️  El directorio 'keys/' existe pero no contiene claves SSH.")
            print("   → Si usas conexiones SSH, copia tus claves ahí:")
            print("     cp /ruta/a/tu/clave.pem keys/")

    # --- Directorio logs/ (se puede crear automáticamente) ---
    os.makedirs('logs', exist_ok=True)

    return ok

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
        instalacion_ok = verificar_instalacion()
        if not instalacion_ok:
            print()
            respuesta = input("¿Deseas continuar de todas formas? (s/N): ").strip().lower()
            if respuesta != 's':
                print("\n👋 Corrige los problemas indicados y vuelve a ejecutar el programa.")
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
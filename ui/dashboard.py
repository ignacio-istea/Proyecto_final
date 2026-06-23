#!/usr/bin/env python3
"""
Dashboard Principal Modularizado
Sistema de Monitoreo Distribuido
"""

# Suprimir warnings de deprecación
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*TripleDES.*")

import time
import questionary
from questionary import Style

# Importar módulos del dashboard
from ui.dashboard_modules.data_manager import init_alarm_data, registrar_evento
from ui.dashboard_modules.display import mostrar_tablero_tiempo_real
from ui.dashboard_modules.history import mostrar_historial_filtrable
from ui.dashboard_modules.reports import generar_reporte_alarmas
from ui.dashboard_modules.stats import mostrar_estadisticas
from ui.dashboard_modules.maintenance import ejecutar_limpieza_alarmas

_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
])

def ejecutar_tablero_alarmas(config_path="config.json"):
    """Función principal para ejecutar el tablero de alarmas"""
    import os
    
    init_alarm_data(config_path)
    
    while True:
        try:
            # Limpiar pantalla
            os.system('cls' if os.name == 'nt' else 'clear')
            
            opciones = [
                "🚨 Ver tablero de alarmas en tiempo real",
                "📋 Historial filtrable de eventos",
                "📈 Generar reporte de alarmas",
                "🧹 Limpiar alarmas resueltas",
                "📊 Estadísticas del sistema",
                "← Volver al menú principal"
            ]
            
            try:
                opcion = questionary.select(
                    "🚨 TABLERO DE ALARMAS - ¿Qué deseas hacer?",
                    choices=opciones,
                    style=_custom_style
                ).ask()
                
                if not opcion:
                    break
                    
            except ImportError:
                # Fallback sin questionary
                print("🚨 TABLERO DE ALARMAS")
                print("="*50)
                for i, opcion_menu in enumerate(opciones, 1):
                    print(f"{i}. {opcion_menu}")
                
                try:
                    seleccion = input("\nSelecciona una opción (1-6): ")
                    idx = int(seleccion) - 1
                    if 0 <= idx < len(opciones):
                        opcion = opciones[idx]
                    else:
                        print("❌ Opción inválida")
                        time.sleep(1)
                        continue
                except (ValueError, KeyboardInterrupt):
                    print("\n❌ Operación cancelada")
                    break
            
            # Limpiar pantalla antes de ejecutar opción
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Ejecutar opción seleccionada
            if "🚨 Ver tablero" in opcion:
                try:
                    mostrar_tablero_tiempo_real()
                except KeyboardInterrupt:
                    pass
            elif "📋 Historial filtrable" in opcion:
                mostrar_historial_filtrable()
            elif "📈 Generar reporte" in opcion:
                generar_reporte_alarmas()
            elif "🧹 Limpiar alarmas" in opcion:
                ejecutar_limpieza_alarmas()
            elif "📊 Estadísticas" in opcion:
                mostrar_estadisticas()
            elif "← Volver" in opcion:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("👋 Volviendo al menú principal...")
                time.sleep(1)
                break
                
        except KeyboardInterrupt:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n\n🚫 Saliendo del tablero de alarmas...")
            time.sleep(1)
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPresiona Enter para continuar...")

def main():
    """Función principal"""
    try:
        ejecutar_tablero_alarmas()
    except KeyboardInterrupt:
        print("\n\nSaliendo del tablero de alarmas...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
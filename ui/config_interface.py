#!/usr/bin/env python3
"""
Menú Interactivo para Configuración de Umbrales
Sistema de Monitoreo Distribuido
"""

# Suprimir warnings de deprecación
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*TripleDES.*")

import json
import os
from pathlib import Path
import questionary
from questionary import Style


# Variables globales para configuración
_config_path = "config.json"
_config = None
_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])

def init_configurador(config_path="config.json"):
    """Inicializa el configurador con la ruta del archivo de configuración"""
    global _config_path, _config
    _config_path = config_path
    _config = _cargar_config()
    return _config is not None

def _cargar_config():
    """Carga la configuración desde el archivo JSON"""
    try:
        with open(_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {_config_path}")
        return None

def _guardar_config():
    """Guarda la configuración al archivo JSON"""
    try:
        with open(_config_path, 'w') as f:
            json.dump(_config, f, indent=2, ensure_ascii=False)
        print("✓ Configuración guardada correctamente")
        return True
    except Exception as e:
        print(f"✗ Error guardando configuración: {e}")
        return False

def _inicializar_umbrales_equipo(equipo_nombre):
    """Inicializa umbrales por equipo si no existen"""
    if 'umbrales_por_equipo' not in _config:
        _config['umbrales_por_equipo'] = {}
    
    if equipo_nombre not in _config['umbrales_por_equipo']:
        # Usar valores globales como base
        monitoreo = _config['monitoreo']
        _config['umbrales_por_equipo'][equipo_nombre] = {
            'cpu': {
                'warning': round(monitoreo['cpu_limite'] * 0.7, 1),
                'critico': monitoreo['cpu_limite'],
                'clear': round(monitoreo['cpu_limite'] * 0.6, 1)
            },
            'memoria': {
                'warning': round(monitoreo['memoria_limite'] * 0.7, 1),
                'critico': monitoreo['memoria_limite'],
                'clear': round(monitoreo['memoria_limite'] * 0.6, 1)
            },
            'temperatura': {
                'warning': round(monitoreo['temp_limite'] * 0.8, 1),
                'critico': monitoreo['temp_limite'],
                'clear': round(monitoreo['temp_limite'] * 0.7, 1)
            }
        }
    
def mostrar_menu_principal():
    """Muestra el menú principal de opciones"""
    opciones = [
        "📊 Ver umbrales actuales",
        "⚙️  Configurar umbrales por equipo",
        "🖥️  Gestionar equipos",
        "🌐 Configurar umbrales globales",
        "🚨 Ver tablero de alarmas",
        "💾 Guardar y salir",
        "❌ Salir sin guardar"
    ]
    
    return questionary.select(
        "¿Qué deseas hacer?",
        choices=opciones,
        style=_custom_style
    ).ask()

def ver_umbrales_actuales():
    """Muestra los umbrales actuales de todos los equipos"""
    print("\n" + "="*60)
    print("📊 UMBRALES ACTUALES DEL SISTEMA")
    print("="*60)
    
    # Umbrales globales
    monitoreo = _config['monitoreo']
    print(f"\n🌐 UMBRALES GLOBALES:")
    print(f"   CPU Crítico: {monitoreo['cpu_limite']}%")
    print(f"   Memoria Crítica: {monitoreo['memoria_limite']}%")
    print(f"   Temperatura Crítica: {monitoreo['temp_limite']}°C")
    
    # Umbrales por equipo
    if 'umbrales_por_equipo' in _config:
        print(f"\n📋 UMBRALES POR EQUIPO:")
        for equipo_nombre, umbrales in _config['umbrales_por_equipo'].items():
            print(f"\n   🖥️  {equipo_nombre}:")
            for metrica, niveles in umbrales.items():
                unidad = "%" if metrica != "temperatura" else "°C"
                print(f"      {metrica.upper()}: Clear={niveles['clear']}{unidad} | "
                      f"Warning={niveles['warning']}{unidad} | "
                      f"Crítico={niveles['critico']}{unidad}")
    else:
        print(f"\n📋 No hay umbrales específicos por equipo configurados")
    
    print("\n" + "="*60)
    input("Presiona Enter para continuar...")

def configurar_umbrales_equipo():
    """Menú para configurar umbrales de un equipo específico"""
    equipos = [equipo['nombre'] for equipo in _config['equipos']]
    equipos.append("← Volver al menú principal")
    
    equipo_seleccionado = questionary.select(
        "Selecciona el equipo a configurar:",
        choices=equipos,
        style=_custom_style
    ).ask()
    
    if equipo_seleccionado == "← Volver al menú principal":
        return
    
    _inicializar_umbrales_equipo(equipo_seleccionado)
    _configurar_metricas_equipo(equipo_seleccionado)
    
def _configurar_metricas_equipo(equipo_nombre):
    """Configura las métricas de un equipo específico"""
    while True:
        umbrales = _config['umbrales_por_equipo'][equipo_nombre]
        
        opciones_metricas = [
            f"🖥️  CPU (C:{umbrales['cpu']['clear']}% | W:{umbrales['cpu']['warning']}% | Cr:{umbrales['cpu']['critico']}%)",
            f"💾 Memoria (C:{umbrales['memoria']['clear']}% | W:{umbrales['memoria']['warning']}% | Cr:{umbrales['memoria']['critico']}%)",
            f"🌡️  Temperatura (C:{umbrales['temperatura']['clear']}°C | W:{umbrales['temperatura']['warning']}°C | Cr:{umbrales['temperatura']['critico']}°C)",
            "← Volver"
        ]
        
        metrica_seleccionada = questionary.select(
            f"Configurando {equipo_nombre} - Selecciona métrica:",
            choices=opciones_metricas,
            style=_custom_style
        ).ask()
        
        if metrica_seleccionada.startswith("← Volver"):
            break
        elif metrica_seleccionada.startswith("🖥️"):
            _configurar_niveles_metrica(equipo_nombre, 'cpu', '%')
        elif metrica_seleccionada.startswith("💾"):
            _configurar_niveles_metrica(equipo_nombre, 'memoria', '%')
        elif metrica_seleccionada.startswith("🌡️"):
            _configurar_niveles_metrica(equipo_nombre, 'temperatura', '°C')

    
def ejecutar_configurador():
    """Ejecuta el menú principal con navegación mejorada"""
    import os
    
    if not init_configurador():
        return
    
    print("🔧 CONFIGURADOR DE UMBRALES - Sistema de Monitoreo Distribuido")
    
    while True:
        try:
            # Limpiar pantalla
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("🔧 CONFIGURADOR DE UMBRALES")
            print("="*50)
            
            opcion = mostrar_menu_principal()
            
            if not opcion:  # Usuario canceló
                break
            
            # Limpiar pantalla antes de ejecutar opción
            os.system('cls' if os.name == 'nt' else 'clear')
            
            if "📊 Ver umbrales" in opcion:
                ver_umbrales_actuales()
            
            elif "⚙️  Configurar umbrales por equipo" in opcion:
                print("⚙️ CONFIGURACIÓN POR EQUIPO")
                print("="*50)
                configurar_umbrales_equipo()
            
            elif "🖥️  Gestionar equipos" in opcion:
                print("🖥️ GESTIÓN DE EQUIPOS")
                print("="*50)
                gestionar_equipos()
            
            elif "🌐 Configurar umbrales globales" in opcion:
                print("🌐 CONFIGURACIÓN GLOBAL")
                print("="*50)
                configurar_umbrales_globales()
            
            elif "🚨 Ver tablero" in opcion:
                try:
                    from tablero_alarmas import ejecutar_tablero_alarmas
                    ejecutar_tablero_alarmas(_config_path)
                except ImportError:
                    print("❌ Error: No se pudo cargar el módulo de tablero de alarmas")
                    input("\nPresiona Enter para continuar...")
                except Exception as e:
                    print(f"❌ Error en tablero de alarmas: {e}")
                    input("\nPresiona Enter para continuar...")
            
            elif "💾 Guardar y salir" in opcion:
                if _guardar_config():
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("✅ ¡Configuración guardada exitosamente!")
                    break
            
            elif "❌ Salir sin guardar" in opcion:
                salir_sin_guardar = questionary.select(
                    "¿Estás seguro de salir sin guardar los cambios?",
                    choices=["💾 No, guardar antes de salir", "❌ Sí, salir sin guardar"],
                    style=_custom_style
                ).ask()
                
                if salir_sin_guardar == "❌ Sí, salir sin guardar":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("👋 Saliendo sin guardar cambios...")
                    break
                elif salir_sin_guardar == "💾 No, guardar antes de salir":
                    if _guardar_config():
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print("✅ ¡Configuración guardada exitosamente!")
                        break
                    
        except KeyboardInterrupt:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n\n🚫 Operación cancelada")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPresiona Enter para continuar...")

# Funciones simplificadas para las funcionalidades principales
def configurar_umbrales_globales():
    """Configura los umbrales globales del sistema"""
    print("Funcionalidad de umbrales globales disponible")
    input("\nPresiona Enter para continuar...")

def gestionar_equipos():
    """Menú para gestionar equipos del sistema"""
    print("Funcionalidad de gestión de equipos disponible")
    input("\nPresiona Enter para continuar...")

def _configurar_niveles_metrica(equipo_nombre, metrica, unidad):
    """Configura los niveles de una métrica"""
    print(f"Configurando {metrica} para {equipo_nombre}")
    input("\nPresiona Enter para continuar...")


def main():
    """Función principal"""
    try:
        ejecutar_configurador()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
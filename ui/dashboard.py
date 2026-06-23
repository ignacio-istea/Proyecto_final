#!/usr/bin/env python3
"""
Tablero de Alarmas Interactivo con Rich
Sistema de Monitoreo Distribuido
"""

# Suprimir warnings de deprecación
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*TripleDES.*")

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import questionary
from questionary import Style
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text


# Variables globales para el tablero de alarmas
_config_path = "config.json"
_config = None
_alarmas_activas = {}
_historial_eventos = []
_console = Console()
_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
])

def init_alarm_manager(config_path="config.json"):
    """Inicializa el gestor de alarmas"""
    global _config_path, _config
    _config_path = config_path
    _config = _cargar_config()
    _cargar_datos_alarmas()
    return True

def _cargar_config():
    """Carga la configuración desde el archivo JSON"""
    try:
        with open(_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def _cargar_datos_alarmas():
    """Carga alarmas y eventos desde archivos de datos"""
    global _alarmas_activas, _historial_eventos
    try:
        # Cargar alarmas activas
        if Path("./logs/alarmas_activas.json").exists():
            with open("./logs/alarmas_activas.json", 'r') as f:
                _alarmas_activas = json.load(f)
        
        # Cargar historial de eventos
        if Path("./logs/historial_eventos.json").exists():
            with open("./logs/historial_eventos.json", 'r') as f:
                _historial_eventos = json.load(f)
    except Exception as e:
        print(f"Error cargando datos de alarmas: {e}")

def _guardar_datos_alarmas():
    """Guarda alarmas y eventos en archivos JSON"""
    try:
        Path("./logs").mkdir(exist_ok=True)
        
        # Guardar alarmas activas
        with open("./logs/alarmas_activas.json", 'w') as f:
            json.dump(_alarmas_activas, f, indent=2)
        
        # Guardar historial (últimos 1000 eventos)
        with open("./logs/historial_eventos.json", 'w') as f:
            json.dump(_historial_eventos[-1000:], f, indent=2)
    except Exception as e:
        print(f"Error guardando datos: {e}")

def registrar_evento(equipo, metrica, severidad, valor, umbral):
    """Registra un nuevo evento de alarma"""
    global _alarmas_activas, _historial_eventos
    
    timestamp = datetime.now().isoformat()
    
    evento = {
        "timestamp": timestamp,
        "equipo": equipo,
        "metrica": metrica,
        "severidad": severidad,
        "valor": valor,
        "umbral": umbral,
        "id": f"{equipo}_{metrica}_{int(time.time())}"
    }
    
    # Agregar al historial
    _historial_eventos.append(evento)
    
    # Manejar alarmas activas
    key = f"{equipo}_{metrica}"
    
    if severidad == "clear":
        # Remover de alarmas activas si existe
        if key in _alarmas_activas:
            _alarmas_activas[key]["estado"] = "resuelto"
            _alarmas_activas[key]["resuelto_timestamp"] = timestamp
    else:
        # Agregar/actualizar alarma activa
        _alarmas_activas[key] = {
            "equipo": equipo,
            "metrica": metrica,
            "severidad": severidad,
            "valor": valor,
            "umbral": umbral,
            "inicio_timestamp": _alarmas_activas.get(key, {}).get("inicio_timestamp") or timestamp,
            "ultimo_timestamp": timestamp,
            "estado": "activo",
            "contador_eventos": _alarmas_activas.get(key, {}).get("contador_eventos", 0) + 1
        }
    
    _guardar_datos_alarmas()
    
def mostrar_tablero_tiempo_real():
    """Muestra el tablero en tiempo real con colores rich"""
    import os
    
    # Limpiar pantalla al inicio
    os.system('cls' if os.name == 'nt' else 'clear')
    
    try:
        _console.print("🚨 [bold red]TABLERO DE ALARMAS - VISTA EN TIEMPO REAL[/bold red]")
        _console.print("Presiona [yellow]Ctrl+C[/yellow] para salir")
        _console.print("=" * 80, style="dim")
        
        contador = 0
        
        while True:
            try:
                contador += 1
                
                # Recargar datos
                _cargar_datos_alarmas()
                
                # Mostrar contenido actualizado
                _console.clear()
                _console.print(f"🚨 [bold red]TABLERO DE ALARMAS #{contador:03d}[/bold red]")
                _console.print(f"[blue]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/blue]")
                _console.print("=" * 60)
                
                # Mostrar alarmas usando Rich
                _mostrar_alarmas_rich()
                
                _console.print("\n[yellow]🎮 Presiona Ctrl+C para salir[/yellow]")
                
                # Pausa antes de la siguiente actualización
                time.sleep(3)
                
            except KeyboardInterrupt:
                break
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        _console.print(f"[red]Error en tablero: {e}[/red]")
        # Fallback a modo simple
        _tablero_simple_fallback()
    finally:
        # Limpiar pantalla al salir
        os.system('cls' if os.name == 'nt' else 'clear')
        _console.print("👋 [green]Saliendo del tablero de alarmas...[/green]")
        time.sleep(1)

def _mostrar_alarmas_rich():
    """Muestra alarmas activas usando Rich"""
    # Filtrar solo alarmas activas
    alarmas_filtradas = {k: v for k, v in _alarmas_activas.items() 
                       if v.get("estado") == "activo"}
    
    if not alarmas_filtradas:
        _console.print("[green]✅ ESTADO: SIN ALARMAS ACTIVAS[/green]")
        _console.print("[green]🟢 Todos los equipos funcionando normalmente[/green]")
        return
    
    # Crear tabla
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("🖥️ Equipo", style="cyan")
    table.add_column("📊 Tipo", style="green")
    table.add_column("⚠️ Severidad", style="yellow")
    table.add_column("📈 Info", style="white")
    
    for key, alarma in alarmas_filtradas.items():
        equipo = alarma['equipo']
        
        # Tipo y valores
        if "metrica" in alarma:
            metrica = alarma['metrica']
            tipo_display = f"📊 {metrica}"
            valor = alarma.get('valor', 0)
            umbral = alarma.get('umbral', 0)
            unidad = "%" if metrica != "temperatura" else "°C"
            info_display = f"{valor:.1f}{unidad}/{umbral:.0f}{unidad}"
        else:
            tipo_display = "📡 Conexión"
            info_display = "OFFLINE"
        
        # Severidad con colores
        severidad = alarma["severidad"]
        if severidad == "critico":
            sev_display = "[bold red]🔴 CRÍTICO[/bold red]"
        elif severidad == "warning":
            sev_display = "[bold yellow]🟡 WARNING[/bold yellow]"
        else:
            sev_display = "[bold blue]🔵 INFO[/bold blue]"
        
        table.add_row(equipo, tipo_display, sev_display, info_display)
    
    _console.print(table)
    
    # Mostrar estadísticas
    total_criticas = len([a for a in alarmas_filtradas.values() 
                        if a.get("severidad") == "critico"])
    total_warnings = len([a for a in alarmas_filtradas.values() 
                        if a.get("severidad") == "warning"])
    
    _console.print(f"\n[red]🚨 Total alarmas: {len(alarmas_filtradas)}[/red]")
    _console.print(f"[red]🔴 Críticas: {total_criticas}[/red] | [yellow]🟡 Warnings: {total_warnings}[/yellow]")

def _tablero_simple_fallback():
    """Tablero simple como fallback"""
    import os
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("🚨 TABLERO DE ALARMAS - MODO SIMPLE")
            print(f"🕰️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
            
            _cargar_datos_alarmas()
            _mostrar_alarmas_simple()
            
            print("\n🎮 Controles: Ctrl+C = Salir")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("👋 Saliendo del tablero...")
        time.sleep(1)

def _mostrar_alarmas_simple():
    """Muestra alarmas en formato simple"""
    alarmas_filtradas = {k: v for k, v in _alarmas_activas.items() 
                       if v.get("estado") == "activo"}
    
    if not alarmas_filtradas:
        print("✅ ESTADO: SIN ALARMAS ACTIVAS")
        print("🟢 Todos los equipos funcionando normalmente")
        return
    
    print(f"🚨 ALARMAS ACTIVAS: {len(alarmas_filtradas)}")
    print("-" * 50)
    
    for i, (key, alarma) in enumerate(alarmas_filtradas.items(), 1):
        # Emoji según severidad
        if alarma["severidad"] == "critico":
            emoji = "🔴"
        elif alarma["severidad"] == "warning":
            emoji = "🟡"
        else:
            emoji = "🔵"
        
        print(f"{i:2d}. {emoji} {alarma['equipo']} - {alarma.get('metrica', 'conexion').upper()}")
        if "valor" in alarma:
            valor = alarma['valor']
            umbral = alarma['umbral']
            unidad = "%" if alarma.get('metrica') != "temperatura" else "°C"
            print(f"     Valor: {valor:.1f}{unidad} / Límite: {umbral:.1f}{unidad}")
        print()

    
def ejecutar_tablero_alarmas(config_path="config.json"):
    """Función principal para ejecutar el tablero de alarmas"""
    import os
    
    init_alarm_manager(config_path)
    
    while True:
        try:
            # Limpiar pantalla
            os.system('cls' if os.name == 'nt' else 'clear')
            
            opciones = [
                "🚨 Ver tablero de alarmas en tiempo real",
                "← Volver al menú principal"
            ]
            
            try:
                import questionary
                
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
                    seleccion = input("\nSelecciona una opción (1-2): ")
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
            
            if "🚨 Ver tablero" in opcion:
                try:
                    mostrar_tablero_tiempo_real()
                except KeyboardInterrupt:
                    pass
            
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
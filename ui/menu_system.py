#!/usr/bin/env python3
"""
Sistema de menús usando match-case
Simplificada del sistema con máquina de estados
"""

import os
import sys
import subprocess
import threading
import time
from enum import Enum
import questionary
from questionary import Style

# Importar funciones de agentes
try:
    from agents.ag_controller import (
        start_ping_agent, stop_ping_agent,
        start_ssh_agent, stop_ssh_agent, 
        start_monitor_distribuido, stop_monitor_distribuido,
        show_agents_status, handle_exit
    )
    import agents.ag_controller as agent_functions
except ImportError as e:
    print(f"Error importando funciones de agentes: {e}")
    # Funciones dummy como fallback
    def start_ping_agent(): print("Error: funciones de agentes no disponibles")
    def stop_ping_agent(): pass
    def start_ssh_agent(): pass
    def stop_ssh_agent(): pass  
    def start_monitor_distribuido(): pass
    def stop_monitor_distribuido(): pass
    def show_agents_status(): pass
    def handle_exit(): pass

class MenuState(Enum):
    MAIN = "main"
    AGENTS = "agents" 
    LOCAL_SYSTEM = "local_system"
    EXIT = "exit"

class MenuAction(Enum):
    SHOW_ALARMS = "show_alarms"
    CONFIG_THRESHOLDS = "config_thresholds"
    AGENTS_MENU = "agents_menu"
    LOCAL_MENU = "local_menu"
    START_PING = "start_ping"
    START_SSH = "start_ssh"
    START_MONITOR = "start_monitor"
    STOP_PING = "stop_ping"
    STOP_SSH = "stop_ssh"
    STOP_MONITOR = "stop_monitor"
    SHOW_AGENTS_STATUS = "show_agents_status"
    SHOW_LOGS = "show_logs"
    CLEAN_DATA = "clean_data"
    SYSTEM_INFO = "system_info"
    BACK = "back"
    EXIT = "exit"

# Variables globales para mantener estado de agentes
# (manejadas por agent_functions)

def clear_screen():
    """Limpia la pantalla de la consola"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_user_input_interactive():
    """Obtiene entrada del usuario con selección interactiva"""
    # Mostrar título del menú principal
    print("\n📋 MENÚ PRINCIPAL")
    print("─" * 50)
    
    custom_style = Style([
        ('qmark', 'fg:#ff9d00 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#ff9d00 bold'),
        ('pointer', 'fg:#ff9d00 bold'),
        ('highlighted', 'fg:#ff9d00 bold'),
        ('selected', 'fg:#cc5454'),
    ])
    
    try:
        return questionary.select(
            "👉 Selecciona una opción:",
            choices=[
                "📊 Ver tablero de alarmas",
                "⚙️ Configurar dispositivos", 
                "🤖 Agentes de monitoreo",
                "💻 Sistema local",
                "❌ Salir"
            ],
            style=custom_style
        ).ask()
    except (KeyboardInterrupt, EOFError):
        return "❌ Salir"

def get_agents_input_interactive():
    """Obtiene entrada del menú de agentes con selección interactiva"""
    # Obtener estado de agentes
    try:
        ping_running = agent_functions.ping_running
        ssh_running = agent_functions.ssh_running  
        monitor_running = agent_functions.monitor_running
    except:
        ping_running = ssh_running = monitor_running = False
    
    # Mostrar título del menú de agentes
    print("\n🤖 AGENTES DE MONITOREO")
    print("─" * 50)
    
    # Mostrar estado actual de agentes
    print(f"📊 Estado actual:")
    print(f"  • Ping: {'🟢 ACTIVO' if ping_running else '🔴 INACTIVO'}")
    print(f"  • SSH: {'🟢 ACTIVO' if ssh_running else '🔴 INACTIVO'}")
    print(f"  • Monitor: {'🟢 ACTIVO' if monitor_running else '🔴 INACTIVO'}")
    print()
    
    custom_style = Style([
        ('qmark', 'fg:#ff9d00 bold'),
        ('question', 'bold'), 
        ('answer', 'fg:#ff9d00 bold'),
        ('pointer', 'fg:#ff9d00 bold'),
        ('highlighted', 'fg:#ff9d00 bold'),
        ('selected', 'fg:#cc5454'),
    ])
    
    # Crear opciones dinámicas basadas en el estado
    choices = []
    
    # Opciones de iniciar/detener ping
    if ping_running:
        choices.append("🛑 Detener agente de ping")
    else:
        choices.append("🏓 Iniciar agente de ping")
    
    # Opciones de iniciar/detener SSH
    if ssh_running:
        choices.append("🛑 Detener agente SSH")
    else:
        choices.append("🔐 Iniciar agente SSH")
    
    # Opciones de iniciar/detener monitor
    if monitor_running:
        choices.append("🛑 Detener monitor distribuido")
    else:
        choices.append("📡 Iniciar monitor distribuido")
    
    # Opciones adicionales
    choices.extend([
        "📊 Ver estado de agentes",
        "⬅️ Volver al menú principal"
    ])
    
    try:
        return questionary.select(
            "👉 Selecciona una opción:",
            choices=choices,
            style=custom_style
        ).ask()
    except (KeyboardInterrupt, EOFError):
        return "⬅️ Volver al menú principal"

def get_local_system_input_interactive():
    """Obtiene entrada del menú de sistema local con selección interactiva"""
    # Mostrar título del menú de sistema local
    print("\n💻 SISTEMA LOCAL")
    print("─" * 50)
    
    custom_style = Style([
        ('qmark', 'fg:#ff9d00 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#ff9d00 bold'), 
        ('pointer', 'fg:#ff9d00 bold'),
        ('highlighted', 'fg:#ff9d00 bold'),
        ('selected', 'fg:#cc5454'),
    ])
    
    try:
        return questionary.select(
            "👉 Selecciona una opción:",
            choices=[
                "📄 Ver logs del sistema",
                "🧹 Limpiar datos/alarmas",
                "ℹ️ Información del sistema",
                "⬅️ Volver al menú principal"
            ],
            style=custom_style
        ).ask()
    except (KeyboardInterrupt, EOFError):
        return "⬅️ Volver al menú principal"

def execute_action(action):
    """Ejecuta la acción correspondiente usando match-case"""
    match action:
        case MenuAction.SHOW_ALARMS:
            try:
                clear_screen()
                print("📊 Cargando tablero de alarmas...")
                from ui.dashboard import ejecutar_tablero_alarmas
                ejecutar_tablero_alarmas()
            except Exception as e:
                print(f"❌ Error ejecutando tablero: {e}")
                try:
                    questionary.press_any_key_to_continue(
                        "Presiona cualquier tecla para continuar..."
                    ).ask()
                except:
                    input("\nPresiona Enter para continuar...")
            
        case MenuAction.CONFIG_THRESHOLDS:
            try:
                clear_screen()
                print("⚙️ Cargando configurador de umbrales...")
                from ui.config_interface import ejecutar_configurador
                ejecutar_configurador()
            except Exception as e:
                print(f"❌ Error ejecutando configurador: {e}")
                try:
                    questionary.press_any_key_to_continue(
                        "Presiona cualquier tecla para continuar..."
                    ).ask()
                except:
                    input("\nPresiona Enter para continuar...")
            
        case MenuAction.START_PING:
            clear_screen()
            start_ping_agent()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.STOP_PING:
            clear_screen()
            stop_ping_agent()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.START_SSH:
            clear_screen()
            start_ssh_agent()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.STOP_SSH:
            clear_screen()
            stop_ssh_agent()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.START_MONITOR:
            clear_screen()
            start_monitor_distribuido()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.STOP_MONITOR:
            clear_screen()
            stop_monitor_distribuido()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.SHOW_AGENTS_STATUS:
            show_agents_status()
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
            
        case MenuAction.SHOW_LOGS:
            show_logs()
            
        case MenuAction.CLEAN_DATA:
            clean_system_data()
            
        case MenuAction.SYSTEM_INFO:
            show_system_info()
            
        case _:
            print("❌ Acción no reconocida")

def process_main_menu_input(choice):
    """Procesa la entrada del menú principal usando match-case"""
    match choice:
        case "📊 Ver tablero de alarmas":
            return MenuAction.SHOW_ALARMS, MenuState.MAIN
        case "⚙️ Configurar dispositivos":
            return MenuAction.CONFIG_THRESHOLDS, MenuState.MAIN
        case "🤖 Agentes de monitoreo":
            return None, MenuState.AGENTS
        case "💻 Sistema local":
            return None, MenuState.LOCAL_SYSTEM
        case "❌ Salir":
            return MenuAction.EXIT, MenuState.EXIT
        case _:
            print("❌ Opción inválida.")
            input("Presiona Enter para continuar...")
            return None, MenuState.MAIN

def process_agents_menu_input(choice):
    """Procesa la entrada del menú de agentes usando match-case"""
    match choice:
        case "🏓 Iniciar agente de ping":
            return MenuAction.START_PING, MenuState.AGENTS
        case "🛑 Detener agente de ping":
            return MenuAction.STOP_PING, MenuState.AGENTS
        case "🔐 Iniciar agente SSH":
            return MenuAction.START_SSH, MenuState.AGENTS
        case "🛑 Detener agente SSH":
            return MenuAction.STOP_SSH, MenuState.AGENTS
        case "📡 Iniciar monitor distribuido":
            return MenuAction.START_MONITOR, MenuState.AGENTS
        case "🛑 Detener monitor distribuido":
            return MenuAction.STOP_MONITOR, MenuState.AGENTS
        case "📊 Ver estado de agentes":
            return MenuAction.SHOW_AGENTS_STATUS, MenuState.AGENTS
        case "⬅️ Volver al menú principal":
            return None, MenuState.MAIN
        case _:
            print("❌ Opción inválida.")
            input("Presiona Enter para continuar...")
            return None, MenuState.AGENTS

def process_local_system_input(choice):
    """Procesa la entrada del menú de sistema local usando match-case"""
    match choice:
        case "📄 Ver logs del sistema":
            return MenuAction.SHOW_LOGS, MenuState.LOCAL_SYSTEM
        case "🧹 Limpiar datos/alarmas":
            return MenuAction.CLEAN_DATA, MenuState.LOCAL_SYSTEM
        case "ℹ️ Información del sistema":
            return MenuAction.SYSTEM_INFO, MenuState.LOCAL_SYSTEM
        case "⬅️ Volver al menú principal":
            return None, MenuState.MAIN
        case _:
            print("❌ Opción inválida.")
            input("Presiona Enter para continuar...")
            return None, MenuState.LOCAL_SYSTEM

def show_logs():
    """Muestra los logs del sistema con selección interactiva"""
    clear_screen()
    print("📄 LOGS DEL SISTEMA")
    print("=" * 40)
    
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        if log_files:
            custom_style = Style([
                ('qmark', 'fg:#ff9d00 bold'),
                ('question', 'bold'),
                ('answer', 'fg:#ff9d00 bold'),
                ('pointer', 'fg:#ff9d00 bold'),
                ('highlighted', 'fg:#ff9d00 bold'),
                ('selected', 'fg:#cc5454'),
            ])
            
            try:
                choice = questionary.select(
                    "Selecciona un log para ver:",
                    choices=log_files + ["⬅️ Volver"],
                    style=custom_style
                ).ask()
                
                if choice and choice != "⬅️ Volver":
                    log_path = os.path.join(logs_dir, choice)
                    clear_screen()
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            print(f"📄 LOG: {choice}")
                            print("=" * 60)
                            content = f.read()
                            # Mostrar últimas 2000 caracteres
                            if len(content) > 2000:
                                print("... (mostrando últimas líneas)")
                                print(content[-2000:])
                            else:
                                print(content)
                            print("=" * 60)
                    except Exception as e:
                        print(f"❌ Error leyendo archivo: {e}")
                    
                    # Usar questionary para continuar
                    try:
                        questionary.press_any_key_to_continue(
                            "Presiona cualquier tecla para continuar..."
                        ).ask()
                    except:
                        input("\nPresiona Enter para continuar...")
            except (FileNotFoundError, KeyboardInterrupt):
                print("❌ Error al leer el archivo")
        else:
            print("No hay archivos de log disponibles")
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
    else:
        print("Directorio de logs no encontrado")
        try:
            questionary.press_any_key_to_continue(
                "Presiona cualquier tecla para continuar..."
            ).ask()
        except:
            input("\nPresiona Enter para continuar...")

def clean_system_data():
    """Limpia datos del sistema con selección interactiva"""
    clear_screen()
    print("🧹 LIMPIEZA DE DATOS")
    print("=" * 40)
    
    custom_style = Style([
        ('qmark', 'fg:#ff9d00 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#ff9d00 bold'),
        ('pointer', 'fg:#ff9d00 bold'),
        ('highlighted', 'fg:#ff9d00 bold'),
        ('selected', 'fg:#cc5454'),
    ])
    
    try:
        choice = questionary.select(
            "Selecciona qué limpiar:",
            choices=[
                "📄 Limpiar logs",
                "🚨 Limpiar archivos de alarmas",
                "🧹 Limpiar todo",
                "⬅️ Volver"
            ],
            style=custom_style
        ).ask()
        
        if choice and choice != "⬅️ Volver":
            clear_screen()
            print("🧹 EJECUTANDO LIMPIEZA...")
            print("=" * 40)
            
            match choice:
                case "📄 Limpiar logs":
                    clean_logs()
                case "🚨 Limpiar archivos de alarmas":
                    clean_alarms()
                case "🧹 Limpiar todo":
                    clean_logs()
                    clean_alarms()
            
            print("\n✅ Limpieza completada")
            
            # Usar questionary para continuar
            try:
                questionary.press_any_key_to_continue(
                    "Presiona cualquier tecla para continuar..."
                ).ask()
            except:
                input("\nPresiona Enter para continuar...")
                
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada")
        try:
            questionary.press_any_key_to_continue(
                "Presiona cualquier tecla para continuar..."
            ).ask()
        except:
            input("\nPresiona Enter para continuar...")

def clean_logs():
    """Limpia archivos de log"""
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        for file in os.listdir(logs_dir):
            if file.endswith('.log'):
                os.remove(os.path.join(logs_dir, file))
        print("✅ Logs limpiados")

def clean_alarms():
    """Limpia archivos de alarmas"""
    alarm_files = ["alarmas_activas.json", "eventos_alarmas.json"]
    for file in alarm_files:
        if os.path.exists(file):
            os.remove(file)
    print("✅ Archivos de alarmas limpiados")

def show_system_info():
    """Muestra información del sistema"""
    clear_screen()
    print("ℹ️  INFORMACIÓN DEL SISTEMA")
    print("=" * 40)
    print(f"OS: {os.name}")
    print(f"Python: {sys.version}")
    print(f"Directorio: {os.getcwd()}")
    print(f"PID: {os.getpid()}")
    
    # Verificar archivos de configuración
    config_files = ["config.json", "requirements.txt"]
    print("\n📁 Archivos de configuración:")
    for file in config_files:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"{status} {file}")
    
    # Verificar directorios
    directories = ["logs", "keys"]
    print("\n📂 Directorios:")
    for directory in directories:
        status = "✅" if os.path.exists(directory) else "❌"
        print(f"{status} {directory}/")
    
    print("=" * 40)
    
    # Usar questionary para continuar
    try:
        questionary.press_any_key_to_continue(
            "Presiona cualquier tecla para continuar..."
        ).ask()
    except:
        input("\nPresiona Enter para continuar...")

def run_menu_system():
    """Función principal que ejecuta el sistema de menús usando match-case"""
    current_state = MenuState.MAIN
    
    try:
        while current_state != MenuState.EXIT:
            action = None
            
            match current_state:
                case MenuState.MAIN:
                    # Limpiar pantalla y mostrar encabezado principal
                    clear_screen()
                    print("=" * 60)
                    print("🖥️  SISTEMA DE MONITOREO DISTRIBUIDO")
                    print("=" * 60)
                    choice = get_user_input_interactive()
                    if choice:  # Si no es None (cancelación)
                        action, current_state = process_main_menu_input(choice)
                    
                case MenuState.AGENTS:
                    clear_screen()
                    print("=" * 60)
                    print("🖥️  SISTEMA DE MONITOREO DISTRIBUIDO")
                    print("=" * 60)
                    choice = get_agents_input_interactive()
                    if choice:
                        action, current_state = process_agents_menu_input(choice)
                    
                case MenuState.LOCAL_SYSTEM:
                    clear_screen()
                    print("=" * 60)
                    print("🖥️  SISTEMA DE MONITOREO DISTRIBUIDO")
                    print("=" * 60)
                    choice = get_local_system_input_interactive()
                    if choice:
                        action, current_state = process_local_system_input(choice)
            
            # Ejecutar acción si existe
            if action and action != MenuAction.EXIT:
                execute_action(action)
        
        # Manejar salida
        handle_exit()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Salida interrumpida por el usuario")
        handle_exit()

if __name__ == "__main__":
    run_menu_system()
#!/usr/bin/env python3
"""
Funciones para manejo de agentes en background
"""

import os
import sys
import threading
import time

# Variables globales para mantener estado de agentes
ping_running = False
ssh_running = False
monitor_running = False

def clear_screen():
    """Limpia la pantalla de la consola"""
    os.system('cls' if os.name == 'nt' else 'clear')

def start_ping_agent():
    """Inicia el agente de ping en background"""
    global ping_running
    
    if ping_running:
        print("ℹ️ El agente de ping ya está ejecutándose")
        return
    
    try:
        print("🏓 Iniciando agente de ping en segundo plano...")
        
        # Importar e inicializar logging
        from agents.ag_ping import setup_logging, iniciar_background_ping, mostrar_estado_ping
        setup_logging()
        
        # Iniciar en background
        iniciar_background_ping()
        ping_running = True
        
        time.sleep(2)  # Dar tiempo a que inicie
        print("✅ Agente de ping iniciado exitosamente")
        print("📊 Monitoreando conectividad cada 30 segundos")
        print("📄 Logs disponibles en: ./logs/agente_ping.log")
        
        # Mostrar estado
        mostrar_estado_ping()
        
    except ImportError as e:
        print(f"❌ Error importando agente de ping: {e}")
    except Exception as e:
        print(f"❌ Error iniciando agente de ping: {e}")
        import traceback
        traceback.print_exc()
        ping_running = False

def stop_ping_agent():
    """Detiene el agente de ping"""
    global ping_running
    
    if not ping_running:
        print("ℹ️ El agente de ping no está ejecutándose")
        return
    
    try:
        print("🛑 Deteniendo agente de ping...")
        
        from agents.ag_ping import detener_monitoreo_ping
        detener_monitoreo_ping()
        
        ping_running = False
        print("✅ Agente de ping detenido")
        
    except Exception as e:
        print(f"❌ Error deteniendo agente de ping: {e}")

def start_ssh_agent():
    """Inicia el agente SSH en background"""
    global ssh_running
    
    if ssh_running:
        print("ℹ️ El agente SSH ya está ejecutándose")
        return
    
    try:
        print("🔐 Iniciando agente SSH en segundo plano...")
        
        # Importar e inicializar logging
        from agents.ag_ssh import setup_logging_ssh, iniciar_background_ssh, mostrar_estado_ssh
        setup_logging_ssh()
        
        # Iniciar en background
        iniciar_background_ssh()
        ssh_running = True
        
        time.sleep(2)  # Dar tiempo a que inicie
        print("✅ Agente SSH iniciado exitosamente")
        print("📊 Monitoreando equipos remotos via SSH")
        print("📄 Logs disponibles en: ./logs/agente_ssh.log")
        
        # Mostrar estado
        mostrar_estado_ssh()
        
    except ImportError as e:
        print(f"❌ Error importando agente SSH: {e}")
    except Exception as e:
        print(f"❌ Error iniciando agente SSH: {e}")
        import traceback
        traceback.print_exc()
        ssh_running = False

def stop_ssh_agent():
    """Detiene el agente SSH"""
    global ssh_running
    
    if not ssh_running:
        print("ℹ️ El agente SSH no está ejecutándose")
        return
    
    try:
        print("🛑 Deteniendo agente SSH...")
        
        from agents.ag_ssh import detener_monitoreo_ssh
        detener_monitoreo_ssh()
        
        ssh_running = False
        print("✅ Agente SSH detenido")
        
    except Exception as e:
        print(f"❌ Error deteniendo agente SSH: {e}")

def start_monitor_distribuido():
    """Inicia el monitor distribuido en background"""
    global monitor_running
    
    if monitor_running:
        print("ℹ️ El monitor distribuido ya está ejecutándose")
        return
    
    try:
        print("📡 Iniciando monitor distribuido en segundo plano...")
        
        # Importar funciones del monitor
        from core.config_manager import crear_monitor_distribuido, iniciar_monitoreo
        
        # Crear monitor
        monitor = crear_monitor_distribuido()
        
        # Iniciar en background usando thread
        def run_monitor():
            global monitor_running
            try:
                monitor_running = True
                iniciar_monitoreo(monitor)
            except Exception as e:
                print(f"❌ Error en monitor: {e}")
            finally:
                monitor_running = False
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        time.sleep(2)  # Dar tiempo a que inicie
        
        if monitor_running:
            print("✅ Monitor distribuido iniciado exitosamente")
            print("📊 Monitoreando CPU, memoria y temperatura")
            print("📄 Logs disponibles en: ./logs/monitor_distribuido.log")
        else:
            print("❌ El monitor no se pudo iniciar correctamente")
        
    except ImportError as e:
        print(f"❌ Error importando monitor distribuido: {e}")
    except Exception as e:
        print(f"❌ Error iniciando monitor distribuido: {e}")
        import traceback
        traceback.print_exc()
        monitor_running = False

def stop_monitor_distribuido():
    """Detiene el monitor distribuido"""
    global monitor_running
    
    if not monitor_running:
        print("ℹ️ El monitor distribuido no está ejecutándose")
        return
    
    try:
        print("🛑 Deteniendo monitor distribuido...")
        
        # El monitor se detiene cambiando la variable global
        monitor_running = False
        print("✅ Monitor distribuido detenido")
        print("📊 Se detendrá en la próxima iteración")
        
    except Exception as e:
        print(f"❌ Error deteniendo monitor distribuido: {e}")

def show_agents_status():
    """Muestra el estado de todos los agentes"""
    global ping_running, ssh_running, monitor_running
    
    clear_screen()
    print("📊 ESTADO DE AGENTES")
    print("=" * 60)
    
    # Estado general
    print(f"📊 Estado general:")
    print(f"  • Agente Ping: {'🟢 ACTIVO' if ping_running else '🔴 INACTIVO'}")
    print(f"  • Agente SSH: {'🟢 ACTIVO' if ssh_running else '🔴 INACTIVO'}")
    print(f"  • Monitor Distribuido: {'🟢 ACTIVO' if monitor_running else '🔴 INACTIVO'}")
    print()
    
    # Detalles del agente de ping
    if ping_running:
        print("🏓 AGENTE DE PING:")
        try:
            from agents.ag_ping import mostrar_estado_ping
            mostrar_estado_ping()
        except Exception as e:
            print(f"  ❌ Error obteniendo estado: {e}")
        print()
    
    # Detalles del agente SSH
    if ssh_running:
        print("🔐 AGENTE SSH:")
        try:
            from agents.ag_ssh import mostrar_estado_ssh
            mostrar_estado_ssh()
        except Exception as e:
            print(f"  ❌ Error obteniendo estado: {e}")
        print()
    
    # Información de logs
    print("📄 ARCHIVOS DE LOG:")
    log_files = ["./logs/agente_ping.log", "./logs/agente_ssh.log", "./logs/monitor_distribuido.log"]
    for log_file in log_files:
        exists = "✅" if os.path.exists(log_file) else "❌"
        print(f"  {exists} {log_file}")
    
    print("=" * 60)

def handle_exit():
    """Maneja la salida del sistema deteniendo agentes activos"""
    global ping_running, ssh_running, monitor_running
    
    print("\n🛑 Cerrando sistema...")
    
    # Detener agentes activos
    if ping_running:
        print("🛑 Deteniendo agente de ping...")
        try:
            from agents.ag_ping import detener_monitoreo_ping
            detener_monitoreo_ping()
        except:
            pass
        ping_running = False
    
    if ssh_running:
        print("🛑 Deteniendo agente SSH...")
        try:
            from agents.ag_ssh import detener_monitoreo_ssh
            detener_monitoreo_ssh()
        except:
            pass
        ssh_running = False
    
    if monitor_running:
        print("🛑 Deteniendo monitor distribuido...")
        monitor_running = False
    
    print("\n👋 ¡Hasta luego!")
    print("📊 Todos los agentes han sido detenidos")
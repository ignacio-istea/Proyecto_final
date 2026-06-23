#!/usr/bin/env python3
"""
Agente de Ping - Sistema de Monitoreo Distribuido
Monitorea conectividad de dispositivos y genera alarmas por conexión perdida
"""

import json
import time
import logging
import subprocess
import platform
from datetime import datetime
from pathlib import Path
import schedule
import threading


# Variables globales para el estado del agente
_agente_running = False
_agente_thread = None
_dispositivos_offline = set()
_logger = None

def setup_logging():
    """Configura el sistema de logging"""
    global _logger
    Path("./logs").mkdir(exist_ok=True)
    
    # Configurar logging solo para archivo, sin consola
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('./logs/agente_ping.log')
            # Removido StreamHandler() para evitar salida a consola
        ]
    )
    _logger = logging.getLogger(__name__)
    
def cargar_config_ping(config_path="config.json"):
    """Carga la configuración desde JSON"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        if _logger:
            _logger.error(f"Error cargando configuración: {e}")
        return None

def hacer_ping(ip, timeout=3):
    """Ejecuta ping a una IP específica"""
    try:
        sistema = platform.system().lower()
        
        if sistema == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
        else:  # Unix/Linux/macOS
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        if _logger:
            _logger.error(f"Error ejecutando ping a {ip}: {e}")
        return False
    
def generar_alarma_conexion(equipo, estado):
    """Genera alarma de conexión perdida o restaurada"""
    try:
        # Cargar alarmas activas
        alarmas_file = "./logs/alarmas_activas.json"
        Path(alarmas_file).parent.mkdir(exist_ok=True)
        
        try:
            with open(alarmas_file, 'r') as f:
                alarmas = json.load(f)
        except:
            alarmas = {}
        
        alarma_id = f"conexion_{equipo['nombre']}"
        timestamp = datetime.now().isoformat()
        
        if estado == "offline":
            # Dispositivo perdió conexión
            if alarma_id not in alarmas:
                alarma = {
                    "id": alarma_id,
                    "equipo": equipo['nombre'],
                    "ip": equipo['ip'],
                    "tipo": "conexion",
                    "severidad": "critico",
                    "mensaje": f"Conexión perdida con {equipo['nombre']} ({equipo['ip']})",
                    "timestamp_inicio": timestamp,
                    "estado": "activo",
                    "eventos": [{
                        "timestamp": timestamp,
                        "evento": "conexion_perdida",
                        "detalle": "Dispositivo no responde a ping"
                    }]
                }
                
                alarmas[alarma_id] = alarma
                if _logger:
                    _logger.warning(f"🔴 CONEXIÓN PERDIDA: {equipo['nombre']} ({equipo['ip']})")
                
                # Notificación del sistema
                enviar_notificacion_ping(
                    f"Conexión Perdida - {equipo['nombre']}",
                    f"El dispositivo {equipo['nombre']} ({equipo['ip']}) no responde"
                )
        
        elif estado == "online":
            # Dispositivo restauró conexión
            if alarma_id in alarmas:
                alarmas[alarma_id]["estado"] = "resuelto"
                alarmas[alarma_id]["timestamp_fin"] = timestamp
                alarmas[alarma_id]["eventos"].append({
                    "timestamp": timestamp,
                    "evento": "conexion_restaurada",
                    "detalle": "Dispositivo vuelve a responder a ping"
                })
                
                if _logger:
                    _logger.info(f"🟢 CONEXIÓN RESTAURADA: {equipo['nombre']} ({equipo['ip']})")
                
                # Notificación del sistema
                enviar_notificacion_ping(
                    f"Conexión Restaurada - {equipo['nombre']}",
                    f"El dispositivo {equipo['nombre']} ({equipo['ip']}) vuelve a responder"
                )
        
        # Guardar alarmas
        with open(alarmas_file, 'w') as f:
            json.dump(alarmas, f, indent=2)
            
    except Exception as e:
        if _logger:
            _logger.error(f"Error generando alarma: {e}")

def enviar_notificacion_ping(titulo, mensaje):
    """Envía notificación del sistema"""
    try:
        sistema = platform.system().lower()
        
        if sistema == "darwin":  # macOS
            subprocess.run([
                "osascript", "-e", 
                f'display notification "{mensaje}" with title "{titulo}"'
            ], check=False, capture_output=True)
        
        elif sistema == "linux":
            subprocess.run([
                "notify-send", titulo, mensaje
            ], check=False, capture_output=True)
        
        elif sistema == "windows":
            subprocess.run([
                "powershell", "-Command",
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $toastXml = [xml] $template.GetXml(); $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{titulo}")) > $null; $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{mensaje}")) > $null; $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml); [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Sistema Monitoreo").Show($toast);'
            ], check=False, capture_output=True)
        
    except Exception as e:
        if _logger:
            _logger.error(f"Error enviando notificación: {e}")
    
def verificar_dispositivos():
    """Verifica conectividad de todos los dispositivos"""
    global _dispositivos_offline
    
    config = cargar_config_ping()
    if not config:
        return
    
    equipos = config.get('equipos', [])
    # Solo verificar equipos que tengan ping activo
    equipos_ping = [e for e in equipos if e.get('ping_activo', True)]
    
    for equipo in equipos_ping:
        try:
            ip = equipo.get('ip')
            nombre = equipo.get('nombre')
            
            if ip == 'localhost' or ip == '127.0.0.1':
                # Localhost siempre está "online"
                if nombre in _dispositivos_offline:
                    _dispositivos_offline.remove(nombre)
                    generar_alarma_conexion(equipo, "online")
                continue
            
            ping_ok = hacer_ping(ip)
            
            if ping_ok:
                # Dispositivo online
                if nombre in _dispositivos_offline:
                    _dispositivos_offline.remove(nombre)
                    generar_alarma_conexion(equipo, "online")
                    if _logger:
                        _logger.info(f"✅ {nombre} ({ip}) - CONEXIÓN RESTAURADA")
            else:
                # Dispositivo offline
                if nombre not in _dispositivos_offline:
                    _dispositivos_offline.add(nombre)
                    generar_alarma_conexion(equipo, "offline")
                    if _logger:
                        _logger.warning(f"❌ {nombre} ({ip}) - CONEXIÓN PERDIDA")
                    
        except Exception as e:
            if _logger:
                _logger.error(f"Error verificando {equipo.get('nombre', 'desconocido')}: {e}")

def job_verificacion_ping():
    """Job que se ejecuta cada 30 segundos"""
    try:
        verificar_dispositivos()
    except Exception as e:
        if _logger:
            _logger.error(f"Error en job de verificación: {e}")
    
def iniciar_monitoreo_ping():
    """Inicia el monitoreo de ping en background"""
    global _agente_running
    
    if _agente_running:
        if _logger:
            _logger.info("El agente de ping ya está ejecutándose")
        return
    
    if _logger:
        _logger.info("🚀 Iniciando Agente de Ping...")
    _agente_running = True
    
    # Programar verificación cada 30 segundos
    schedule.every(30).seconds.do(job_verificacion_ping)
    
    # Ejecutar primera verificación inmediatamente
    job_verificacion_ping()
    
    # Loop principal
    while _agente_running:
        schedule.run_pending()
        time.sleep(1)
    
    if _logger:
        _logger.info("🛑 Agente de Ping detenido")

def detener_monitoreo_ping():
    """Detiene el monitoreo"""
    global _agente_running
    if _logger:
        _logger.info("Deteniendo Agente de Ping...")
    _agente_running = False

def iniciar_background_ping():
    """Inicia el agente en un hilo separado"""
    global _agente_thread
    
    if _agente_thread and _agente_thread.is_alive():
        if _logger:
            _logger.info("El agente ya está ejecutándose en background")
        return
    
    _agente_thread = threading.Thread(target=iniciar_monitoreo_ping, daemon=True)
    _agente_thread.start()
    if _logger:
        _logger.info("Agente de Ping iniciado en background")
    
def mostrar_estado_ping():
    """Muestra el estado actual del agente"""
    config = cargar_config_ping()
    if not config:
        print("❌ No se pudo cargar la configuración")
        return
    
    equipos = config.get('equipos', [])
    equipos_ping = [e for e in equipos if e.get('ping_activo', True)]
    equipos_deshabilitados = [e for e in equipos if not e.get('ping_activo', True)]
    
    print(f"\n📡 ESTADO DEL AGENTE DE PING")
    print("=" * 50)
    print(f"Estado: {'🟢 ACTIVO' if _agente_running else '🔴 INACTIVO'}")
    print(f"Equipos con ping habilitado: {len(equipos_ping)}")
    print(f"Equipos offline: {len(_dispositivos_offline)}")
    
    if equipos_ping:
        print(f"\n📋 EQUIPOS MONITOREADOS:")
        for equipo in equipos_ping:
            nombre = equipo.get('nombre')
            ip = equipo.get('ip')
            estado = "🔴 OFFLINE" if nombre in _dispositivos_offline else "🟢 ONLINE"
            print(f"  • {nombre} ({ip}) - {estado}")
    
    if equipos_deshabilitados:
        print(f"\n🚫 EQUIPOS CON PING DESHABILITADO:")
        for equipo in equipos_deshabilitados:
            print(f"  • {equipo.get('nombre')} ({equipo.get('ip')}) - PING DESHABILITADO")

def get_ping_running():
    """Obtiene el estado de ejecución del agente"""
    return _agente_running


def main():
    """Función principal para ejecutar el agente independientemente"""
    print("🚀 Iniciando Agente de Ping...")
    
    setup_logging()
    
    try:
        # Mostrar estado inicial
        mostrar_estado_ping()
        print("\nPresiona Ctrl+C para detener...")
        
        # Iniciar monitoreo
        iniciar_monitoreo_ping()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo agente...")
        detener_monitoreo_ping()
        print("👋 Agente de Ping detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
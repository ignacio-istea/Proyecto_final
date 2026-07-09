#!/usr/bin/env python3
"""
Agente SSH - Sistema de Monitoreo Distribuido
Se conecta a dispositivos remotos via SSH para obtener métricas del sistema
"""

import json
import time
import logging
import subprocess
import platform
from datetime import datetime
from pathlib import Path
import paramiko
import schedule
import threading
import warnings

# Suprimir warnings de paramiko
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*TripleDES.*")


# Variables globales para el estado del agente SSH
_ssh_agente_running = False
_ssh_agente_thread = None
_ssh_conexiones_activas = {}
_ssh_logger = None

def setup_logging_ssh():
    """Configura el logger propio del agente SSH (solo archivo, sin consola)"""
    global _ssh_logger
    Path("./logs").mkdir(exist_ok=True)
    _ssh_logger = logging.getLogger('agente_ssh')
    _ssh_logger.setLevel(logging.INFO)
    _ssh_logger.propagate = False
    if not _ssh_logger.handlers:
        handler = logging.FileHandler('./logs/agente_ssh.log', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        _ssh_logger.addHandler(handler)
    
def cargar_config_ssh(config_path="config.json"):
    """Carga la configuración desde JSON"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error cargando configuración: {e}")
        return None

def conectar_ssh(equipo):
    """Establece conexión SSH con un equipo"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ip = equipo.get('ip')
        puerto = equipo.get('port', 22)
        usuario = equipo.get('user')
        key_path = equipo.get('ssh_key_path')
        
        # Conectar usando clave SSH
        if key_path and Path(key_path).exists():
            ssh.connect(
                hostname=ip,
                port=puerto,
                username=usuario,
                key_filename=key_path,
                timeout=10
            )
        else:
            if _ssh_logger:
                _ssh_logger.warning(f"Clave SSH no encontrada para {equipo['nombre']}: {key_path}")
            return None
        
        return ssh
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error conectando SSH a {equipo['nombre']} ({ip}): {e}")
        return None

def ejecutar_comando_ssh_agente(ssh, comando):
    """Ejecuta un comando via SSH y retorna la salida"""
    try:
        stdin, stdout, stderr = ssh.exec_command(comando, timeout=15)
        salida = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        
        if error and "command not found" not in error.lower():
            if _ssh_logger:
                _ssh_logger.debug(f"Error en comando SSH: {error}")
        
        return salida
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error ejecutando comando SSH: {e}")
        return None
    
def obtener_cpu_remoto(ssh):
    """Obtiene el uso de CPU del dispositivo remoto"""
    try:
        # Intentar varios métodos para obtener CPU
        comandos = [
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'",
            "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {print usage}'",
            "iostat -c 1 1 | tail -1 | awk '{print 100-$6}'",
            "vmstat 1 2 | tail -1 | awk '{print 100-$15}'"
        ]
        
        for comando in comandos:
            resultado = ejecutar_comando_ssh_agente(ssh, comando)
            if resultado:
                try:
                    cpu = float(resultado.split()[0])
                    if 0 <= cpu <= 100:
                        return cpu
                except (ValueError, IndexError):
                    continue
        
        # Fallback: usar uptime load average
        resultado = ejecutar_comando_ssh_agente(ssh, "uptime")
        if resultado and "load average:" in resultado:
            try:
                load = float(resultado.split("load average:")[-1].split(",")[0].strip())
                # Convertir load a porcentaje aproximado (asumiendo 1 core)
                cpu = min(load * 100, 100)
                return cpu
            except (ValueError, IndexError):
                pass
        
        return None
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error obteniendo CPU remoto: {e}")
        return None

def obtener_memoria_remota(ssh):
    """Obtiene el uso de memoria del dispositivo remoto"""
    try:
        # Comando para obtener memoria
        comando = "free | grep Mem | awk '{print ($3/$2) * 100.0}'"
        resultado = ejecutar_comando_ssh_agente(ssh, comando)
        
        if resultado:
            try:
                memoria = float(resultado.strip())
                return memoria
            except ValueError:
                pass
        
        # Fallback: usar /proc/meminfo
        comando = "cat /proc/meminfo | grep -E '^(MemTotal|MemAvailable)' | awk '{print $2}'"
        resultado = ejecutar_comando_ssh_agente(ssh, comando)
        
        if resultado:
            try:
                lineas = resultado.strip().split('\n')
                if len(lineas) >= 2:
                    total = float(lineas[0])
                    disponible = float(lineas[1])
                    usado = total - disponible
                    memoria = (usado / total) * 100
                    return memoria
            except (ValueError, IndexError):
                pass
        
        return None
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error obteniendo memoria remota: {e}")
        return None

def obtener_temperatura_remota(ssh):
    """Obtiene la temperatura del dispositivo remoto"""
    try:
        # Intentar diferentes métodos según el tipo de dispositivo
        comandos_temperatura = [
            # Raspberry Pi
            "vcgencmd measure_temp | grep -o '[0-9]*\\.[0-9]*'",
            # Sistemas con sensors (lm-sensors)
            "sensors | grep -E 'Core 0|Package id 0|temp1' | head -1 | grep -o '[0-9]*\\.[0-9]*°C' | head -1 | sed 's/°C//'",
            # Sistemas con sensors (alternativo)
            "sensors | grep -i temp | head -1 | grep -o '[0-9]*\\.[0-9]*' | head -1",
            # Archivo directo del kernel (algunos sistemas Linux)
            "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000}'",
            "cat /sys/class/thermal/thermal_zone1/temp 2>/dev/null | awk '{print $1/1000}'",
            # macOS (si está disponible via SSH)
            "sudo powermetrics --samplers smc_temp -n 1 2>/dev/null | grep 'CPU die temperature' | awk '{print $4}'"
        ]
        
        for comando in comandos_temperatura:
            resultado = ejecutar_comando_ssh_agente(ssh, comando)
            if resultado:
                try:
                    temp = float(resultado.strip())
                    # Validar rango razonable de temperatura (0-100°C)
                    if 0 <= temp <= 100:
                        return temp
                except ValueError:
                    continue
        
        # Si no se puede obtener temperatura real, estimar basada en CPU
        cpu = obtener_cpu_remoto(ssh)
        if cpu is not None:
            # Estimación básica: 30°C base + (CPU/4)
            temp_estimada = 30 + (cpu / 4)
            if _ssh_logger:
                _ssh_logger.debug(f"Temperatura estimada basada en CPU: {temp_estimada:.1f}°C")
            return temp_estimada
        
        return None
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error obteniendo temperatura remota: {e}")
        return None
    
def obtener_metricas_locales_ssh():
    """Obtiene métricas del equipo local usando comandos del sistema"""
    try:
        metricas = {}
        
        # CPU local
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = "top -l 1 | grep 'CPU usage' | awk '{print $3}' | sed 's/%//' | sed 's/user//' | head -1"
            else:  # Linux
                cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                metricas['cpu'] = float(result.stdout.strip())
        except:
            metricas['cpu'] = 0.0
        
        # Memoria local
        try:
            if platform.system() == "Darwin":  # macOS
                # Simplificado: usar estimación para macOS
                metricas['memoria'] = 45.0
            else:  # Linux
                cmd = "free | grep Mem | awk '{print ($3/$2) * 100.0}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    metricas['memoria'] = float(result.stdout.strip())
        except:
            metricas['memoria'] = 0.0
        
        # Temperatura local
        try:
            if platform.system() == "Darwin":  # macOS
                # Usar estimación basada en CPU para macOS
                metricas['temperatura'] = 35 + (metricas.get('cpu', 0) / 3)
            else:  # Linux
                cmd = "sensors | grep -i temp | head -1 | grep -o '[0-9]*\\.[0-9]*' | head -1"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    metricas['temperatura'] = float(result.stdout.strip())
                else:
                    metricas['temperatura'] = 35 + (metricas.get('cpu', 0) / 3)
        except:
            metricas['temperatura'] = 35.0
        
        return metricas
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error obteniendo métricas locales: {e}")
        return {'cpu': 0.0, 'memoria': 0.0, 'temperatura': 35.0}
    
def procesar_alarmas_ssh(equipo, metricas):
    """Procesa las métricas y genera alarmas via data_manager"""
    try:
        from ui.dashboard_modules.data_manager import registrar_evento

        config = cargar_config_ssh()
        if not config:
            return

        umbrales = config.get('umbrales_por_equipo', {}).get(equipo['nombre'], {})
        if not umbrales:
            return

        for metrica, valor in metricas.items():
            if metrica not in umbrales:
                continue

            u = umbrales[metrica]
            clear_t   = u.get('clear',   70)
            warning_t = u.get('warning', 80)
            critico_t = u.get('critico', 95)

            if valor >= critico_t:
                registrar_evento(equipo['nombre'], metrica, 'critico', valor, critico_t)
                if _ssh_logger:
                    _ssh_logger.warning(f"🚨 {equipo['nombre']} - {metrica} CRÍTICO: {valor:.1f}")
            elif valor >= warning_t:
                registrar_evento(equipo['nombre'], metrica, 'warning', valor, warning_t)
                if _ssh_logger:
                    _ssh_logger.warning(f"⚠️  {equipo['nombre']} - {metrica} WARNING: {valor:.1f}")
            elif valor <= clear_t:
                registrar_evento(equipo['nombre'], metrica, 'clear', valor, clear_t)
                if _ssh_logger:
                    _ssh_logger.info(f"✅ {equipo['nombre']} - {metrica} normalizado: {valor:.1f}")

    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error procesando alarmas para {equipo['nombre']}: {e}")

def monitorear_equipo_ssh(equipo):
    """Monitorea un equipo específico"""
    try:
        nombre = equipo.get('nombre')
        ip = equipo.get('ip')
        
        if ip == 'localhost' or ip == '127.0.0.1':
            # Monitoreo local
            metricas = obtener_metricas_locales_ssh()
            if _ssh_logger:
                _ssh_logger.info(f"📊 {nombre} (local) - CPU: {metricas['cpu']:.1f}% | Mem: {metricas['memoria']:.1f}% | Temp: {metricas['temperatura']:.1f}°C")
        else:
            # Monitoreo remoto via SSH
            ssh = conectar_ssh(equipo)
            if not ssh:
                if _ssh_logger:
                    _ssh_logger.error(f"❌ No se pudo conectar a {nombre} ({ip})")
                return
            
            try:
                metricas = {}
                
                # Obtener métricas remotas
                cpu = obtener_cpu_remoto(ssh)
                memoria = obtener_memoria_remota(ssh)
                temperatura = obtener_temperatura_remota(ssh)
                
                metricas['cpu'] = cpu if cpu is not None else 0.0
                metricas['memoria'] = memoria if memoria is not None else 0.0
                metricas['temperatura'] = temperatura if temperatura is not None else 35.0
                
                if _ssh_logger:
                    _ssh_logger.info(f"📊 {nombre} ({ip}) - CPU: {metricas['cpu']:.1f}% | Mem: {metricas['memoria']:.1f}% | Temp: {metricas['temperatura']:.1f}°C")
                
            finally:
                ssh.close()
        
        # Procesar alarmas
        procesar_alarmas_ssh(equipo, metricas)
        
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error monitoreando {equipo.get('nombre', 'desconocido')}: {e}")
    
def job_monitoreo_ssh():
    """Job que se ejecuta cada intervalo configurado"""
    try:
        config = cargar_config_ssh()
        if not config:
            return
        
        equipos = config.get('equipos', [])
        # Solo monitorear equipos que no sean de tipo 'externo' y tengan SSH habilitado
        equipos_monitoreables = [e for e in equipos 
                               if e.get('tipo') != 'externo' 
                               and e.get('ssh_activo', True)]
        
        if not equipos_monitoreables:
            if _ssh_logger:
                _ssh_logger.warning("No hay equipos configurados para monitoreo SSH")
            return
        
        if _ssh_logger:
            _ssh_logger.info(f"🔍 Monitoreando {len(equipos_monitoreables)} equipos...")
        
        for equipo in equipos_monitoreables:
            monitorear_equipo_ssh(equipo)
            
    except Exception as e:
        if _ssh_logger:
            _ssh_logger.error(f"Error en job de monitoreo: {e}")
    
def iniciar_monitoreo_ssh():
    """Inicia el monitoreo SSH en background"""
    global _ssh_agente_running
    
    if _ssh_agente_running:
        if _ssh_logger:
            _ssh_logger.info("El agente SSH ya está ejecutándose")
        return
    
    config = cargar_config_ssh()
    if not config:
        if _ssh_logger:
            _ssh_logger.error("No se pudo cargar configuración")
        return
    
    intervalo = config.get('monitoreo', {}).get('intervalo_segundos', 30)
    
    if _ssh_logger:
        _ssh_logger.info(f"🚀 Iniciando Agente SSH (intervalo: {intervalo}s)...")
    _ssh_agente_running = True
    
    # Programar monitoreo
    schedule.every(intervalo).seconds.do(job_monitoreo_ssh)
    
    # Ejecutar primera verificación inmediatamente
    job_monitoreo_ssh()
    
    # Loop principal
    while _ssh_agente_running:
        schedule.run_pending()
        time.sleep(1)
    
    if _ssh_logger:
        _ssh_logger.info("🛑 Agente SSH detenido")

def detener_monitoreo_ssh():
    """Detiene el monitoreo"""
    global _ssh_agente_running
    if _ssh_logger:
        _ssh_logger.info("Deteniendo Agente SSH...")
    _ssh_agente_running = False

def iniciar_background_ssh():
    """Inicia el agente en un hilo separado"""
    global _ssh_agente_thread
    
    if _ssh_agente_thread and _ssh_agente_thread.is_alive():
        if _ssh_logger:
            _ssh_logger.info("El agente SSH ya está ejecutándose en background")
        return
    
    _ssh_agente_thread = threading.Thread(target=iniciar_monitoreo_ssh, daemon=True)
    _ssh_agente_thread.start()
    if _ssh_logger:
        _ssh_logger.info("Agente SSH iniciado en background")
    
def mostrar_estado_ssh():
    """Muestra el estado actual del agente"""
    config = cargar_config_ssh()
    if not config:
        print("❌ No se pudo cargar la configuración")
        return
    
    equipos = config.get('equipos', [])
    equipos_monitoreables = [e for e in equipos 
                           if e.get('tipo') != 'externo' 
                           and e.get('ssh_activo', True)]
    equipos_deshabilitados = [e for e in equipos 
                            if e.get('tipo') != 'externo' 
                            and not e.get('ssh_activo', True)]
    
    print(f"\n🔧 ESTADO DEL AGENTE SSH")
    print("=" * 50)
    print(f"Estado: {'🟢 ACTIVO' if _ssh_agente_running else '🔴 INACTIVO'}")
    print(f"Equipos con SSH habilitado: {len(equipos_monitoreables)}")
    print(f"Intervalo: {config.get('monitoreo', {}).get('intervalo_segundos', 30)}s")
    
    if equipos_monitoreables:
        print(f"\n📋 EQUIPOS PARA MONITOREO SSH:")
        for equipo in equipos_monitoreables:
            nombre = equipo.get('nombre')
            ip = equipo.get('ip')
            tipo = equipo.get('tipo', 'unknown')
            estado = "🏠 LOCAL" if ip in ['localhost', '127.0.0.1'] else "🌐 REMOTO"
            print(f"  • {nombre} ({ip}) - {tipo.upper()} - {estado}")
    
    if equipos_deshabilitados:
        print(f"\n🚫 EQUIPOS CON SSH DESHABILITADO:")
        for equipo in equipos_deshabilitados:
            print(f"  • {equipo.get('nombre')} ({equipo.get('ip')}) - SSH DESHABILITADO")

def get_ssh_running():
    """Obtiene el estado de ejecución del agente SSH"""
    return _ssh_agente_running


def main():
    """Función principal para ejecutar el agente independientemente"""
    print("🚀 Iniciando Agente SSH...")
    
    setup_logging_ssh()
    
    try:
        # Mostrar estado inicial
        mostrar_estado_ssh()
        print("\nPresiona Ctrl+C para detener...")
        
        # Iniciar monitoreo
        iniciar_monitoreo_ssh()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo agente...")
        detener_monitoreo_ssh()
        print("👋 Agente SSH detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
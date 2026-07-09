#!/usr/bin/env python3
"""
Módulo de obtención de métricas del sistema

"""

import subprocess
import platform
import logging
from datetime import datetime
import paramiko

def obtener_metricas_locales():
    """Obtiene métricas del sistema local"""
    return {
        'cpu': _obtener_cpu_subprocess(),
        'memoria': _obtener_memoria_subprocess(), 
        'temperatura': _obtener_temperatura_subprocess(),
        'timestamp': datetime.now().isoformat()
    }

def _obtener_cpu_subprocess():
    """Obtiene CPU usando comandos del sistema"""
    try:
        sistema = platform.system()
        
        if sistema == "Darwin":  # macOS
            result = subprocess.run(['iostat', '-c', '1'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 3:
                    cpu_line = lines[-1].split()
                    if len(cpu_line) >= 6:
                        idle = float(cpu_line[5])
                        return 100.0 - idle
            
            # Fallback: usar top
            result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'CPU usage:' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if '%' in part and i > 0:
                                return float(part.replace('%', ''))
        
        elif sistema == "Linux":
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                cpu_times = [int(x) for x in line.split()[1:8]]
                idle_time = cpu_times[3]
                total_time = sum(cpu_times)
                cpu_percent = 100 * (1 - idle_time / total_time)
                return cpu_percent
        
        # Fallback: usar psutil si está disponible
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            pass
            
    except Exception as e:
        logging.warning(f"Error obteniendo CPU: {e}")
    
    return 0.0
    
def _obtener_memoria_subprocess():
    """Obtiene memoria usando comandos del sistema"""
    try:
        sistema = platform.system()
        
        if sistema == "Darwin":  # macOS
            result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                page_size = 4096
                
                total_pages = 0
                free_pages = 0
                
                for line in lines:
                    if 'Pages free:' in line:
                        free_pages = int(line.split(':')[1].strip().replace('.', ''))
                    elif 'Pages active:' in line:
                        total_pages += int(line.split(':')[1].strip().replace('.', ''))
                    elif 'Pages inactive:' in line:
                        total_pages += int(line.split(':')[1].strip().replace('.', ''))
                    elif 'Pages speculative:' in line:
                        total_pages += int(line.split(':')[1].strip().replace('.', ''))
                    elif 'Pages wired down:' in line:
                        total_pages += int(line.split(':')[1].strip().replace('.', ''))
                
                total_pages += free_pages
                if total_pages > 0:
                    used_pages = total_pages - free_pages
                    return (used_pages / total_pages) * 100
        
        elif sistema == "Linux":
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            total = 0
            available = 0
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    total = int(line.split()[1])
                elif line.startswith('MemAvailable:'):
                    available = int(line.split()[1])
            
            if total > 0:
                used = total - available
                return (used / total) * 100
        
        # Fallback: usar psutil si está disponible
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            pass
            
    except Exception as e:
        logging.warning(f"Error obteniendo memoria: {e}")
    
    return 0.0
    
def _obtener_temperatura_subprocess():
    """Obtiene temperatura usando comandos del sistema"""
    try:
        sistema = platform.system()
        
        if sistema == "Darwin":  # macOS
            # Intentar powermetrics
            try:
                result = subprocess.run(['sudo', '-n', 'powermetrics', '-n', '1', '-s', 'smc'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'CPU die temperature' in line:
                            temp_str = line.split(':')[1].strip()
                            temp = float(temp_str.replace('C', '').strip())
                            return temp
            except:
                pass
            
            # Intentar con istats
            try:
                result = subprocess.run(['istats', 'cpu', 'temp'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '°C' in line:
                            temp_str = line.split('°C')[0].split()[-1]
                            return float(temp_str)
            except:
                pass
            
            # Intentar osx-cpu-temp
            try:
                result = subprocess.run(['osx-cpu-temp'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    temp_str = result.stdout.strip().replace('°C', '')
                    return float(temp_str)
            except:
                pass
            
            # Simular temperatura basada en CPU
            cpu_percent = _obtener_cpu_subprocess()
            base_temp = 35.0
            temp_factor = cpu_percent * 0.3
            return min(base_temp + temp_factor, 85.0)
        
        elif sistema == "Linux":
            # Intentar leer sensores térmicos
            thermal_paths = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/thermal/thermal_zone1/temp',
                '/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp*_input'
            ]
            
            for path in thermal_paths:
                try:
                    if '*' in path:
                        import glob
                        files = glob.glob(path)
                        if files:
                            path = files[0]
                    
                    with open(path, 'r') as f:
                        temp_raw = int(f.read().strip())
                        if temp_raw > 1000:
                            return temp_raw / 1000.0
                        else:
                            return temp_raw
                except:
                    continue
            
            # Intentar comando sensors
            try:
                result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Core 0:' in line or 'temp1:' in line:
                            parts = line.split()
                            for part in parts:
                                if '°C' in part:
                                    temp_str = part.replace('°C', '').replace('+', '')
                                    return float(temp_str)
            except:
                pass
        
        # Fallback: usar psutil si está disponible
        try:
            import psutil
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except ImportError:
            pass
            
    except Exception as e:
        logging.warning(f"Error obteniendo temperatura: {e}")
    
    # Fallback final: temperatura simulada
    try:
        cpu_percent = _obtener_cpu_subprocess()
        base_temp = 40.0
        temp_variation = cpu_percent * 0.25
        return min(base_temp + temp_variation, 75.0)
    except:
        return 45.0

def obtener_metricas_remotas(equipo):
    """Obtiene métricas de un equipo remoto via SSH"""
    from core.ssh_utils import crear_conexion_ssh, ejecutar_comando_ssh, cerrar_conexion_ssh
    
    ssh = crear_conexion_ssh(equipo)
    if not ssh:
        return {}
    
    metricas = {}
    nombre_equipo = equipo['nombre']
    
    try:
        # CPU
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | awk -F'%' '{print $1}'"
        cpu_result = ejecutar_comando_ssh(ssh, cpu_cmd, nombre_equipo)
        if cpu_result:
            try:
                metricas['cpu'] = float(cpu_result)
            except:
                metricas['cpu'] = 0.0
        
        # Memoria
        mem_cmd = "free | grep Mem | awk '{printf \"%.1f\", ($3/$2) * 100.0}'"
        mem_result = ejecutar_comando_ssh(ssh, mem_cmd, nombre_equipo)
        if mem_result:
            try:
                metricas['memoria'] = float(mem_result)
            except:
                metricas['memoria'] = 0.0
        
        # Temperatura
        temp_cmd = "sensors 2>/dev/null | grep -i core | head -1 | awk '{print $3}' | grep -o '[0-9.]*'"
        temp_result = ejecutar_comando_ssh(ssh, temp_cmd, nombre_equipo)
        if temp_result:
            try:
                metricas['temperatura'] = float(temp_result)
            except:
                metricas['temperatura'] = 0.0
        
        metricas['timestamp'] = datetime.now().isoformat()
        
    finally:
        cerrar_conexion_ssh(ssh)
    
    return metricas
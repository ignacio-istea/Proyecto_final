#!/usr/bin/env python3
"""
Módulo de obtención de métricas del sistema

"""

import subprocess
import platform
import logging
from datetime import datetime
import paramiko

_logger = logging.getLogger('metrics_collector')
_logger.propagate = False
if not _logger.handlers:
    from pathlib import Path
    Path('./logs').mkdir(exist_ok=True)
    _h = logging.FileHandler('./logs/monitor_distribuido.log', encoding='utf-8')
    _h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    _logger.addHandler(_h)
    _logger.setLevel(logging.INFO)

def obtener_metricas_locales():
    """Obtiene métricas del sistema local con manejo robusto de errores"""
    try:
        cpu = _obtener_cpu_subprocess()
        memoria = _obtener_memoria_subprocess()
        temperatura = _obtener_temperatura_subprocess()
        
        # Validar rangos de métricas
        if not (0 <= cpu <= 100):
            logging.warning(f"Valor de CPU fuera de rango: {cpu}")
            cpu = max(0, min(cpu, 100))
        
        if not (0 <= memoria <= 100):
            logging.warning(f"Valor de memoria fuera de rango: {memoria}")
            memoria = max(0, min(memoria, 100))
        
        if not (0 <= temperatura <= 100):
            logging.warning(f"Valor de temperatura fuera de rango: {temperatura}")
            temperatura = max(0, min(temperatura, 100))
        
        return {
            'cpu': cpu,
            'memoria': memoria,
            'temperatura': temperatura,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error obteniendo métricas locales: {e}")
        # Retornar valores por defecto en caso de error
        return {
            'cpu': 0.0,
            'memoria': 0.0,
            'temperatura': 35.0,
            'timestamp': datetime.now().isoformat()
        }

def _obtener_cpu_subprocess():
    """Obtiene CPU usando comandos del sistema con manejo robusto"""
    try:
        sistema = platform.system()
        
        if sistema == "Darwin":  # macOS
            # Intentar iostat primero
            try:
                result = subprocess.run(['iostat', '-c', '1'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 3:
                        cpu_line = lines[-1].split()
                        if len(cpu_line) >= 6:
                            idle = float(cpu_line[5])
                            cpu_val = 100.0 - idle
                            if 0 <= cpu_val <= 100:
                                return cpu_val
            except subprocess.CalledProcessError:
                logging.debug("iostat falló, intentando con top")
            except FileNotFoundError:
                logging.debug("iostat no disponible")
            
            # Fallback: usar top
            try:
                result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'CPU usage:' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if '%' in part and i > 0:
                                    cpu_val = float(part.replace('%', ''))
                                    if 0 <= cpu_val <= 100:
                                        return cpu_val
            except subprocess.CalledProcessError:
                logging.debug("top falló")
            except FileNotFoundError:
                logging.debug("top no disponible")
        
        elif sistema == "Linux":
            try:
                with open('/proc/stat', 'r') as f:
                    line = f.readline()
                    cpu_times = [int(x) for x in line.split()[1:8]]
                    idle_time = cpu_times[3]
                    total_time = sum(cpu_times)
                    if total_time > 0:
                        cpu_percent = 100 * (1 - idle_time / total_time)
                        if 0 <= cpu_percent <= 100:
                            return cpu_percent
            except (FileNotFoundError, PermissionError) as e:
                logging.debug(f"No se pudo leer /proc/stat: {e}")
            except (ValueError, IndexError) as e:
                logging.debug(f"Error procesando /proc/stat: {e}")
        
        # Fallback: usar psutil si está disponible
        try:
            import psutil
            cpu_val = psutil.cpu_percent(interval=1)
            if 0 <= cpu_val <= 100:
                return cpu_val
        except ImportError:
            logging.debug("psutil no disponible")
        except Exception as e:
            logging.debug(f"Error con psutil: {e}")
            
    except Exception as e:
        logging.warning(f"Error obteniendo CPU: {e}")
    
    # Valor por defecto
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
    """Obtiene métricas de un equipo remoto via SSH con manejo robusto"""
    from core.ssh_utils import crear_conexion_ssh, ejecutar_comando_ssh, cerrar_conexion_ssh
    
    metricas = {}
    ssh = None
    
    try:
        # Validar equipo
        if not equipo or 'nombre' not in equipo:
            logging.error("Equipo inválido para métricas remotas")
            return metricas
        
        nombre_equipo = equipo['nombre']
        
        # Crear conexión SSH
        ssh = crear_conexion_ssh(equipo)
        if not ssh:
            logging.error(f"No se pudo establecer conexión SSH con {nombre_equipo}")
            return metricas
        
        # Obtener CPU
        try:
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | awk -F'%' '{print $1}'"
            cpu_result = ejecutar_comando_ssh(ssh, cpu_cmd, nombre_equipo, timeout=10)
            if cpu_result:
                try:
                    cpu_val = float(cpu_result)
                    if 0 <= cpu_val <= 100:
                        metricas['cpu'] = cpu_val
                    else:
                        logging.warning(f"CPU fuera de rango para {nombre_equipo}: {cpu_val}")
                        metricas['cpu'] = 0.0
                except ValueError as e:
                    logging.warning(f"Error convirtiendo CPU para {nombre_equipo}: {e}")
                    metricas['cpu'] = 0.0
            else:
                metricas['cpu'] = 0.0
        except Exception as e:
            logging.error(f"Error obteniendo CPU para {nombre_equipo}: {e}")
            metricas['cpu'] = 0.0
        
        # Obtener Memoria
        try:
            mem_cmd = "free | grep Mem | awk '{printf \"%.1f\", ($3/$2) * 100.0}'"
            mem_result = ejecutar_comando_ssh(ssh, mem_cmd, nombre_equipo, timeout=10)
            if mem_result:
                try:
                    mem_val = float(mem_result)
                    if 0 <= mem_val <= 100:
                        metricas['memoria'] = mem_val
                    else:
                        logging.warning(f"Memoria fuera de rango para {nombre_equipo}: {mem_val}")
                        metricas['memoria'] = 0.0
                except ValueError as e:
                    logging.warning(f"Error convirtiendo memoria para {nombre_equipo}: {e}")
                    metricas['memoria'] = 0.0
            else:
                metricas['memoria'] = 0.0
        except Exception as e:
            logging.error(f"Error obteniendo memoria para {nombre_equipo}: {e}")
            metricas['memoria'] = 0.0
        
        # Obtener Temperatura
        try:
            temp_cmd = "sensors 2>/dev/null | grep -i core | head -1 | awk '{print $3}' | grep -o '[0-9.]*'"
            temp_result = ejecutar_comando_ssh(ssh, temp_cmd, nombre_equipo, timeout=10)
            if temp_result:
                try:
                    temp_val = float(temp_result)
                    if 0 <= temp_val <= 100:
                        metricas['temperatura'] = temp_val
                    else:
                        logging.warning(f"Temperatura fuera de rango para {nombre_equipo}: {temp_val}")
                        metricas['temperatura'] = 35.0
                except ValueError as e:
                    logging.warning(f"Error convirtiendo temperatura para {nombre_equipo}: {e}")
                    metricas['temperatura'] = 35.0
            else:
                metricas['temperatura'] = 35.0
        except Exception as e:
            logging.error(f"Error obteniendo temperatura para {nombre_equipo}: {e}")
            metricas['temperatura'] = 35.0
        
        # Timestamp
        metricas['timestamp'] = datetime.now().isoformat()
        
    except Exception as e:
        logging.error(f"Error general obteniendo métricas remotas para {equipo.get('nombre', 'desconocido')}: {e}")
        # Asegurar métricas mínimas
        metricas = {
            'cpu': 0.0,
            'memoria': 0.0,
            'temperatura': 35.0,
            'timestamp': datetime.now().isoformat()
        }
    finally:
        # Cerrar conexión SSH si existe
        if ssh:
            try:
                cerrar_conexion_ssh(ssh)
            except Exception as e:
                logging.warning(f"Error cerrando conexión SSH para {equipo.get('nombre', 'desconocido')}: {e}")
    
    return metricas
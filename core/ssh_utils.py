#!/usr/bin/env python3
"""
Utilidades SSH para conexiones remotas
"""

import os
import socket
import paramiko
import logging
from pathlib import Path

_logger = logging.getLogger('ssh_utils')
_logger.propagate = False
if not _logger.handlers:
    Path('./logs').mkdir(exist_ok=True)
    _h = logging.FileHandler('./logs/monitor_distribuido.log', encoding='utf-8')
    _h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    _logger.addHandler(_h)
    _logger.setLevel(logging.INFO)

def crear_conexion_ssh(equipo):
    """Crea y conecta una conexión SSH con manejo robusto de errores"""
    try:
        # Validar parámetros requeridos
        if not equipo:
            logging.error("Equipo no proporcionado")
            return None
        
        nombre = equipo.get('nombre', 'desconocido')
        ip = equipo.get('ip')
        usuario = equipo.get('user')
        clave_path = equipo.get('ssh_key_path')
        puerto = equipo.get('port', 22)
        
        if not ip:
            logging.error(f"IP no especificada para {nombre}")
            return None
        if not usuario:
            logging.error(f"Usuario no especificado para {nombre}")
            return None
        if not clave_path:
            logging.error(f"Ruta de clave SSH no especificada para {nombre}")
            return None
        
        # Verificar que la clave existe
        if not os.path.exists(clave_path):
            logging.error(f"Clave SSH no encontrada: {clave_path} para {nombre}")
            return None
        
        # Crear cliente SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Cargar clave privada
        try:
            key = paramiko.RSAKey.from_private_key_file(clave_path)
        except paramiko.ssh_exception.PasswordRequiredException:
            logging.error(f"Clave SSH requiere contraseña para {nombre}")
            return None
        except paramiko.ssh_exception.SSHException as e:
            logging.error(f"Error en formato de clave SSH para {nombre}: {e}")
            return None
        
        # Conectar con timeout
        try:
            ssh.connect(
                hostname=ip,
                username=usuario,
                pkey=key,
                port=puerto,
                timeout=15,
                banner_timeout=20,
                auth_timeout=10
            )
            logging.debug(f"Conexión SSH establecida con {nombre} ({ip}:{puerto})")
            return ssh
            
        except paramiko.AuthenticationException:
            logging.error(f"Autenticación fallida para {nombre} ({ip})")
            return None
        except paramiko.SSHException as e:
            logging.error(f"Error SSH para {nombre} ({ip}): {e}")
            return None
        except socket.timeout:
            logging.error(f"Timeout conectando a {nombre} ({ip})")
            return None
        except socket.error as e:
            logging.error(f"Error de socket para {nombre} ({ip}): {e}")
            return None
        
    except KeyError as e:
        logging.error(f"Falta clave en datos del equipo: {e}")
        return None
    except Exception as e:
        logging.error(f"Error inesperado creando conexión SSH: {e}")
        return None

def ejecutar_comando_ssh(ssh, comando, nombre_equipo="", timeout=15):
    """Ejecuta un comando en una conexión SSH activa con manejo de errores"""
    if not ssh:
        logging.warning(f"Conexión SSH no válida para ejecutar comando en {nombre_equipo}")
        return None
    
    if not comando or not isinstance(comando, str):
        logging.warning(f"Comando inválido para {nombre_equipo}: {comando}")
        return None
    
    try:
        stdin, stdout, stderr = ssh.exec_command(comando, timeout=timeout)
        
        # Leer salida y errores
        salida = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        
        # Log de errores si existen
        if error and "command not found" not in error.lower():
            logging.debug(f"Error en comando SSH para {nombre_equipo}: {error}")
        
        return salida
        
    except socket.timeout:
        logging.error(f"Timeout ejecutando comando en {nombre_equipo}: {comando[:50]}...")
        return None
    except paramiko.SSHException as e:
        logging.error(f"Error SSH ejecutando comando en {nombre_equipo}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error inesperado ejecutando comando en {nombre_equipo}: {e}")
        return None

def cerrar_conexion_ssh(ssh):
    """Cierra una conexión SSH de manera segura"""
    if ssh:
        try:
            ssh.close()
            logging.debug("Conexión SSH cerrada correctamente")
        except Exception as e:
            logging.warning(f"Error cerrando conexión SSH: {e}")
#!/usr/bin/env python3
"""
Utilidades SSH para conexiones remotas
"""

import paramiko
import logging

def crear_conexion_ssh(equipo):
    """Crea y conecta una conexión SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        key = paramiko.RSAKey.from_private_key_file(equipo['ssh_key_path'])
        ssh.connect(
            hostname=equipo['ip'],
            username=equipo['user'],
            pkey=key,
            port=equipo['port'],
            timeout=10
        )
        return ssh
    except Exception as e:
        logging.error(f"Error conectando a {equipo['nombre']}: {e}")
        return None

def ejecutar_comando_ssh(ssh, comando, nombre_equipo=""):
    """Ejecuta un comando en una conexión SSH activa"""
    if not ssh:
        return None
    try:
        stdin, stdout, stderr = ssh.exec_command(comando)
        return stdout.read().decode().strip()
    except Exception as e:
        logging.error(f"Error ejecutando comando en {nombre_equipo}: {e}")
        return None

def cerrar_conexion_ssh(ssh):
    """Cierra una conexión SSH"""
    if ssh:
        ssh.close()
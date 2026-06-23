#!/usr/bin/env python3
"""
Utilidades de logging compartidas
"""

import logging
import os
from datetime import datetime

def setup_logging(nombre_modulo, nivel=logging.INFO):
    """
    Configura logging estandarizado para un módulo
    
    Args:
        nombre_modulo (str): Nombre del módulo (ej: 'agente_ping')
        nivel: Nivel de logging (logging.INFO, logging.DEBUG, etc.)
    
    Returns:
        logging.Logger: Logger configurado
    """
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    # Configurar logger
    logger = logging.getLogger(nombre_modulo)
    logger.setLevel(nivel)
    
    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger
    
    # Handler para archivo
    archivo_log = os.path.join("logs", f"{nombre_modulo}.log")
    file_handler = logging.FileHandler(archivo_log, encoding='utf-8')
    file_handler.setLevel(nivel)
    
    # Handler para consola (opcional)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Solo warnings+ en consola
    
    # Formato de logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_evento(logger, evento, detalles=""):
    """
    Registra un evento de manera estandarizada
    
    Args:
        logger: Logger a usar
        evento (str): Descripción del evento
        detalles (str): Detalles adicionales del evento
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje = f"{evento}"
    if detalles:
        mensaje += f" - {detalles}"
    
    logger.info(mensaje)

def log_error(logger, error, contexto=""):
    """
    Registra un error de manera estandarizada
    
    Args:
        logger: Logger a usar
        error (Exception|str): Error ocurrido
        contexto (str): Contexto donde ocurrió el error
    """
    mensaje = f"ERROR: {str(error)}"
    if contexto:
        mensaje = f"{contexto} - {mensaje}"
    
    logger.error(mensaje)

def limpiar_logs_antiguos(dias_maximos=7):
    """
    Limpia logs más antiguos que X días
    
    Args:
        dias_maximos (int): Días máximos de retención de logs
    """
    import time
    
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        return
    
    tiempo_limite = time.time() - (dias_maximos * 24 * 60 * 60)
    
    for archivo in os.listdir(logs_dir):
        if archivo.endswith('.log'):
            ruta_archivo = os.path.join(logs_dir, archivo)
            if os.path.getmtime(ruta_archivo) < tiempo_limite:
                try:
                    os.remove(ruta_archivo)
                    print(f"🗑️ Log antiguo eliminado: {archivo}")
                except Exception as e:
                    print(f"❌ Error eliminando {archivo}: {e}")
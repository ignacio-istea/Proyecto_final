#!/usr/bin/env python3
"""
Gestión de datos de alarmas
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Variables globales para datos de alarmas
_config_path = "config.json"
_config = None
_alarmas_activas = {}
_historial_eventos = []

def init_alarm_data(config_path="config.json"):
    """Inicializa los datos de alarmas"""
    global _config_path, _config
    _config_path = config_path
    _config = _cargar_config()
    _cargar_datos_alarmas()
    return True

def _cargar_config():
    """Carga la configuración desde el archivo JSON con manejo robusto"""
    try:
        with open(_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
            # Validar estructura básica
            if not isinstance(config, dict):
                raise ValueError("Configuración debe ser un diccionario")
            
            # Validar secciones requeridas
            secciones_requeridas = ['equipos', 'monitoreo', 'logging', 'alertas']
            for seccion in secciones_requeridas:
                if seccion not in config:
                    raise ValueError(f"Falta sección requerida: {seccion}")
            
            return config
            
    except FileNotFoundError:
        logging.error(f"Archivo de configuración no encontrado: {_config_path}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error en formato JSON: {e}")
        return None
    except PermissionError as e:
        logging.error(f"Error de permisos: {e}")
        return None
    except ValueError as e:
        logging.error(f"Error de validación: {e}")
        return None
    except Exception as e:
        logging.error(f"Error inesperado cargando configuración: {e}")
        return None

def _cargar_datos_alarmas():
    """Carga alarmas y eventos desde archivos de datos con manejo robusto"""
    global _alarmas_activas, _historial_eventos
    
    try:
        # Cargar alarmas activas
        alarmas_file = Path("./logs/alarmas_activas.json")
        if alarmas_file.exists():
            try:
                with open(alarmas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        _alarmas_activas = data
                    else:
                        logging.warning(f"Formato inválido en {alarmas_file}, reiniciando alarmas")
                        _alarmas_activas = {}
            except json.JSONDecodeError as e:
                logging.error(f"Error JSON en {alarmas_file}: {e}")
                # Crear archivo vacío
                _alarmas_activas = {}
                _guardar_datos_alarmas()
            except Exception as e:
                logging.error(f"Error leyendo {alarmas_file}: {e}")
                _alarmas_activas = {}
        else:
            _alarmas_activas = {}
        
        # Cargar historial de eventos
        historial_file = Path("./logs/historial_eventos.json")
        if historial_file.exists():
            try:
                with open(historial_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        _historial_eventos = data
                    else:
                        logging.warning(f"Formato inválido en {historial_file}, reiniciando historial")
                        _historial_eventos = []
            except json.JSONDecodeError as e:
                logging.error(f"Error JSON en {historial_file}: {e}")
                _historial_eventos = []
                _guardar_datos_alarmas()
            except Exception as e:
                logging.error(f"Error leyendo {historial_file}: {e}")
                _historial_eventos = []
        else:
            _historial_eventos = []
            
    except Exception as e:
        logging.error(f"Error crítico cargando datos de alarmas: {e}")
        # Inicializar estructuras vacías
        _alarmas_activas = {}
        _historial_eventos = []

def _guardar_datos_alarmas():
    """Guarda alarmas y eventos en archivos JSON con manejo robusto"""
    try:
        # Crear directorio de logs si no existe
        logs_dir = Path("./logs")
        try:
            logs_dir.mkdir(exist_ok=True)
        except PermissionError as e:
            logging.error(f"Error de permisos creando directorio logs: {e}")
            return False
        
        # Guardar alarmas activas
        try:
            alarmas_file = logs_dir / "alarmas_activas.json"
            with open(alarmas_file, 'w', encoding='utf-8') as f:
                json.dump(_alarmas_activas, f, indent=2, ensure_ascii=False)
        except PermissionError as e:
            logging.error(f"Error de permisos guardando alarmas: {e}")
            return False
        except Exception as e:
            logging.error(f"Error guardando alarmas: {e}")
            return False
        
        # Guardar historial (últimos 1000 eventos)
        try:
            historial_file = logs_dir / "historial_eventos.json"
            with open(historial_file, 'w', encoding='utf-8') as f:
                json.dump(_historial_eventos[-1000:], f, indent=2, ensure_ascii=False)
        except PermissionError as e:
            logging.error(f"Error de permisos guardando historial: {e}")
            # Al menos las alarmas se guardaron
            return True
        except Exception as e:
            logging.error(f"Error guardando historial: {e}")
            # Al menos las alarmas se guardaron
            return True
        
        return True
        
    except Exception as e:
        logging.error(f"Error crítico guardando datos: {e}")
        return False

def registrar_evento(equipo, metrica, severidad, valor, umbral):
    """Registra un nuevo evento de alarma con manejo robusto"""
    global _alarmas_activas, _historial_eventos
    
    try:
        # Validar parámetros
        if not equipo or not isinstance(equipo, str):
            logging.warning(f"Equipo inválido para evento: {equipo}")
            return False
        
        if not metrica or not isinstance(metrica, str):
            logging.warning(f"Métrica inválida para evento: {metrica}")
            return False
        
        if severidad not in ['clear', 'warning', 'critico']:
            logging.warning(f"Severidad inválida: {severidad}")
            return False
        
        # Validar valores numéricos
        try:
            valor_num = float(valor) if valor is not None else 0.0
            umbral_num = float(umbral) if umbral is not None else 0.0
        except (ValueError, TypeError):
            logging.warning(f"Valores numéricos inválidos: valor={valor}, umbral={umbral}")
            return False
        
        timestamp = datetime.now().isoformat()
        
        evento = {
            "timestamp": timestamp,
            "equipo": equipo,
            "metrica": metrica,
            "severidad": severidad,
            "valor": valor_num,
            "umbral": umbral_num,
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
                "valor": valor_num,
                "umbral": umbral_num,
                "inicio_timestamp": _alarmas_activas.get(key, {}).get("inicio_timestamp") or timestamp,
                "ultimo_timestamp": timestamp,
                "estado": "activo",
                "contador_eventos": _alarmas_activas.get(key, {}).get("contador_eventos", 0) + 1
            }
        
        # Guardar datos
        return _guardar_datos_alarmas()
        
    except Exception as e:
        logging.error(f"Error crítico registrando evento: {e}")
        return False

def get_alarmas_activas():
    """Obtiene alarmas activas"""
    _cargar_datos_alarmas()
    return {k: v for k, v in _alarmas_activas.items() if v.get("estado") == "activo"}

def get_alarmas_resueltas():
    """Obtiene alarmas resueltas"""
    _cargar_datos_alarmas()
    return {k: v for k, v in _alarmas_activas.items() if v.get("estado") == "resuelto"}

def get_historial_eventos():
    """Obtiene historial completo de eventos"""
    _cargar_datos_alarmas()
    return _historial_eventos.copy()

def get_todas_alarmas():
    """Obtiene todas las alarmas"""
    _cargar_datos_alarmas()
    return _alarmas_activas.copy()

def limpiar_alarmas_resueltas():
    """Elimina alarmas resueltas de los datos"""
    global _alarmas_activas
    resueltas = get_alarmas_resueltas()
    
    if resueltas:
        _alarmas_activas = {k: v for k, v in _alarmas_activas.items() 
                          if v.get("estado") != "resuelto"}
        _guardar_datos_alarmas()
    
    return len(resueltas)

def recargar_datos():
    """Recarga datos desde archivos"""
    _cargar_datos_alarmas()
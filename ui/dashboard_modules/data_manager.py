#!/usr/bin/env python3
"""
Gestión de datos de alarmas
"""

import json
import time
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
    """Carga la configuración desde el archivo JSON"""
    try:
        with open(_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def _cargar_datos_alarmas():
    """Carga alarmas y eventos desde archivos de datos"""
    global _alarmas_activas, _historial_eventos
    try:
        # Cargar alarmas activas
        if Path("./logs/alarmas_activas.json").exists():
            with open("./logs/alarmas_activas.json", 'r') as f:
                _alarmas_activas = json.load(f)
        
        # Cargar historial de eventos
        if Path("./logs/historial_eventos.json").exists():
            with open("./logs/historial_eventos.json", 'r') as f:
                _historial_eventos = json.load(f)
    except Exception as e:
        print(f"Error cargando datos de alarmas: {e}")

def _guardar_datos_alarmas():
    """Guarda alarmas y eventos en archivos JSON"""
    try:
        Path("./logs").mkdir(exist_ok=True)
        
        # Guardar alarmas activas
        with open("./logs/alarmas_activas.json", 'w') as f:
            json.dump(_alarmas_activas, f, indent=2)
        
        # Guardar historial (últimos 1000 eventos)
        with open("./logs/historial_eventos.json", 'w') as f:
            json.dump(_historial_eventos[-1000:], f, indent=2)
    except Exception as e:
        print(f"Error guardando datos: {e}")

def registrar_evento(equipo, metrica, severidad, valor, umbral):
    """Registra un nuevo evento de alarma"""
    global _alarmas_activas, _historial_eventos
    
    timestamp = datetime.now().isoformat()
    
    evento = {
        "timestamp": timestamp,
        "equipo": equipo,
        "metrica": metrica,
        "severidad": severidad,
        "valor": valor,
        "umbral": umbral,
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
            "valor": valor,
            "umbral": umbral,
            "inicio_timestamp": _alarmas_activas.get(key, {}).get("inicio_timestamp") or timestamp,
            "ultimo_timestamp": timestamp,
            "estado": "activo",
            "contador_eventos": _alarmas_activas.get(key, {}).get("contador_eventos", 0) + 1
        }
    
    _guardar_datos_alarmas()

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
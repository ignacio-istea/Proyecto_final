#!/usr/bin/env python3
"""
Gestor de configuración del sistema
Separado de las métricas para mejor modularización
"""

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from utils.notifications import enviar_notificacion
from core.metrics_collector import obtener_metricas_locales, obtener_metricas_remotas

def cargar_configuracion(config_path="config.json"):
    """Carga la configuración desde archivo JSON"""
    with open(config_path, 'r') as f:
        return json.load(f)

def get_equipos(config):
    """Obtiene lista de equipos de la configuración"""
    return config['equipos']

def get_monitoreo_config(config):
    """Obtiene configuración de monitoreo"""
    return config['monitoreo']

def get_logging_config(config):
    """Obtiene configuración de logging"""
    return config['logging']

def get_alertas_config(config):
    """Obtiene configuración de alertas"""
    return config['alertas']

def crear_sistema_alertas(config_alertas, umbrales_por_equipo=None):
    """Crea configuración del sistema de alertas"""
    config = config_alertas.copy()
    config['voz_activa'] = False  # Texto a voz deshabilitado permanentemente
    return {
        'config': config,
        'umbrales_por_equipo': umbrales_por_equipo or {}
    }

def enviar_alerta(sistema_alertas, equipo_nombre, tipo_alerta, valor, limite, severidad='critico'):
    """Envía una alerta del sistema"""
    mensaje = f"ALERTA {severidad.upper()}: {equipo_nombre} - {tipo_alerta}: {valor}% (límite: {limite}%)"
    
    # Log según severidad
    if severidad == 'critico':
        logging.critical(mensaje)
    elif severidad == 'warning':
        logging.warning(mensaje)
    else:
        logging.info(f"CLEAR: {equipo_nombre} - {tipo_alerta} normalizado: {valor}%")
    
    if sistema_alertas['config']['notificaciones_desktop']:
        _enviar_notificacion_desktop(equipo_nombre, tipo_alerta, valor, severidad)

def _enviar_notificacion_desktop(equipo, tipo, valor, severidad):
    """Envía notificación desktop usando comandos nativos del sistema"""
    try:
        if severidad == 'clear':
            titulo = f"✅ {equipo} - {tipo} Normalizado"
        elif severidad == 'warning':
            titulo = f"⚠️ Alerta Preventiva - {equipo}"
        else:
            titulo = f"🚨 Alerta Crítica - {equipo}"
        
        mensaje = f"{tipo.upper()}: {valor}%"
        
        # Usar la función de utilidades
        enviar_notificacion(titulo, mensaje)
        
    except Exception as e:
        # Fallback: log como notificación
        logging.info(f"NOTIFICACIÓN: {equipo} - {tipo.upper()}: {valor}% ({severidad})")

def crear_monitor_distribuido():
    """Inicializa el monitor distribuido"""
    config = cargar_configuracion()
    equipos = get_equipos(config)
    monitoreo_config = get_monitoreo_config(config)
    
    # Cargar umbrales por equipo si existen
    umbrales_por_equipo = config.get('umbrales_por_equipo', {})
    
    sistema_alertas = crear_sistema_alertas(
        get_alertas_config(config),
        umbrales_por_equipo
    )
    
    _setup_logging(get_logging_config(config))
    
    estados_alertas = {}  # Para tracking de estados
    
    # Inicializar manager de alarmas
    try:
        from ui.dashboard import AlarmManager
        alarm_manager = AlarmManager()
    except ImportError:
        alarm_manager = None
        logging.warning("Tablero de alarmas no disponible")
    
    return {
        'config': config,
        'equipos': equipos,
        'monitoreo_config': monitoreo_config,
        'sistema_alertas': sistema_alertas,
        'estados_alertas': estados_alertas,
        'alarm_manager': alarm_manager,
        'ejecutando': False
    }

def _setup_logging(log_config):
    """Configura el sistema de logging"""
    Path(log_config['directorio']).mkdir(exist_ok=True)
    
    log_file = Path(log_config['directorio']) / log_config['archivo_principal']
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def monitorear_equipo(monitor, equipo):
    """Monitorea un equipo específico"""
    # Monitoreo local si es localhost o equipo local
    if (equipo['ip'] in ['localhost', '127.0.0.1'] or 
        equipo['nombre'].lower().startswith('local') or
        equipo.get('tipo') == 'local'):
        
        try:
            metricas = obtener_metricas_locales()
            logging.info(f"Monitoreando localmente: {equipo['nombre']}")
        except Exception as e:
            logging.error(f"Error obteniendo métricas locales para {equipo['nombre']}: {e}")
            return
    else:
        # Monitoreo remoto SSH
        try:
            metricas = obtener_metricas_remotas(equipo)
        except Exception as e:
            logging.error(f"Error obteniendo métricas remotas para {equipo['nombre']}: {e}")
            return
    
    # Verificar límites y mostrar información
    _verificar_limites(monitor, equipo['nombre'], metricas)
    logging.info(f"{equipo['nombre']}: CPU={metricas.get('cpu', 0):.1f}%, "
                f"MEM={metricas.get('memoria', 0):.1f}%, "
                f"TEMP={metricas.get('temperatura', 0):.1f}°C")

def _verificar_limites(monitor, nombre_equipo, metricas):
    """Verifica los límites de las métricas y genera alertas"""
    config = monitor['monitoreo_config']
    umbrales_equipo = monitor['sistema_alertas']['umbrales_por_equipo'].get(nombre_equipo)
    
    # Inicializar estado si no existe
    if nombre_equipo not in monitor['estados_alertas']:
        monitor['estados_alertas'][nombre_equipo] = {
            'cpu': 'normal',
            'memoria': 'normal', 
            'temperatura': 'normal'
        }
    
    # Verificar cada métrica
    _verificar_metrica(monitor, nombre_equipo, 'cpu', metricas.get('cpu', 0), 
                       umbrales_equipo, config['cpu_limite'])
    
    _verificar_metrica(monitor, nombre_equipo, 'memoria', metricas.get('memoria', 0),
                       umbrales_equipo, config['memoria_limite'])
    
    _verificar_metrica(monitor, nombre_equipo, 'temperatura', metricas.get('temperatura', 0),
                       umbrales_equipo, config['temp_limite'])

def _verificar_metrica(monitor, equipo, metrica, valor, umbrales_equipo, limite_global):
    """Verifica una métrica específica y genera alertas si es necesario"""
    estado_anterior = monitor['estados_alertas'][equipo][metrica]
    nuevo_estado = 'normal'
    
    # Usar umbrales específicos del equipo si existen, sino globales
    if umbrales_equipo and metrica in umbrales_equipo:
        umbrales = umbrales_equipo[metrica]
        clear_val = umbrales['clear']
        warning_val = umbrales['warning']
        critico_val = umbrales['critico']
    else:
        # Calcular umbrales basados en el límite global
        critico_val = limite_global
        warning_val = limite_global * 0.7
        clear_val = limite_global * 0.6
    
    # Determinar nuevo estado
    if valor >= critico_val:
        nuevo_estado = 'critico'
    elif valor >= warning_val:
        nuevo_estado = 'warning'
    elif valor <= clear_val and estado_anterior != 'normal':
        nuevo_estado = 'clear'
    
    # Enviar alerta solo si hay cambio de estado
    if nuevo_estado != estado_anterior:
        if nuevo_estado == 'critico':
            enviar_alerta(monitor['sistema_alertas'], equipo, metrica, valor, critico_val, 'critico')
            if monitor['alarm_manager']:
                monitor['alarm_manager'].registrar_evento(equipo, metrica, 'critico', valor, critico_val)
        elif nuevo_estado == 'warning':
            enviar_alerta(monitor['sistema_alertas'], equipo, metrica, valor, warning_val, 'warning')
            if monitor['alarm_manager']:
                monitor['alarm_manager'].registrar_evento(equipo, metrica, 'warning', valor, warning_val)
        elif nuevo_estado == 'clear':
            enviar_alerta(monitor['sistema_alertas'], equipo, metrica, valor, clear_val, 'clear')
            if monitor['alarm_manager']:
                monitor['alarm_manager'].registrar_evento(equipo, metrica, 'clear', valor, clear_val)
        
        # Actualizar estado
        if nuevo_estado != 'clear':
            monitor['estados_alertas'][equipo][metrica] = nuevo_estado
        else:
            monitor['estados_alertas'][equipo][metrica] = 'normal'

def iniciar_monitoreo(monitor):
    """Inicia el monitoreo distribuido"""
    monitor['ejecutando'] = True
    logging.info("Iniciando monitoreo distribuido...")
    
    while monitor['ejecutando']:
        for equipo in monitor['equipos']:
            if not monitor['ejecutando']:
                break
            threading.Thread(target=monitorear_equipo, args=(monitor, equipo)).start()
        
        time.sleep(monitor['monitoreo_config']['intervalo_segundos'])

def detener_monitoreo(monitor):
    """Detiene el monitoreo distribuido"""
    monitor['ejecutando'] = False
    logging.info("Deteniendo monitoreo...")

def main():
    """Función principal con manejo mejorado de errores"""
    try:
        print("=== Sistema de Monitoreo Distribuido ===")
        print("Inicializando sistema...")
        
        monitor = crear_monitor_distribuido()
        
        print("✅ Sistema inicializado correctamente")
        print("Presiona Ctrl+C para detener")
        print("="*50)
        
        iniciar_monitoreo(monitor)
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Ejecuta: python3 setup.py para instalar dependencias")
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")
        print("💡 Verifica que config.json existe o ejecuta python3 setup.py")
    except PermissionError as e:
        print(f"❌ Error de permisos: {e}")
        print("💡 Verifica permisos de archivos y directorios")
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido por el usuario.")
        print("👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("\n🔍 Información técnica del error:")
        import traceback
        traceback.print_exc()
        print("\n💡 Si el problema persiste, revisa la configuración")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Gestor de configuración del sistema

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
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Archivo de configuración con formato JSON inválido: {config_path}") from e
    except PermissionError as e:
        raise PermissionError(f"Sin permisos para leer el archivo de configuración: {config_path}") from e
    except Exception as e:
        raise RuntimeError(f"Error al cargar configuración: {e}") from e

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

# Logger propio del monitor — no toca el logger raíz del proceso
_logger = logging.getLogger('monitor_distribuido')

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

    if severidad == 'critico':
        _logger.critical(mensaje)
    elif severidad == 'warning':
        _logger.warning(mensaje)
    else:
        _logger.info(f"CLEAR: {equipo_nombre} - {tipo_alerta} normalizado: {valor}%")

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
        
    except Exception:
        pass  # Notificación desktop opcional, fallo silencioso

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
    
    # Registrar eventos de alarma via data_manager
    try:
        from ui.dashboard_modules.data_manager import registrar_evento as _registrar_evento, init_alarm_data
        init_alarm_data()  # inicializa _config y carga archivos existentes
        alarm_manager = type('AlarmProxy', (), {'registrar_evento': staticmethod(_registrar_evento)})()
    except ImportError:
        alarm_manager = None
    
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
    """Configura el logger propio del monitor (solo archivo, sin consola)"""
    try:
        Path(log_config['directorio']).mkdir(exist_ok=True)
        log_file = Path(log_config['directorio']) / log_config['archivo_principal']

        # Usar logger con nombre propio para no interferir con el proceso principal
        _logger.setLevel(logging.INFO)
        _logger.propagate = False  # No propagar al logger raíz

        # Evitar duplicar handlers si se llama más de una vez
        if not _logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            _logger.addHandler(handler)

    except Exception as e:
        # Silencioso — el monitor no debe romper la terminal
        pass

def monitorear_equipo_seguro(monitor, equipo):
    """Wrapper seguro para monitorear_equipo con manejo de excepciones"""
    try:
        monitorear_equipo(monitor, equipo)
    except Exception as e:
        _logger.error(f"Error crítico monitoreando {equipo.get('nombre', 'desconocido')}: {e}")

def monitorear_equipo(monitor, equipo):
    """Monitorea un equipo específico"""
    try:
        # Validar datos del equipo
        if not equipo or 'nombre' not in equipo or 'ip' not in equipo:
            _logger.error(f"Equipo inválido o datos incompletos: {equipo}")
            return
        
        # Saltar equipos con SSH deshabilitado que no sean locales
        es_local = (equipo['ip'] in ['localhost', '127.0.0.1'] or
                    equipo.get('tipo') == 'local')
        ssh_activo = equipo.get('ssh_activo', False)

        if es_local:
            try:
                metricas = obtener_metricas_locales()
            except Exception as e:
                _logger.error(f"Error métricas locales {equipo['nombre']}: {e}")
                return
        elif not ssh_activo:
            return  # SSH deshabilitado, no monitorear
        else:
            try:
                metricas = obtener_metricas_remotas(equipo)
            except Exception as e:
                _logger.error(f"Error métricas remotas {equipo['nombre']}: {e}")
                return

        if not metricas:
            _logger.warning(f"Sin métricas para {equipo['nombre']}")
            return

        _verificar_limites(monitor, equipo['nombre'], metricas)
        _logger.info(f"{equipo['nombre']}: CPU={metricas.get('cpu', 0):.1f}% "
                     f"MEM={metricas.get('memoria', 0):.1f}% "
                     f"TEMP={metricas.get('temperatura', 0):.1f}°C")

    except KeyError as e:
        _logger.error(f"Clave faltante en equipo {equipo.get('nombre', '?')}: {e}")
    except Exception as e:
        _logger.error(f"Error inesperado monitoreando {equipo.get('nombre', '?')}: {e}")

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
    try:
        # Validar estructura del monitor
        if not monitor or 'equipos' not in monitor or 'monitoreo_config' not in monitor:
            _logger.error("Estructura del monitor inválida")
            return
        
        monitor['ejecutando'] = True
        _logger.info("Iniciando monitoreo distribuido...")
        
        threads_activos = []
        
        while monitor['ejecutando']:
            for equipo in monitor['equipos']:
                if not monitor['ejecutando']:
                    break
                
                # Validar equipo antes de crear thread
                if not equipo or 'nombre' not in equipo:
                    _logger.warning("Equipo inválido omitido")
                    continue
                
                thread = threading.Thread(
                    target=monitorear_equipo_seguro,
                    args=(monitor, equipo),
                    daemon=True,
                    name=f"Monitor-{equipo['nombre']}"
                )
                thread.start()
                threads_activos.append(thread)
                
                # Limitar threads activos para evitar sobrecarga
                if len(threads_activos) > 10:
                    # Esperar a que algunos threads terminen
                    for t in threads_activos[:5]:
                        if t.is_alive():
                            t.join(timeout=1)
                    threads_activos = [t for t in threads_activos if t.is_alive()]
            
            intervalo = monitor['monitoreo_config'].get('intervalo_segundos', 30)
            time.sleep(intervalo)
            
    except KeyboardInterrupt:
        _logger.info("Monitoreo interrumpido por usuario")
        monitor['ejecutando'] = False
    except Exception as e:
        _logger.error(f"Error crítico en iniciar_monitoreo: {e}")
        monitor['ejecutando'] = False
    finally:
        _logger.info("Monitoreo distribuido finalizado")

def detener_monitoreo(monitor):
    """Detiene el monitoreo distribuido"""
    monitor['ejecutando'] = False
    _logger.info("Deteniendo monitoreo...")

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
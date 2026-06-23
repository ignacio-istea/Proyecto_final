#!/usr/bin/env python3
"""
Generación de reportes automatizados
"""

import questionary
from datetime import datetime, timedelta
from pathlib import Path
from questionary import Style
from rich.console import Console
from ui.dashboard_modules.data_manager import get_alarmas_activas, get_historial_eventos, get_todas_alarmas

_console = Console()
_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
])

def generar_reporte_alarmas():
    """Genera un reporte automatizado de alarmas"""
    import os
    
    try:
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_reporte = f"./logs/reporte_alarmas_{timestamp}.txt"
        
        # Crear directorio si no existe
        Path("./logs").mkdir(exist_ok=True)
        
        # Generar contenido del reporte
        contenido = generar_contenido_reporte()
        
        # Guardar archivo
        with open(archivo_reporte, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        os.system('cls' if os.name == 'nt' else 'clear')
        _console.print("📈 [bold green]REPORTE GENERADO EXITOSAMENTE[/bold green]")
        _console.print(f"Archivo: [blue]{archivo_reporte}[/blue]")
        _console.print("\n" + "=" * 60)
        
        # Mostrar preview del reporte
        _console.print("[bold]PREVIEW DEL REPORTE:[/bold]")
        _console.print(contenido[:1000] + "..." if len(contenido) > 1000 else contenido)
        
        questionary.press_any_key_to_continue(
            "\nPresiona cualquier tecla para continuar..."
        ).ask()
        
    except Exception as e:
        _console.print(f"[red]❌ Error generando reporte: {e}[/red]")
        input("\nPresiona Enter para continuar...")

def generar_contenido_reporte():
    """Genera el contenido del reporte de alarmas"""
    ahora = datetime.now()
    historial_eventos = get_historial_eventos()
    alarmas_activas = get_alarmas_activas()
    todas_alarmas = get_todas_alarmas()
    
    contenido = f"""REPORTE DE ALARMAS - Sistema de Monitoreo Distribuido
============================================================
Generado: {ahora.strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    # Alarmas activas
    contenido += f"ALARMAS ACTIVAS: {len(alarmas_activas)}\n"
    contenido += "-" * 30 + "\n"
    
    if alarmas_activas:
        for key, alarma in alarmas_activas.items():
            inicio = datetime.fromisoformat(alarma['inicio_timestamp'])
            duracion = ahora - inicio
            
            minutos = int(duracion.total_seconds() / 60)
            horas = minutos // 60
            mins = minutos % 60
            
            if horas > 0:
                duracion_str = f"{horas}h {mins}m"
            else:
                duracion_str = f"{mins}m"
            
            if 'valor' in alarma:
                unidad = "%" if alarma.get('metrica') != 'temperatura' else "°C"
                info = f"{alarma['valor']:.1f}{unidad}/{alarma.get('umbral', 0):.1f}{unidad}"
            else:
                info = "OFFLINE"
            
            contenido += f"- {alarma['equipo']} | {alarma.get('metrica', 'conexion')} | {info} | {alarma['severidad']} | {duracion_str}\n"
    else:
        contenido += "No hay alarmas activas\n"
    
    # Eventos últimas 24h
    hace_24h = ahora - timedelta(hours=24)
    eventos_24h = [e for e in historial_eventos 
                  if datetime.fromisoformat(e['timestamp']) > hace_24h]
    
    contenido += f"\nEVENTOS ÚLTIMAS 24H: {len(eventos_24h)}\n"
    contenido += "-" * 30 + "\n"
    
    # Agrupar por severidad
    criticos = len([e for e in eventos_24h if e.get('severidad') == 'critico'])
    warnings = len([e for e in eventos_24h if e.get('severidad') == 'warning'])
    resueltos = len([e for e in eventos_24h if e.get('severidad') == 'clear'])
    
    contenido += f"- Críticos: {criticos}\n"
    contenido += f"- Warnings: {warnings}\n"
    contenido += f"- Resueltos: {resueltos}\n"
    
    # Equipos más afectados
    equipos_contador = {}
    for evento in eventos_24h:
        equipo = evento.get('equipo', 'desconocido')
        equipos_contador[equipo] = equipos_contador.get(equipo, 0) + 1
    
    contenido += "\nEQUIPOS MÁS AFECTADOS (24H):\n"
    contenido += "-" * 30 + "\n"
    
    equipos_ordenados = sorted(equipos_contador.items(), key=lambda x: x[1], reverse=True)
    for equipo, count in equipos_ordenados[:5]:
        contenido += f"- {equipo}: {count} eventos\n"
    
    # Estadísticas generales
    contenido += f"\nESTADÍSTICAS GENERALES:\n"
    contenido += "-" * 30 + "\n"
    contenido += f"- Total eventos históricos: {len(historial_eventos)}\n"
    contenido += f"- Total alarmas registradas: {len(todas_alarmas)}\n"
    
    if historial_eventos:
        primer_evento = min(historial_eventos, key=lambda x: x['timestamp'])
        primer_fecha = datetime.fromisoformat(primer_evento['timestamp'])
        contenido += f"- Primer evento: {primer_fecha.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    contenido += f"\n============================================================\n"
    contenido += f"Reporte generado por Sistema de Monitoreo Distribuido\n"
    
    return contenido
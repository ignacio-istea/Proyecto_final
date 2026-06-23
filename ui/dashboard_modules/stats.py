#!/usr/bin/env python3
"""
Estadísticas del sistema de monitoreo
"""

import questionary
from datetime import datetime
from questionary import Style
from rich.console import Console
from ui.dashboard_modules.data_manager import get_alarmas_activas, get_historial_eventos

_console = Console()
_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
])

def mostrar_estadisticas():
    """Muestra estadísticas del sistema"""
    import os
    
    try:
        alarmas_activas = get_alarmas_activas()
        historial_eventos = get_historial_eventos()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        _console.print("📊 [bold]ESTADÍSTICAS DEL SISTEMA[/bold]")
        _console.print("=" * 60)
        
        # Estadísticas de alarmas activas
        _console.print(f"\n🚨 [red]ALARMAS ACTIVAS: {len(alarmas_activas)}[/red]")
        
        if alarmas_activas:
            criticas = len([a for a in alarmas_activas.values() 
                          if a.get('severidad') == 'critico'])
            warnings = len([a for a in alarmas_activas.values() 
                          if a.get('severidad') == 'warning'])
            
            _console.print(f"  • Críticas: [red]{criticas}[/red]")
            _console.print(f"  • Warnings: [yellow]{warnings}[/yellow]")
            
            # Alarma más antigua
            alarma_mas_antigua = min(alarmas_activas.values(), 
                                   key=lambda x: x['inicio_timestamp'])
            inicio = datetime.fromisoformat(alarma_mas_antigua['inicio_timestamp'])
            duracion = datetime.now() - inicio
            horas = int(duracion.total_seconds() / 3600)
            
            _console.print(f"  • Alarma más antigua: {alarma_mas_antigua['equipo']} ({horas}h activa)")
        
        # Estadísticas del historial
        _console.print(f"\n📋 [blue]HISTORIAL DE EVENTOS[/blue]")
        _console.print(f"  • Total eventos registrados: {len(historial_eventos)}")
        
        if historial_eventos:
            # Eventos por severidad
            criticos_hist = len([e for e in historial_eventos if e.get('severidad') == 'critico'])
            warnings_hist = len([e for e in historial_eventos if e.get('severidad') == 'warning'])
            resueltos_hist = len([e for e in historial_eventos if e.get('severidad') == 'clear'])
            
            _console.print(f"  • Eventos críticos: [red]{criticos_hist}[/red]")
            _console.print(f"  • Eventos warning: [yellow]{warnings_hist}[/yellow]")
            _console.print(f"  • Eventos resueltos: [green]{resueltos_hist}[/green]")
            
            # Periodo de datos
            fechas = [datetime.fromisoformat(e['timestamp']) for e in historial_eventos]
            primer_evento = min(fechas)
            ultimo_evento = max(fechas)
            
            _console.print(f"  • Primer evento: {primer_evento.strftime('%Y-%m-%d %H:%M')}")
            _console.print(f"  • Último evento: {ultimo_evento.strftime('%Y-%m-%d %H:%M')}")
            
            # Promedio de eventos por día
            dias_total = (ultimo_evento - primer_evento).days + 1
            promedio_dia = len(historial_eventos) / max(dias_total, 1)
            _console.print(f"  • Promedio eventos/día: {promedio_dia:.1f}")
        
        # Equipos más problemáticos
        _console.print(f"\n🖥️ [cyan]EQUIPOS MÁS PROBLEMÁTICOS[/cyan]")
        
        equipos_contador = {}
        for evento in historial_eventos:
            if evento.get('severidad') in ['critico', 'warning']:
                equipo = evento.get('equipo', 'desconocido')
                equipos_contador[equipo] = equipos_contador.get(equipo, 0) + 1
        
        if equipos_contador:
            equipos_top = sorted(equipos_contador.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (equipo, eventos) in enumerate(equipos_top, 1):
                _console.print(f"  {i}. {equipo}: {eventos} eventos")
        else:
            _console.print("  • No hay eventos problemáticos registrados")
        
        # Métricas por tipo
        _console.print(f"\n📈 [magenta]MÉTRICAS POR TIPO[/magenta]")
        
        metricas_contador = {}
        for evento in historial_eventos:
            if evento.get('severidad') in ['critico', 'warning']:
                metrica = evento.get('metrica', 'conexion')
                metricas_contador[metrica] = metricas_contador.get(metrica, 0) + 1
        
        if metricas_contador:
            for metrica, count in sorted(metricas_contador.items()):
                _console.print(f"  • {metrica.capitalize()}: {count} alertas")
        
        _console.print("\n" + "=" * 60)
        
        questionary.press_any_key_to_continue(
            "\nPresiona cualquier tecla para continuar..."
        ).ask()
        
    except Exception as e:
        _console.print(f"[red]❌ Error mostrando estadísticas: {e}[/red]")
        input("\nPresiona Enter para continuar...")
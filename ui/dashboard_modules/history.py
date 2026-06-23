#!/usr/bin/env python3
"""
Gestión de historial y filtros de eventos
"""

import questionary
from datetime import datetime, timedelta
from questionary import Style
from rich.console import Console
from ui.dashboard_modules.data_manager import get_historial_eventos

_console = Console()
_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
])

def mostrar_historial_filtrable():
    """Muestra el historial de eventos con filtros"""
    import os
    
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            filtros = [
                "📋 Todos los eventos",
                "🔴 Solo eventos críticos", 
                "🟡 Solo warnings",
                "✅ Solo eventos resueltos",
                "📅 Últimas 24 horas",
                "📅 Últimos 7 días",
                "🔍 Buscar por equipo",
                "← Volver"
            ]
            
            filtro = questionary.select(
                "📋 HISTORIAL DE EVENTOS - Selecciona filtro:",
                choices=filtros,
                style=_custom_style
            ).ask()
            
            if not filtro or "← Volver" in filtro:
                break
                
            eventos_filtrados = aplicar_filtro_historial(filtro)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            mostrar_eventos_filtrados(eventos_filtrados, filtro)
            
            questionary.press_any_key_to_continue(
                "\nPresiona cualquier tecla para continuar..."
            ).ask()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Presiona Enter para continuar...")

def aplicar_filtro_historial(filtro):
    """Aplica filtro al historial de eventos"""
    eventos = get_historial_eventos()
    
    if "🔴 Solo eventos críticos" in filtro:
        eventos = [e for e in eventos if e.get('severidad') == 'critico']
    elif "🟡 Solo warnings" in filtro:
        eventos = [e for e in eventos if e.get('severidad') == 'warning']
    elif "✅ Solo eventos resueltos" in filtro:
        eventos = [e for e in eventos if e.get('severidad') == 'clear']
    elif "📅 Últimas 24 horas" in filtro:
        hace_24h = datetime.now() - timedelta(hours=24)
        eventos = [e for e in eventos if datetime.fromisoformat(e['timestamp']) > hace_24h]
    elif "📅 Últimos 7 días" in filtro:
        hace_7d = datetime.now() - timedelta(days=7)
        eventos = [e for e in eventos if datetime.fromisoformat(e['timestamp']) > hace_7d]
    elif "🔍 Buscar por equipo" in filtro:
        equipo = questionary.text("Ingresa nombre del equipo:").ask()
        if equipo:
            eventos = [e for e in eventos if equipo.lower() in e.get('equipo', '').lower()]
    
    return sorted(eventos, key=lambda x: x['timestamp'], reverse=True)

def mostrar_eventos_filtrados(eventos, filtro):
    """Muestra eventos filtrados con Rich"""
    _console.print(f"📋 [bold]HISTORIAL DE EVENTOS - {filtro}[/bold]")
    _console.print(f"Total eventos encontrados: {len(eventos)}")
    _console.print("=" * 80)
    
    if not eventos:
        _console.print("[yellow]ℹ️ No se encontraron eventos con el filtro aplicado[/yellow]")
        return
    
    # Mostrar los primeros 20 eventos
    for i, evento in enumerate(eventos[:20]):
        timestamp = datetime.fromisoformat(evento['timestamp'])
        tiempo_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Color según severidad
        if evento['severidad'] == 'critico':
            color = "red"
            emoji = "🔴"
        elif evento['severidad'] == 'warning':
            color = "yellow"
            emoji = "🟡"
        elif evento['severidad'] == 'clear':
            color = "green"
            emoji = "✅"
        else:
            color = "blue"
            emoji = "🔵"
        
        _console.print(f"{emoji} [{color}]{tiempo_str}[/{color}] - {evento['equipo']} - {evento.get('metrica', 'conexion')} - {evento['severidad'].upper()}")
        
        if 'valor' in evento:
            unidad = "%" if evento.get('metrica') != 'temperatura' else "°C"
            _console.print(f"    Valor: {evento['valor']:.1f}{unidad} / Umbral: {evento.get('umbral', 0):.1f}{unidad}")
        
        _console.print()
    
    if len(eventos) > 20:
        _console.print(f"[dim]... y {len(eventos) - 20} eventos más[/dim]")
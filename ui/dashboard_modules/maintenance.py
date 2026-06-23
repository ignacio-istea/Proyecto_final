#!/usr/bin/env python3
"""
Mantenimiento y limpieza de alarmas
"""

import questionary
from questionary import Style
from rich.console import Console
from ui.dashboard_modules.data_manager import get_alarmas_resueltas, limpiar_alarmas_resueltas

_console = Console()
_custom_style = Style([
    ('qmark', 'fg:#ff9d00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9d00 bold'),
    ('pointer', 'fg:#ff9d00 bold'),
    ('highlighted', 'fg:#ff9d00 bold'),
    ('selected', 'fg:#cc5454'),
])

def ejecutar_limpieza_alarmas():
    """Limpia alarmas que ya han sido resueltas"""
    import os
    
    try:
        resueltas = get_alarmas_resueltas()
        
        if not resueltas:
            os.system('cls' if os.name == 'nt' else 'clear')
            _console.print("✅ [green]No hay alarmas resueltas para limpiar[/green]")
            questionary.press_any_key_to_continue(
                "\nPresiona cualquier tecla para continuar..."
            ).ask()
            return
        
        os.system('cls' if os.name == 'nt' else 'clear')
        _console.print(f"🧹 [bold]LIMPIAR ALARMAS RESUELTAS[/bold]")
        _console.print(f"Se encontraron {len(resueltas)} alarmas resueltas:")
        _console.print("\n")
        
        for key, alarma in resueltas.items():
            _console.print(f"- {alarma['equipo']} - {alarma.get('metrica', 'conexion')}")
        
        confirmar = questionary.select(
            f"\n¿Deseas eliminar estas {len(resueltas)} alarmas resueltas?",
            choices=[
                "🧹 Sí, limpiar alarmas resueltas",
                "❌ No, mantenerlas"
            ],
            style=_custom_style
        ).ask()
        
        if "🧹 Sí, limpiar" in confirmar:
            # Ejecutar limpieza
            eliminadas = limpiar_alarmas_resueltas()
            
            os.system('cls' if os.name == 'nt' else 'clear')
            _console.print("✅ [bold green]LIMPIEZA COMPLETADA[/bold green]")
            _console.print(f"Se eliminaron {eliminadas} alarmas resueltas")
        else:
            _console.print("❌ [yellow]Operación cancelada[/yellow]")
        
        questionary.press_any_key_to_continue(
            "\nPresiona cualquier tecla para continuar..."
        ).ask()
        
    except Exception as e:
        _console.print(f"[red]❌ Error limpiando alarmas: {e}[/red]")
        input("\nPresiona Enter para continuar...")
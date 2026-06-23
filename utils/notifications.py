#!/usr/bin/env python3
"""
Utilidades de notificaciones del sistema
"""

import os
import subprocess
import platform

def enviar_notificacion(titulo, mensaje, icono="info"):
    """
    Envía notificación nativa del sistema operativo
    
    Args:
        titulo (str): Título de la notificación
        mensaje (str): Mensaje de la notificación  
        icono (str): Tipo de icono (info, warning, error)
    """
    sistema = platform.system()
    
    try:
        if sistema == "Darwin":  # macOS
            script = f'''
            display notification "{mensaje}" with title "{titulo}"
            '''
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
            
        elif sistema == "Linux":
            # Verificar si notify-send está disponible
            if subprocess.run(["which", "notify-send"], capture_output=True).returncode == 0:
                subprocess.run([
                    "notify-send",
                    "-t", "5000",  # 5 segundos
                    titulo,
                    mensaje
                ], check=True)
            else:
                print(f"📱 {titulo}: {mensaje}")
                
        elif sistema == "Windows":
            # PowerShell para Windows
            script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.Visible = $true
            $notify.ShowBalloonTip(5000, "{titulo}", "{mensaje}", "Info")
            '''
            subprocess.run([
                "powershell", "-Command", script
            ], check=True)
        else:
            # Fallback para otros sistemas
            print(f"📱 {titulo}: {mensaje}")
            
    except Exception as e:
        # Fallback si la notificación falla
        print(f"📱 {titulo}: {mensaje}")
        print(f"⚠️ Error enviando notificación: {e}")

def verificar_notificaciones():
    """Verifica si las notificaciones están disponibles en el sistema"""
    sistema = platform.system()
    
    if sistema == "Darwin":
        return True  # macOS siempre tiene osascript
    elif sistema == "Linux":
        return subprocess.run(["which", "notify-send"], capture_output=True).returncode == 0
    elif sistema == "Windows":
        return True  # PowerShell disponible en Windows moderno
    else:
        return False
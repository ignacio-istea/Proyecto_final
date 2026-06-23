# Sistema de Monitoreo Distribuido
Proyecto final de programación en Python para Tecnicatura en Infraestructura

## 📋 Descripción
Sistema de monitoreo distribuido que supervisa múltiples equipos de red de forma remota via SSH, monitoreando CPU, memoria y temperatura con sistema de alertas integrado.

## 🚀 Características
- Monitoreo remoto via SSH
- Métricas de CPU, memoria y temperatura  
- **Agente de ping para monitoreo de conectividad**
- **Agente SSH para métricas remotas en tiempo real**
- **Tablero interactivo de alarmas en tiempo real**
- **Umbrales configurables por severidad (Warning, Crítico, Clear)**
- **Menú principal integrado**
- Notificaciones nativas del sistema operativo
- Logging detallado
- Configuración flexible JSON
- Soporte multi-threading

## 📦 Instalación
```bash
# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd Proyecto_final

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🔧 Configuración
Edita `config.json` para configurar:
- Equipos a monitorear (IP, credenciales SSH)
- Umbrales personalizados por equipo
- Intervalos de monitoreo
- Configuración del agente de ping
- Claves SSH para conexiones remotas

## 🖥️ Uso del Sistema
```bash
# Activar entorno virtual primero
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# Menú principal integrado (recomendado)
python3 main.py

# O ejecutar módulos individuales:
python3 ui/config_interface.py    # Configuración interactiva
python3 ui/dashboard.py           # Ver tablero de alarmas
python3 agents/ag_ping.py         # Monitoreo de conectividad
python3 agents/ag_ssh.py          # Monitoreo SSH remoto
```

## 📁 Estructura del Proyecto (Modularizada)
```
├── main.py                 # Punto de entrada principal
├── config.json            # Configuración del sistema
├── setup.py               # Instalador de dependencias  
├── requirements.txt       # Lista de dependencias
├── compat_legacy.py       # Compatibilidad hacia atrás
├── logs/                  # Archivos de registro
├── keys/                  # Claves SSH
├── core/                  # Módulo núcleo del sistema
│   ├── __init__.py        
│   └── config_manager.py  # Sistema principal de monitoreo
├── agents/                # Módulo de agentes especializados
│   ├── __init__.py
│   ├── ag_controller.py   # Controlador de agentes
│   ├── ag_ping.py         # Agente de conectividad
│   └── ag_ssh.py          # Agente SSH remoto
├── ui/                    # Módulo de interfaz de usuario
│   ├── __init__.py
│   ├── menu_system.py     # Sistema de menús
│   ├── dashboard.py       # Tablero de alarmas
│   └── config_interface.py # Configurador interactivo
└── utils/                 # Módulo de utilidades compartidas
    ├── __init__.py
    ├── notifications.py   # Sistema de notificaciones
    └── logging_utils.py   # Utilidades de logging
```

## 🎯 Funcionalidades del Tablero
- 📊 **Vista en tiempo real** de alarmas activas
- 🔍 **Detalles específicos** de cada alarma
- 📋 **Historial filtrable** de eventos
- 📈 **Reportes automatizados**
- 🧹 **Limpieza de alarmas resueltas**
- 📊 **Estadísticas del sistema**

## ⚠️ Notas Importantes
- Sistema optimizado para funcionar sin dependencias problemáticas
- Notificaciones nativas multiplataforma (macOS, Linux, Windows)
- Warnings de paramiko son normales y están suprimidos
- Para equipos locales usar `"ip": "localhost"`
- Claves SSH se almacenan en `./keys/`
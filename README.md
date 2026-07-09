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
- **Gestión de equipos desde el configurador interactivo**
- **Menú principal integrado**
- Notificaciones nativas del sistema operativo
- Logging detallado
- Configuración flexible JSON
- Soporte multi-threading

## 📦 Instalación
```bash
# Clonar el repositorio
git clone https://github.com/ignacio-istea/Proyecto_final.git
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

## 🔧 Configuración inicial (primer uso)

> ⚠️ `config.json` y el directorio `keys/` **no se incluyen en el repositorio** (están en `.gitignore`).
> Debes crearlos manualmente antes de ejecutar el sistema.
> Al iniciar `main.py`, el sistema detecta si faltan y muestra instrucciones con una plantilla lista para copiar.

### 1 — Crear config.json
Crea el archivo `config.json` en la raíz del proyecto. Puedes usar la plantilla que muestra el programa al arrancar, o copiar esta base mínima:

```json
{
  "equipos": [
    {
      "nombre": "Equipo-Local",
      "ip": "localhost",
      "user": "local",
      "ssh_key_path": "",
      "port": 22,
      "tipo": "local",
      "ssh_activo": false,
      "ping_activo": true
    }
  ],
  "monitoreo": {
    "intervalo_segundos": 30,
    "temp_limite": 50.0,
    "cpu_limite": 80.0,
    "memoria_limite": 85.0,
    "reintentos": 3
  },
  "logging": {
    "directorio": "./logs",
    "archivo_principal": "monitor_distribuido.log",
    "max_bytes": 10485760,
    "backup_count": 5
  },
  "alertas": {
    "email_activo": false,
    "notificaciones_desktop": true,
    "voz_activa": false
  },
  "umbrales_por_equipo": {},
  "agente_ping": {
    "activo": true,
    "intervalo_segundos": 30,
    "timeout_ping": 3,
    "dispositivos_criticos": []
  }
}
```

Edita los equipos según tu red. Para agregar más equipos puedes usar el configurador interactivo (`⚙️ Configurar dispositivos` → `🖥️ Gestionar equipos`).

### 2 — Crear directorio keys/
```bash
mkdir keys
# Copiar las claves SSH de tus equipos remotos:
cp /ruta/a/tu/clave.pem keys/
```
Si no usas conexiones SSH, basta con crear el directorio vacío.

## 🖥️ Uso del Sistema
```bash
# Activar entorno virtual primero
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# Menú principal integrado (recomendado)
python3 main.py

# O ejecutar módulos individuales:
python3 ui/config_interface.py    # Configurador de umbrales y equipos
python3 ui/dashboard.py           # Tablero de alarmas
python3 agents/ag_ping.py         # Agente de conectividad
python3 agents/ag_ssh.py          # Agente SSH remoto
```

## 📁 Estructura del Proyecto
```
├── main.py                        # Punto de entrada principal
├── config.json                    # Configuración (NO versionado, crear manualmente)
├── requirements.txt               # Dependencias
├── logs/                          # Archivos de registro (generado automáticamente)
├── keys/                          # Claves SSH (NO versionado, crear manualmente)
├── core/                          # Módulo núcleo del sistema
│   ├── config_manager.py          # Gestor de configuración y monitoreo
│   ├── metrics_collector.py       # Recolección de métricas locales y remotas
│   └── ssh_utils.py               # Utilidades de conexión SSH
├── agents/                        # Módulo de agentes especializados
│   ├── ag_controller.py           # Controlador de agentes (start/stop)
│   ├── ag_ping.py                 # Agente de conectividad
│   └── ag_ssh.py                  # Agente SSH remoto
├── ui/                            # Módulo de interfaz de usuario
│   ├── menu_system.py             # Sistema de menús principal
│   ├── dashboard.py               # Tablero de alarmas
│   ├── config_interface.py        # Configurador interactivo
│   └── dashboard_modules/         # Submódulos del tablero
│       ├── data_manager.py        # Gestión de datos de alarmas
│       ├── display.py             # Vista en tiempo real
│       ├── history.py             # Historial de eventos
│       ├── maintenance.py         # Limpieza de alarmas
│       ├── reports.py             # Generación de reportes
│       └── stats.py               # Estadísticas del sistema
└── utils/                         # Utilidades compartidas
    ├── notifications.py           # Notificaciones nativas del SO
    └── logging_utils.py           # Utilidades de logging
```

## 🎯 Funcionalidades del Tablero
- 📊 **Vista en tiempo real** de alarmas activas
- 🔍 **Detalles específicos** de cada alarma
- 📋 **Historial filtrable** de eventos
- 📈 **Reportes automatizados**
- 🧹 **Limpieza de alarmas resueltas**
- 📊 **Estadísticas del sistema**

## ⚙️ Funcionalidades del Configurador
- 📊 **Ver umbrales** globales y por equipo
- ⚙️ **Configurar umbrales por equipo** con niveles Clear / Warning / Crítico
- 🖥️ **Gestionar equipos**: agregar nuevos o editar existentes
- 🌐 **Configurar umbrales globales** del sistema
- 🚨 **Acceso directo al tablero** de alarmas

## ⚠️ Notas Importantes
- `config.json` y `keys/` están en `.gitignore` y **no se versionan** — deben crearse manualmente
- Al iniciar el programa se verifica su existencia y se muestran instrucciones si faltan
- Notificaciones nativas multiplataforma (macOS, Linux, Windows)
- Warnings de paramiko son normales y están suprimidos
- Para equipos locales usar `"ip": "localhost"`
- Claves SSH se almacenan en `./keys/`
- El directorio `logs/` se crea automáticamente al iniciar

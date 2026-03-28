# Stacer 2026

**Reimaginación moderna de Stacer — construida con PyQt6, datos 100% reales del sistema.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4%2B-green)
![License](https://img.shields.io/badge/License-MIT-purple)
![Platform](https://img.shields.io/badge/Platform-Linux-orange)

---

## Características

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | Gauges animados de CPU / RAM / Disco + info del sistema en tiempo real |
| **Limpiador** | Caché APT, journal, logs rotados, crash reports, miniaturas, papelera |
| **Optimizador** | Liberar RAM, swappiness, TRIM SSD, fc-cache, autoremove, flush DNS |
| **Servicios** | Tabla completa de servicios systemd con inicio/parada/habilitación |
| **Inicio Automático** | Gestión de `.desktop` en autostart — habilitar/deshabilitar por usuario |
| **Desinstalador** | Buscar y desinstalar paquetes APT con una acción |
| **Monitor de Recursos** | Gráficas en tiempo real: CPU, RAM, Red ↑↓ + barras por núcleo |
| **Repositorios** | Ver, activar/desactivar y eliminar entradas de APT sources |

---

## Requisitos

```
python3 >= 3.10
PyQt6   >= 6.4
psutil  >= 5.9
pkexec  (para operaciones con sudo — polkit)
```

---

## Instalación rápida

### Desde PyPI
```bash
pip install PyQt6 psutil --break-system-packages
python3 stacer2026.py
```

### Como paquete .deb
```bash
chmod +x build_deb.sh
./build_deb.sh
sudo apt install ./dist/stacer2026_1.0.0_all.deb
stacer2026
```

### En Debian/Ubuntu/MX Linux/ArgOs Platinum
```bash
sudo apt install python3-pyqt6 python3-psutil
python3 stacer2026.py
```

---

## Estructura del proyecto

```
stacer2026/
├── stacer2026.py       # Aplicación principal (único archivo fuente)
├── requirements.txt    # Dependencias Python
├── build_deb.sh        # Script de empaquetado .deb
└── README.md
```

---

## Capturas de pantalla (módulos)

- **Dashboard**: 3 gauges circulares animados con easing suave, cards de sistema, red y disco.
- **Limpiador**: Escaneo de tamaños antes de limpiar, log en tiempo real del proceso.
- **Recursos**: 4 gráficas de línea con relleno degradado + barras verticales por núcleo.
- **Servicios**: Tabla de todos los servicios systemd con color-coding por estado.

---

## Notas de desarrollo

- Construido con **PyQt6** puro — sin dependencias de terceros de UI.
- Todas las gráficas son **QPainter** nativo — sin matplotlib ni pyqtgraph.
- Workers en **QThread** para todas las operaciones de sistema — UI nunca se bloquea.
- Compatibilidad verificada con **Debian 12, Ubuntu 22.04/24.04, MX Linux KDE, ArgOs Platinum Edition**.
- Fuentes: Ubuntu → Liberation Sans → DejaVu Sans (fallback chain Linux-compatible).

---

## Licencia

MIT — Úsalo, modifícalo, distribúyelo.

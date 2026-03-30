# Stacer 2026

**Reimaginación moderna de Stacer — construida con PyQt6/PyQt5, datos 100% reales del sistema.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt](https://img.shields.io/badge/PyQt-6%20%7C%205-green)
![License](https://img.shields.io/badge/License-MIT-purple)
![Platform](https://img.shields.io/badge/Platform-Linux-orange)
![Arch](https://img.shields.io/badge/Arch-x86__64-lightgrey)

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

## Compatibilidad Qt — Detección Automática

Stacer 2026 detecta automáticamente qué librería Qt está disponible en tu sistema, **sin necesidad de configurar nada**:

| Librería | CPUs compatibles | Notas |
|----------|-----------------|-------|
| **PyQt6** | CPUs modernos (2012+) con SSE4.1 / SSE4.2 / POPCNT | Prioridad 1 |
| **PyQt5** | CPUs legacy — cualquier x86_64 | Fallback automático |

La lógica de detección al arrancar:
```
→ Intenta cargar PyQt6
    ✓ Disponible y compatible  →  usa PyQt6
    ✗ Error (CPU legacy / no instalado)  →  cae a PyQt5 automáticamente
```

No se requiere ningún cambio en el código ni en la configuración. La app simplemente funciona.

---

## Requisitos

```
python3     >= 3.10
psutil      >= 5.9
PyQt6       >= 6.4   (CPUs modernos)
  ó
PyQt5       >= 5.15  (CPUs legacy / fallback)

pkexec      (para operaciones con sudo — polkit)
```

---

## Instalación rápida

### Opción A — Directa (sin .deb)
```bash
# CPUs modernos
sudo apt install python3-pyqt6 python3-psutil
python3 stacer2026.py

# CPUs legacy (sin SSE4.2)
sudo apt install python3-pyqt5 python3-psutil
python3 stacer2026.py
```

### Opción B — Paquete .deb (recomendado)
```bash
# Opcional: para generar PNGs del ícono
sudo apt install librsvg2-bin

# Construir
chmod +x build_deb.sh
./build_deb.sh

# Instalar
sudo apt install ./dist/stacer2026_1.0.0_all.deb
stacer2026
```

> El `postinst` detecta automáticamente cuál Qt instalar en cada máquina.

### En Debian / Ubuntu / LMDE / MX Linux / ArgOs Platinum
```bash
sudo apt install python3-pyqt5 python3-psutil   # funciona en cualquier CPU
python3 stacer2026.py
```

---

## Estructura del proyecto

```
stacer2026/
├── stacer2026.py       # Aplicación principal — PyQt6/PyQt5 auto-detect
├── stacer2026.svg      # Ícono vectorial (512×512)
├── requirements.txt    # Dependencias Python
├── build_deb.sh        # Script de empaquetado .deb
└── README.md
```

---

## Notas técnicas

- **PyQt6/PyQt5** — detección automática en runtime, sin flags ni variables de entorno.
- Todas las gráficas son **QPainter nativo** — sin matplotlib ni pyqtgraph.
- Workers en **QThread** — la UI nunca se bloquea en operaciones de sistema.
- Compatibilidad verificada: **Debian 12, Ubuntu 22.04/24.04, LMDE 7, MX Linux KDE, ArgOs Platinum**.
- Fuentes: Ubuntu → Liberation Sans → DejaVu Sans (fallback chain Linux-compatible).
- Ícono SVG con gradiente morado→cyan, coherente con el diseño de la app.

---

## Historial de versiones

| Versión | Cambios |
|---------|---------|
| **1.0.0** | Lanzamiento inicial con PyQt6 |
| **1.0.1** | Compatibilidad automática PyQt6/PyQt5 — soporte CPU legacy |

---

## Licencia

MIT — Úsalo, modifícalo, distribúyelo.

---

*Desarrollado por Andrés Tapia · 2026*


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-58-27" src="https://github.com/user-attachments/assets/3aab13a6-2080-4d3c-963f-3301e0254901" />


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-58-44" src="https://github.com/user-attachments/assets/e86f3388-24e1-4272-8dc5-0073d62a60ec" />


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-58-57" src="https://github.com/user-attachments/assets/cecbdc0d-dbba-4f04-96e2-43c56dd7a7c6" />


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-59-10" src="https://github.com/user-attachments/assets/38a1bd65-efc4-402e-9157-26f3db39bd4d" />


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-59-23" src="https://github.com/user-attachments/assets/99e46832-be4e-476f-ac9a-601207add40a" />


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-59-37" src="https://github.com/user-attachments/assets/a0108734-02c5-4919-acf8-1a114586e115" />


<img width="1440" height="900" alt="Captura de pantalla de 2026-03-28 19-59-47" src="https://github.com/user-attachments/assets/e6eaa898-1d42-417e-b2c7-548f6ac39866" />

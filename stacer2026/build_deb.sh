#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  build_deb.sh — Construye el paquete .deb de Stacer 2026
#  Compatible con PyQt6 y PyQt5 (detección automática en runtime)
# ─────────────────────────────────────────────────────────────────
set -e

APP="stacer2026"
VERSION="1.0.0"
ARCH="all"
PKG="${APP}_${VERSION}_${ARCH}"
BUILD_DIR="dist/${PKG}"

echo "==> Limpiando build anterior..."
rm -rf dist/
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/${APP}"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/pixmaps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/48x48/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps"

echo "==> Copiando archivos..."
cp stacer2026.py "${BUILD_DIR}/usr/lib/${APP}/"
chmod 644 "${BUILD_DIR}/usr/lib/${APP}/stacer2026.py"

# ── Ícono SVG ────────────────────────────────────────────────────
if [ -f "stacer2026.svg" ]; then
    cp stacer2026.svg "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/stacer2026.svg"
    cp stacer2026.svg "${BUILD_DIR}/usr/share/pixmaps/stacer2026.svg"
    chmod 644 "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/stacer2026.svg"
    chmod 644 "${BUILD_DIR}/usr/share/pixmaps/stacer2026.svg"
    for SIZE in 48 128 256; do
        if command -v rsvg-convert &>/dev/null; then
            rsvg-convert -w "${SIZE}" -h "${SIZE}" stacer2026.svg \
                -o "${BUILD_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/stacer2026.png"
            chmod 644 "${BUILD_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/stacer2026.png"
        elif command -v inkscape &>/dev/null; then
            inkscape --export-type=png \
                --export-width="${SIZE}" --export-height="${SIZE}" \
                --export-filename="${BUILD_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/stacer2026.png" \
                stacer2026.svg 2>/dev/null
            chmod 644 "${BUILD_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/stacer2026.png"
        fi
    done
    echo "   Icono instalado"
fi

# Launcher
cat > "${BUILD_DIR}/usr/bin/stacer2026" << 'EOF'
#!/bin/bash
exec python3 /usr/lib/stacer2026/stacer2026.py "$@"
EOF
chmod +x "${BUILD_DIR}/usr/bin/stacer2026"

# .desktop
cat > "${BUILD_DIR}/usr/share/applications/stacer2026.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Stacer 2026
GenericName=Linux System Optimizer
Comment=Optimizador y monitor del sistema para Linux
Exec=stacer2026
Icon=stacer2026
Terminal=false
Categories=System;Settings;
Keywords=system;optimizer;cleaner;monitor;linux;stacer;
StartupNotify=true
StartupWMClass=stacer2026
EOF

# DEBIAN/control  — acepta PyQt6 O PyQt5
cat > "${BUILD_DIR}/DEBIAN/control" << EOF
Package: ${APP}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: Andrés Tapia <andres@example.com>
Depends: python3 (>= 3.10), python3-psutil
Recommends: pkexec, librsvg2-bin
Section: utils
Priority: optional
Description: Stacer 2026 - Modern Linux System Optimizer
 Reimaginacion moderna de Stacer construida con PyQt6/PyQt5.
 Detecta automaticamente la libreria Qt disponible en el sistema.
 Incluye dashboard, limpiador, optimizador, servicios, inicio
 automatico, desinstalador, monitor de recursos y repositorios.
 .
 Datos 100% reales. Sin simulacion. Compatible con CPU legacy.
EOF

# postinst — instala la mejor Qt disponible
cat > "${BUILD_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

chmod 644 /usr/lib/stacer2026/stacer2026.py 2>/dev/null || true
chmod 755 /usr/bin/stacer2026               2>/dev/null || true

# Actualizar cache de íconos
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# Instalar Qt: intentar PyQt6 primero, si falla usar PyQt5
install_qt() {
    if python3 -c "import PyQt6" 2>/dev/null; then
        echo "PyQt6 ya disponible."
        return 0
    fi
    if python3 -c "import PyQt5" 2>/dev/null; then
        echo "PyQt5 ya disponible."
        return 0
    fi
    echo "Instalando PyQt6..."
    if apt-get install -y python3-pyqt6 2>/dev/null; then return 0; fi
    if pip3 install PyQt6 --break-system-packages 2>/dev/null; then return 0; fi
    echo "PyQt6 no compatible con este CPU, instalando PyQt5..."
    if apt-get install -y python3-pyqt5 2>/dev/null; then return 0; fi
    if pip3 install PyQt5 --break-system-packages 2>/dev/null; then return 0; fi
    if pip3 install PyQt5 2>/dev/null; then return 0; fi
    echo "AVISO: Instala manualmente: sudo apt install python3-pyqt5"
}

install_psutil() {
    if python3 -c "import psutil" 2>/dev/null; then return 0; fi
    echo "Instalando psutil..."
    if apt-get install -y python3-psutil 2>/dev/null; then return 0; fi
    if pip3 install psutil --break-system-packages 2>/dev/null; then return 0; fi
    echo "AVISO: Instala manualmente: sudo apt install python3-psutil"
}

install_qt
install_psutil

echo ""
echo "Stacer 2026 instalado correctamente."
echo "Ejecuta: stacer2026"
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# postrm
cat > "${BUILD_DIR}/DEBIAN/postrm" << 'EOF'
#!/bin/bash
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"

echo "==> Fijando permisos finales..."
find "${BUILD_DIR}" -type d -exec chmod 755 {} \;
find "${BUILD_DIR}" -type f -exec chmod 644 {} \;
chmod 755 "${BUILD_DIR}/usr/bin/stacer2026"
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"

echo "==> Construyendo .deb..."
dpkg-deb --build --root-owner-group "${BUILD_DIR}"

echo ""
echo "✅  Paquete creado: dist/${PKG}.deb"
echo "    Instalar con:   sudo apt install ./dist/${PKG}.deb"

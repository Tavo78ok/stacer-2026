#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║        Stacer 2026 — Modern Linux System Optimizer            ║
║        PyQt6/PyQt5 · Real System Data · No Simulation v1.0.0 ║
╚═══════════════════════════════════════════════════════════════╝
"""

import sys, os, subprocess, psutil, shutil, glob, re, time, socket, platform
from collections import deque
from datetime import datetime
from pathlib import Path

# ── Detección de CPU antes de importar Qt ────────────────────────────────────
def _cpu_has_pyqt6() -> bool:
    """Verifica si el CPU tiene SSE4.1/SSE4.2/POPCNT requeridos por PyQt6."""
    try:
        flags = open("/proc/cpuinfo").read()
        required = {"sse4_1", "sse4_2", "popcnt"}
        present  = set(re.findall(r'\b(sse4_1|sse4_2|popcnt)\b', flags))
        return required.issubset(present)
    except Exception:
        return False

_USE_QT6 = _cpu_has_pyqt6()

if _USE_QT6:
    try:
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QPushButton, QFrame, QScrollArea, QTableWidget,
            QTableWidgetItem, QHeaderView, QCheckBox, QLineEdit, QProgressBar,
            QStackedWidget, QMessageBox, QSizePolicy, QAbstractItemView,
            QTextEdit, QGridLayout, QButtonGroup
        )
        from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QSize
        from PyQt6.QtGui import (
            QColor, QFont, QPainter, QPen, QBrush, QPainterPath,
            QLinearGradient, QPalette, QCursor
        )
        print("Stacer 2026: usando PyQt6")
    except ImportError:
        _USE_QT6 = False

if not _USE_QT6:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QFrame, QScrollArea, QTableWidget,
        QTableWidgetItem, QHeaderView, QCheckBox, QLineEdit, QProgressBar,
        QStackedWidget, QMessageBox, QSizePolicy, QAbstractItemView,
        QTextEdit, QGridLayout, QButtonGroup
    )
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QSize
    from PyQt5.QtGui import (
        QColor, QFont, QPainter, QPen, QBrush, QPainterPath,
        QLinearGradient, QPalette, QCursor
    )
    print("Stacer 2026: usando PyQt5 (CPU legacy)")

# ── Normalización de enums Qt6 → compatibles con Qt5 ─────────────────────────
if _USE_QT6:
    Qt.AlignCenter              = Qt.AlignmentFlag.AlignCenter
    Qt.AlignVCenter             = Qt.AlignmentFlag.AlignVCenter
    Qt.AlignLeft                = Qt.AlignmentFlag.AlignLeft
    Qt.AlignRight               = Qt.AlignmentFlag.AlignRight
    Qt.AlignBottom              = Qt.AlignmentFlag.AlignBottom
    Qt.PointingHandCursor       = Qt.CursorShape.PointingHandCursor
    Qt.ScrollBarAlwaysOff       = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    Qt.Vertical                 = Qt.Orientation.Vertical
    Qt.NoPen                    = Qt.PenStyle.NoPen
    Qt.RoundCap                 = Qt.PenCapStyle.RoundCap
    QFont.Bold                  = QFont.Weight.Bold
    QPainter.Antialiasing       = QPainter.RenderHint.Antialiasing
    QFrame.NoFrame              = QFrame.Shape.NoFrame
    QAbstractItemView.SelectRows     = QAbstractItemView.SelectionBehavior.SelectRows
    QAbstractItemView.NoEditTriggers = QAbstractItemView.EditTrigger.NoEditTriggers
    QHeaderView.ResizeToContents     = QHeaderView.ResizeMode.ResizeToContents
    QHeaderView.Stretch              = QHeaderView.ResizeMode.Stretch
    QMessageBox.Yes             = QMessageBox.StandardButton.Yes
    QMessageBox.No              = QMessageBox.StandardButton.No

# ─────────────────────── PALETTE ─────────────────────────────────────────────

class C:
    BG      = "#0d0f1a"
    SIDEBAR = "#11142b"
    CARD    = "#181b35"
    CARD2   = "#1e2248"
    BORDER  = "#262a55"
    TEXT    = "#e8eaf6"
    DIM     = "#6b6f9a"
    ACCENT  = "#7c4dff"
    CYAN    = "#00e5ff"
    GREEN   = "#00e676"
    AMBER   = "#ffd740"
    RED     = "#ff5252"
    PINK    = "#f06292"
    # Chart aliases
    CPU     = "#7c4dff"
    RAM     = "#00e5ff"
    DISK    = "#00e676"
    NET     = "#ffd740"

VERSION = "1.0.0"

# ─────────────────────── UTILITIES ───────────────────────────────────────────

def bytes_hr(n: float) -> str:
    n = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

def uptime_str(boot_ts: float) -> str:
    secs = int(time.time() - boot_ts)
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"

def sh(cmd: str, sudo: bool = False) -> str:
    try:
        if sudo:
            cmd = f"pkexec sh -c '{cmd}'"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception:
        return ""

def dir_size(path: str) -> int:
    total = 0
    try:
        for p in Path(path).rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except Exception:
                    pass
    except Exception:
        pass
    return total

# ─────────────────────── WORKER THREADS ──────────────────────────────────────

class SystemWorker(QThread):
    updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._go       = True
        self._prev_net = None

    def run(self):
        while self._go:
            try:
                cpu  = psutil.cpu_percent(interval=1)
                ram  = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                net  = psutil.net_io_counters()
                freq = psutil.cpu_freq()

                net_up = net_dn = 0
                if self._prev_net:
                    net_up = max(0, net.bytes_sent - self._prev_net.bytes_sent)
                    net_dn = max(0, net.bytes_recv - self._prev_net.bytes_recv)
                self._prev_net = net

                temps: dict = {}
                try:
                    temps = psutil.sensors_temperatures() or {}
                except Exception:
                    pass

                self.updated.emit({
                    "cpu":        cpu,
                    "cpu_cores":  psutil.cpu_count(logical=False) or 1,
                    "cpu_lcores": psutil.cpu_count(logical=True)  or 1,
                    "cpu_freq":   freq.current if freq else 0,
                    "ram_pct":    ram.percent,
                    "ram_used":   ram.used,
                    "ram_total":  ram.total,
                    "ram_avail":  ram.available,
                    "disk_pct":   disk.percent,
                    "disk_used":  disk.used,
                    "disk_total": disk.total,
                    "disk_free":  disk.free,
                    "net_up":     net_up,
                    "net_dn":     net_dn,
                    "net_up_tot": net.bytes_sent,
                    "net_dn_tot": net.bytes_recv,
                    "temps":      temps,
                    "procs":      len(psutil.pids()),
                    "boot":       psutil.boot_time(),
                })
            except Exception:
                pass

    def stop(self):
        self._go = False
        self.wait(3000)


class ScanWorker(QThread):
    result = pyqtSignal(dict)

    def run(self):
        self.result.emit({
            "pkg":   dir_size("/var/cache/apt/archives/"),
            "logs":  dir_size("/var/log"),
            "crash": dir_size("/var/crash/"),
            "thumb": dir_size(str(Path.home() / ".cache/thumbnails")),
            "trash": dir_size(str(Path.home() / ".local/share/Trash")),
        })


class CleanWorker(QThread):
    log  = pyqtSignal(str)
    done = pyqtSignal(int)

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks

    def run(self):
        total = 0

        if "pkg" in self.tasks:
            self.log.emit("Limpiando cache de APT...")
            before = dir_size("/var/cache/apt/archives/")
            sh("apt-get clean -y", sudo=True)
            freed = max(0, before - dir_size("/var/cache/apt/archives/"))
            total += freed
            self.log.emit(f"  OK  APT cache: {bytes_hr(freed)} liberados")

        if "journal" in self.tasks:
            self.log.emit("Comprimiendo journal del sistema...")
            sh("journalctl --vacuum-time=7d", sudo=True)
            self.log.emit("  OK  Journal reducido a 7 dias")

        if "logs" in self.tasks:
            self.log.emit("Eliminando logs rotados...")
            freed = 0
            for pat in ["/var/log/**/*.gz", "/var/log/**/*.1", "/var/log/**/*.old"]:
                for f in glob.glob(pat, recursive=True):
                    try:
                        freed += os.path.getsize(f)
                        sh(f"rm -f '{f}'", sudo=True)
                    except Exception:
                        pass
            total += freed
            self.log.emit(f"  OK  Logs rotados: {bytes_hr(freed)} liberados")

        if "crash" in self.tasks:
            self.log.emit("Limpiando reportes de crash...")
            freed = dir_size("/var/crash/")
            sh("rm -rf /var/crash/*", sudo=True)
            total += freed
            self.log.emit(f"  OK  Crash reports: {bytes_hr(freed)} liberados")

        if "thumb" in self.tasks:
            self.log.emit("Limpiando miniaturas en cache...")
            p = Path.home() / ".cache/thumbnails"
            freed = dir_size(str(p))
            shutil.rmtree(str(p), ignore_errors=True)
            total += freed
            self.log.emit(f"  OK  Miniaturas: {bytes_hr(freed)} liberados")

        if "trash" in self.tasks:
            self.log.emit("Vaciando papelera...")
            p = Path.home() / ".local/share/Trash"
            freed = dir_size(str(p))
            shutil.rmtree(str(p), ignore_errors=True)
            p.mkdir(parents=True, exist_ok=True)
            (p / "files").mkdir(exist_ok=True)
            (p / "info").mkdir(exist_ok=True)
            total += freed
            self.log.emit(f"  OK  Papelera: {bytes_hr(freed)} liberados")

        if "fontcache" in self.tasks:
            self.log.emit("Reconstruyendo cache de fuentes...")
            sh("fc-cache -f -v")
            self.log.emit("  OK  Cache de fuentes reconstruido")

        self.log.emit(f"\n>>> Limpieza completa: {bytes_hr(total)} liberados")
        self.done.emit(total)


class PackagesWorker(QThread):
    result = pyqtSignal(list)

    def run(self):
        rows = []
        try:
            out = subprocess.run(
                ["dpkg-query", "-W",
                 "-f=${Package}\t${Version}\t${binary:Summary}\n"],
                capture_output=True, text=True, timeout=25
            ).stdout
            for line in out.strip().splitlines():
                parts = line.split("\t", 2)
                if len(parts) == 3:
                    rows.append(tuple(parts))
        except Exception:
            pass
        self.result.emit(rows)


class ServicesWorker(QThread):
    result = pyqtSignal(list)

    def run(self):
        rows = []
        try:
            out = subprocess.run(
                ["systemctl", "list-units", "--type=service",
                 "--all", "--no-pager", "--no-legend"],
                capture_output=True, text=True, timeout=12
            ).stdout
            for line in out.strip().splitlines():
                parts = line.split(None, 4)
                if len(parts) < 4:
                    continue
                name   = parts[0].replace("●", "").strip()
                active = parts[2]
                sub    = parts[3]
                desc   = parts[4].strip() if len(parts) > 4 else ""
                en     = sh(f"systemctl is-enabled {name} 2>/dev/null")
                rows.append((name, active, sub, en.strip(), desc))
        except Exception:
            pass
        self.result.emit(rows)


# ─────────────────────── CUSTOM WIDGETS ──────────────────────────────────────

class CircleGauge(QWidget):
    """Animated circular gauge with smooth easing."""

    def __init__(self, label: str = "", color: str = C.ACCENT, parent=None):
        super().__init__(parent)
        self._val    = 0.0
        self._target = 0.0
        self._label  = label
        self._color  = QColor(color)
        self._sub    = ""
        self.setMinimumSize(164, 190)

        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(16)

    def set_value(self, v: float, sub: str = ""):
        self._target = max(0.0, min(100.0, float(v)))
        self._sub    = sub

    def _tick(self):
        diff = self._target - self._val
        if abs(diff) > 0.2:
            self._val += diff * 0.10
            self.update()
        elif self._val != self._target:
            self._val = self._target
            self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h  = self.width(), self.height()
        size  = min(w, h) - 28
        x     = (w - size) // 2
        y     = 8
        rect  = QRect(x, y, size, size)

        # Track
        pen = QPen(QColor(C.BORDER))
        pen.setWidth(11)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 225 * 16, -270 * 16)

        # Arc
        if self._val > 0:
            arc_pen = QPen(self._color)
            arc_pen.setWidth(11)
            arc_pen.setCapStyle(Qt.RoundCap)
            p.setPen(arc_pen)
            p.drawArc(rect, 225 * 16, int(-270 * 16 * self._val / 100))

        # Centre glow dot
        cx = x + size // 2
        cy = y + size // 2
        rad = size // 2 - 20
        grad = QLinearGradient(cx - 20, cy - 20, cx + 20, cy + 20)
        c1 = QColor(self._color); c1.setAlpha(30)
        c2 = QColor(self._color); c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - rad, cy - rad, rad * 2, rad * 2)

        # Percentage text
        vf = QFont("Ubuntu")
        vf.setPointSize(23)
        vf.setBold(True)
        p.setFont(vf)
        p.setPen(QColor(C.TEXT))
        p.drawText(rect, Qt.AlignCenter, f"{int(self._val)}%")

        # Label
        lf = QFont("Ubuntu")
        lf.setPointSize(10)
        lf.setBold(True)
        p.setFont(lf)
        p.setPen(self._color)
        p.drawText(QRect(x, y + size + 4, size, 20),
                   Qt.AlignCenter, self._label)

        # Sub-label
        if self._sub:
            sf = QFont("Ubuntu")
            sf.setPointSize(8)
            p.setFont(sf)
            p.setPen(QColor(C.DIM))
            p.drawText(QRect(x, y + size + 22, size, 16),
                       Qt.AlignCenter, self._sub)
        p.end()


class LiveChart(QWidget):
    """Scrolling filled line chart."""

    def __init__(self, label: str = "", color: str = C.ACCENT, parent=None):
        super().__init__(parent)
        self._data  = deque([0.0] * 60, maxlen=60)
        self._color = QColor(color)
        self._label = label
        self._unit  = "%"
        self.setMinimumHeight(120)

    def push(self, v: float):
        self._data.append(max(0.0, float(v)))
        self.update()

    def set_unit(self, u: str):
        self._unit = u

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h   = self.width(), self.height()
        pad    = 10
        cw     = w - 2 * pad
        ch     = h - 2 * pad - 18
        data   = list(self._data)
        n      = len(data)
        mx     = max(max(data), 1.0)

        # Background
        p.fillRect(0, 0, w, h, QColor(C.CARD))

        # Grid lines
        gpen = QPen(QColor(C.BORDER))
        gpen.setWidth(1)
        p.setPen(gpen)
        for i in range(1, 4):
            gy = pad + int(ch * i / 4)
            p.drawLine(pad, gy, w - pad, gy)

        if n < 2:
            p.end(); return

        step  = cw / (n - 1)
        path  = QPainterPath()
        fpath = QPainterPath()
        fpath.moveTo(pad, pad + ch)

        for i, v in enumerate(data):
            x = pad + i * step
            y = pad + ch - (v / mx * ch)
            if i == 0:
                path.moveTo(x, y)
                fpath.lineTo(x, y)
            else:
                path.lineTo(x, y)
                fpath.lineTo(x, y)

        fpath.lineTo(pad + (n - 1) * step, pad + ch)
        fpath.closeSubpath()

        # Gradient fill
        grad = QLinearGradient(0, pad, 0, pad + ch)
        c1 = QColor(self._color); c1.setAlpha(90)
        c2 = QColor(self._color); c2.setAlpha(8)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.fillPath(fpath, QBrush(grad))

        # Line
        lpen = QPen(self._color)
        lpen.setWidth(2)
        p.setPen(lpen)
        p.drawPath(path)

        # Label
        lf = QFont("Ubuntu"); lf.setPointSize(8)
        p.setFont(lf)
        p.setPen(QColor(C.DIM))
        cur = data[-1]
        val_str = (bytes_hr(cur) + "/s") if self._unit != "%" else f"{cur:.1f}%"
        p.drawText(pad, h - 3, f"{self._label}  {val_str}")

        p.end()


class SidebarBtn(QPushButton):
    """Custom-painted sidebar navigation button."""

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFlat(True)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        checked = self.isChecked()
        hovered = self.underMouse()

        if checked:
            p.fillRect(0, 0, w, h, QColor("#1c2055"))
        elif hovered:
            p.fillRect(0, 0, w, h, QColor("#161938"))
        else:
            p.fillRect(0, 0, w, h, QColor(C.SIDEBAR))

        # Left accent bar when active
        if checked:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(C.ACCENT))
            p.drawRoundedRect(0, 10, 4, h - 20, 2, 2)

        # Icon
        if_  = QFont("Ubuntu"); if_.setPointSize(13)
        p.setFont(if_)
        p.setPen(QColor(C.ACCENT if checked else C.DIM))
        p.drawText(QRect(14, 0, 32, h),
                   Qt.AlignVCenter | Qt.AlignCenter,
                   self._icon)

        # Label
        lf = QFont("Ubuntu"); lf.setPointSize(10)
        if checked: lf.setBold(True)
        p.setFont(lf)
        p.setPen(QColor(C.TEXT if checked else C.DIM))
        p.drawText(QRect(50, 0, w - 58, h), Qt.AlignVCenter, self._label)

        p.end()


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("s26-card")
        self.setStyleSheet(
            f"QFrame#s26-card {{ background:{C.CARD}; "
            f"border:1px solid {C.BORDER}; border-radius:12px; }}"
        )


def mk_btn(label: str, color: str = C.ACCENT) -> QPushButton:
    b = QPushButton(label)
    b.setCursor(QCursor(Qt.PointingHandCursor))
    b.setFixedHeight(36)
    b.setFont(QFont("Ubuntu", 10))
    lighter = QColor(color).lighter(125).name()
    darker  = QColor(color).darker(110).name()
    b.setStyleSheet(f"""
        QPushButton {{
            background:{color}; color:white; border:none;
            border-radius:8px; padding:0 18px; font-weight:bold;
        }}
        QPushButton:hover   {{ background:{lighter}; }}
        QPushButton:pressed {{ background:{darker};  }}
        QPushButton:disabled {{ background:#2a2d50; color:#444; }}
    """)
    return b


def mk_search(placeholder: str = "Buscar...", width: int = 240) -> QLineEdit:
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setFixedWidth(width)
    e.setFixedHeight(34)
    e.setFont(QFont("Ubuntu", 10))
    e.setStyleSheet(f"""
        QLineEdit {{
            background:{C.CARD2}; color:{C.TEXT};
            border:1px solid {C.BORDER}; border-radius:8px; padding:0 12px;
        }}
        QLineEdit:focus {{ border-color:{C.ACCENT}; }}
    """)
    return e


class StyledTable(QTableWidget):
    def __init__(self, cols: int, headers: list, parent=None):
        super().__init__(0, cols, parent)
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setStyleSheet(f"""
            QTableWidget {{
                background:{C.CARD}; alternate-background-color:{C.CARD2};
                color:{C.TEXT}; border:none; selection-background-color:#2a2d5a;
            }}
            QTableWidget::item {{ padding:5px 10px; border:none; }}
            QHeaderView::section {{
                background:{C.SIDEBAR}; color:{C.DIM}; font-size:9px;
                font-weight:bold; padding:8px 10px; border:none;
                border-bottom:1px solid {C.BORDER}; text-transform:uppercase;
            }}
            QScrollBar:vertical {{
                background:{C.SIDEBAR}; width:6px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:{C.BORDER}; border-radius:3px; min-height:20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)


def section_title(text: str, color: str = C.TEXT) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Ubuntu", 18, QFont.Bold))
    lbl.setStyleSheet(f"color:{color};")
    return lbl


def card_title(text: str, color: str = C.ACCENT) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Ubuntu", 12, QFont.Bold))
    lbl.setStyleSheet(f"color:{color};")
    return lbl


# ─────────────────────── PAGES ───────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        root.addWidget(section_title("  Panel de Control"))

        # ── Gauges ──────────────────────────────────────────────────────────
        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(14)

        self.cpu_g  = CircleGauge("CPU",   C.CPU)
        self.ram_g  = CircleGauge("RAM",   C.RAM)
        self.disk_g = CircleGauge("DISCO", C.DISK)

        for g in (self.cpu_g, self.ram_g, self.disk_g):
            card = Card()
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 14, 10, 14)
            cl.addWidget(g, alignment=Qt.AlignCenter)
            gauge_row.addWidget(card, 1)

        root.addLayout(gauge_row)

        # ── Info cards ──────────────────────────────────────────────────────
        info_row = QHBoxLayout()
        info_row.setSpacing(14)

        # System info
        sys_card = Card()
        scl = QVBoxLayout(sys_card)
        scl.setContentsMargins(18, 16, 18, 16)
        scl.addWidget(card_title("Sistema", C.ACCENT))
        scl.addSpacing(8)
        self._sys_lbl = {}
        for k in ("Hostname", "OS", "Kernel", "Uptime", "Procesos", "CPU Nucleos"):
            row = QHBoxLayout()
            kl = QLabel(k)
            kl.setFont(QFont("Ubuntu", 9))
            kl.setStyleSheet(f"color:{C.DIM};")
            kl.setFixedWidth(110)
            vl = QLabel("—")
            vl.setFont(QFont("Ubuntu", 9))
            vl.setStyleSheet(f"color:{C.TEXT};")
            vl.setWordWrap(True)
            row.addWidget(kl)
            row.addWidget(vl, 1)
            scl.addLayout(row)
            self._sys_lbl[k] = vl
        scl.addStretch()
        info_row.addWidget(sys_card, 1)

        # Network card
        net_card = Card()
        ncl = QVBoxLayout(net_card)
        ncl.setContentsMargins(18, 16, 18, 16)
        ncl.addWidget(card_title("Red", C.CYAN))
        ncl.addSpacing(8)
        self._net_lbl = {}
        for k in ("Enviado total", "Recibido total", "Velocidad subida", "Velocidad bajada"):
            row = QHBoxLayout()
            kl = QLabel(k)
            kl.setFont(QFont("Ubuntu", 9))
            kl.setStyleSheet(f"color:{C.DIM};")
            kl.setFixedWidth(130)
            vl = QLabel("—")
            vl.setFont(QFont("Ubuntu", 9))
            vl.setStyleSheet(f"color:{C.TEXT};")
            row.addWidget(kl)
            row.addWidget(vl, 1)
            ncl.addLayout(row)
            self._net_lbl[k] = vl
        ncl.addSpacing(10)
        ncl.addWidget(card_title("Temperatura", C.AMBER))
        self._temp_lbl = QLabel("—")
        self._temp_lbl.setFont(QFont("Ubuntu", 9))
        self._temp_lbl.setStyleSheet(f"color:{C.TEXT};")
        ncl.addWidget(self._temp_lbl)
        ncl.addStretch()
        info_row.addWidget(net_card, 1)

        # Disk card
        disk_card = Card()
        dcl = QVBoxLayout(disk_card)
        dcl.setContentsMargins(18, 16, 18, 16)
        dcl.addWidget(card_title("Almacenamiento", C.GREEN))
        dcl.addSpacing(8)
        self._disk_lbl = {}
        for k in ("Usado", "Libre", "Total", "Filesystem"):
            row = QHBoxLayout()
            kl = QLabel(k)
            kl.setFont(QFont("Ubuntu", 9))
            kl.setStyleSheet(f"color:{C.DIM};")
            kl.setFixedWidth(90)
            vl = QLabel("—")
            vl.setFont(QFont("Ubuntu", 9))
            vl.setStyleSheet(f"color:{C.TEXT};")
            row.addWidget(kl)
            row.addWidget(vl, 1)
            dcl.addLayout(row)
            self._disk_lbl[k] = vl
        dcl.addStretch()
        info_row.addWidget(disk_card, 1)

        root.addLayout(info_row)
        root.addStretch()

        # Static info
        self._fill_static()

    def _fill_static(self):
        try:
            self._sys_lbl["Hostname"].setText(socket.gethostname())
        except Exception:
            pass
        try:
            with open("/etc/os-release") as f:
                info = {l.split("=")[0]: l.split("=")[1].strip().strip('"')
                        for l in f if "=" in l}
            self._sys_lbl["OS"].setText(info.get("PRETTY_NAME", platform.system()))
        except Exception:
            self._sys_lbl["OS"].setText(platform.system())
        self._sys_lbl["Kernel"].setText(platform.release())
        try:
            fs = sh("df -T / | tail -1 | awk '{print $2}'")
            self._disk_lbl["Filesystem"].setText(fs or "ext4")
        except Exception:
            pass

    def update_data(self, d: dict):
        self.cpu_g.set_value(d["cpu"], f"{d['cpu_freq']:.0f} MHz")
        self.ram_g.set_value(d["ram_pct"], bytes_hr(d["ram_used"]))
        self.disk_g.set_value(d["disk_pct"], bytes_hr(d["disk_used"]))

        self._sys_lbl["Uptime"].setText(uptime_str(d["boot"]))
        self._sys_lbl["Procesos"].setText(str(d["procs"]))
        self._sys_lbl["CPU Nucleos"].setText(
            f"{d['cpu_cores']} fisicos / {d['cpu_lcores']} logicos"
        )

        self._net_lbl["Enviado total"].setText(bytes_hr(d["net_up_tot"]))
        self._net_lbl["Recibido total"].setText(bytes_hr(d["net_dn_tot"]))
        self._net_lbl["Velocidad subida"].setText(bytes_hr(d["net_up"]) + "/s")
        self._net_lbl["Velocidad bajada"].setText(bytes_hr(d["net_dn"]) + "/s")

        temps = d.get("temps", {})
        if temps:
            readings = [e.current for entries in temps.values() for e in entries]
            if readings:
                avg = sum(readings) / len(readings)
                self._temp_lbl.setText(f"{avg:.1f} °C (promedio)")
        else:
            self._temp_lbl.setText("No disponible")

        self._disk_lbl["Usado"].setText(bytes_hr(d["disk_used"]))
        self._disk_lbl["Libre"].setText(bytes_hr(d["disk_free"]))
        self._disk_lbl["Total"].setText(bytes_hr(d["disk_total"]))


# ── CLEANER ───────────────────────────────────────────────────────────────────

class CleanerPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        root.addWidget(section_title("  Limpiador del Sistema"))

        content = QHBoxLayout()
        content.setSpacing(14)

        # Options card
        opts = Card()
        ol = QVBoxLayout(opts)
        ol.setContentsMargins(20, 18, 20, 18)
        ol.setSpacing(2)
        ol.addWidget(card_title("Selecciona que limpiar"))
        ol.addSpacing(10)

        TASKS = [
            ("pkg",       "Cache de paquetes APT",     "/var/cache/apt/archives"),
            ("journal",   "Journal del sistema",       "Logs de systemd > 7 dias"),
            ("logs",      "Logs rotados (.gz, .1)",    "/var/log/**/*.gz"),
            ("crash",     "Reportes de crash",         "/var/crash/"),
            ("thumb",     "Miniaturas en cache",       "~/.cache/thumbnails"),
            ("trash",     "Papelera",                  "~/.local/share/Trash"),
            ("fontcache", "Cache de fuentes",          "fc-cache -f"),
        ]

        self._checks: dict = {}
        self._size_lbl: dict = {}
        CHK_QSS = f"""
            QCheckBox {{ color:{C.TEXT}; spacing:8px; font-size:10pt; }}
            QCheckBox::indicator {{
                width:18px; height:18px; border-radius:4px;
                border:2px solid {C.BORDER}; background:{C.CARD2};
            }}
            QCheckBox::indicator:checked {{
                background:{C.ACCENT}; border-color:{C.ACCENT};
            }}
        """
        for tid, label, hint in TASKS:
            row = QHBoxLayout()
            row.setContentsMargins(0, 3, 0, 3)
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setStyleSheet(CHK_QSS)
            self._checks[tid] = cb

            hint_lbl = QLabel(hint)
            hint_lbl.setFont(QFont("Ubuntu", 8))
            hint_lbl.setStyleSheet(f"color:{C.DIM};")

            sz_lbl = QLabel("")
            sz_lbl.setFont(QFont("Ubuntu", 9))
            sz_lbl.setStyleSheet(f"color:{C.AMBER};")
            sz_lbl.setFixedWidth(76)
            sz_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._size_lbl[tid] = sz_lbl

            col = QVBoxLayout()
            col.setSpacing(0)
            col.addWidget(cb)
            col.addWidget(hint_lbl)

            row.addLayout(col, 1)
            row.addWidget(sz_lbl)
            ol.addLayout(row)

        ol.addSpacing(14)
        brow = QHBoxLayout()
        self._scan_btn  = mk_btn("Analizar", C.CYAN)
        self._clean_btn = mk_btn("Limpiar",  C.ACCENT)
        self._clean_btn.setEnabled(False)
        brow.addWidget(self._scan_btn)
        brow.addWidget(self._clean_btn)
        ol.addLayout(brow)
        ol.addStretch()
        content.addWidget(opts, 1)

        # Log card
        log_card = Card()
        lcl = QVBoxLayout(log_card)
        lcl.setContentsMargins(16, 16, 16, 16)
        lcl.addWidget(card_title("Registro", C.GREEN))
        lcl.addSpacing(4)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Ubuntu Mono", 9))
        self._log.setStyleSheet(f"""
            QTextEdit {{
                background:{C.BG}; color:{C.GREEN};
                border:none; border-radius:8px; padding:10px;
            }}
        """)
        self._log.setPlaceholderText("Haz clic en 'Analizar' para escanear el sistema...")
        lcl.addWidget(self._log)
        content.addWidget(log_card, 1)

        root.addLayout(content)

        self._scan_btn.clicked.connect(self._scan)
        self._clean_btn.clicked.connect(self._clean)

    def _scan(self):
        self._scan_btn.setEnabled(False)
        self._log.setText("Analizando sistema...")
        self._sw = ScanWorker()
        self._sw.result.connect(self._on_scan)
        self._sw.start()

    def _on_scan(self, sizes: dict):
        self._scan_btn.setEnabled(True)
        self._clean_btn.setEnabled(True)
        total = sum(sizes.values())
        lines = ["=== Analisis completado ===\n"]
        for tid, sz in sizes.items():
            lbl = self._size_lbl.get(tid)
            if lbl:
                lbl.setText(bytes_hr(sz))
            lines.append(f"  {tid:12s}  {bytes_hr(sz)}")
        lines.append(f"\nTotal recuperable:  {bytes_hr(total)}")
        self._log.setText("\n".join(lines))

    def _clean(self):
        tasks = [tid for tid, cb in self._checks.items() if cb.isChecked()]
        if not tasks:
            return
        self._clean_btn.setEnabled(False)
        self._scan_btn.setEnabled(False)
        self._log.clear()
        self._cw = CleanWorker(tasks)
        self._cw.log.connect(self._log.append)
        self._cw.done.connect(self._on_done)
        self._cw.start()

    def _on_done(self, _total: int):
        self._clean_btn.setEnabled(True)
        self._scan_btn.setEnabled(True)
        for lbl in self._size_lbl.values():
            lbl.setText("")


# ── OPTIMIZER ─────────────────────────────────────────────────────────────────

class OptimizerPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        root.addWidget(section_title("  Optimizador"))

        OPTS = [
            ("Liberar RAM",      "Limpia cache de paginas de memoria del kernel",   C.CYAN,   self._free_ram),
            ("Swappiness = 10",  "Reduce el uso de swap (mejor para SSD/NVMe)",     C.ACCENT, self._swappiness),
            ("TRIM SSD",         "Ejecuta fstrim en la particion raiz",             C.GREEN,  self._trim_ssd),
            ("Cache de fuentes", "Reconstruye el cache de fuentes del sistema",     C.AMBER,  self._font_cache),
            ("APT Autoremove",   "Elimina paquetes huerfanos e innecesarios",       C.RED,    self._autoremove),
            ("Flush DNS",        "Reinicia el servicio de resolucion DNS",          C.PINK,   self._flush_dns),
        ]

        grid = QGridLayout()
        grid.setSpacing(14)

        for i, (name, desc, color, fn) in enumerate(OPTS):
            card = Card()
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)

            nl = QLabel(name)
            nl.setFont(QFont("Ubuntu", 11, QFont.Bold))
            nl.setStyleSheet(f"color:{color};")
            cl.addWidget(nl)

            dl = QLabel(desc)
            dl.setFont(QFont("Ubuntu", 8))
            dl.setStyleSheet(f"color:{C.DIM};")
            dl.setWordWrap(True)
            cl.addWidget(dl)

            cl.addSpacing(6)
            btn = mk_btn("Ejecutar", color)
            btn.clicked.connect(fn)
            cl.addWidget(btn)

            grid.addWidget(card, i // 2, i % 2)

        root.addLayout(grid)

        # Log
        log_card = Card()
        lcl = QVBoxLayout(log_card)
        lcl.setContentsMargins(14, 12, 14, 12)
        lcl.addWidget(card_title("Salida", C.DIM))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Ubuntu Mono", 9))
        self._log.setFixedHeight(130)
        self._log.setStyleSheet(f"""
            QTextEdit {{
                background:{C.BG}; color:{C.GREEN};
                border:none; border-radius:6px; padding:8px;
            }}
        """)
        lcl.addWidget(self._log)
        root.addWidget(log_card)
        root.addStretch()

    def _log(self, msg: str):
        self._log.append(msg)

    def _out(self, msg: str):
        self._log.append(msg)

    def _free_ram(self):
        self._out("Liberando cache de paginas RAM...")
        sh("sync && echo 3 > /proc/sys/vm/drop_caches", sudo=True)
        self._out("  OK  Cache de memoria liberado")

    def _swappiness(self):
        self._out("Configurando vm.swappiness = 10...")
        sh("sysctl vm.swappiness=10", sudo=True)
        self._out("  OK  Swappiness=10 hasta proximo reinicio")

    def _trim_ssd(self):
        self._out("Ejecutando fstrim -v /...")
        out = sh("fstrim -v /", sudo=True)
        self._out(f"  OK  {out or 'TRIM completado'}")

    def _font_cache(self):
        self._out("Reconstruyendo cache de fuentes...")
        sh("fc-cache -f -v")
        self._out("  OK  fc-cache completado")

    def _autoremove(self):
        self._out("Ejecutando apt-get autoremove...")
        sh("apt-get autoremove -y", sudo=True)
        self._out("  OK  Paquetes huerfanos eliminados")

    def _flush_dns(self):
        self._out("Reiniciando systemd-resolved...")
        sh("systemctl restart systemd-resolved", sudo=True)
        self._out("  OK  DNS reiniciado")


# ── SERVICES ──────────────────────────────────────────────────────────────────

class ServicesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._rows: list = []
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(section_title("  Servicios del Sistema"))
        top.addStretch()
        self._search = mk_search("Buscar servicio...")
        self._search.textChanged.connect(self._filter)
        top.addWidget(self._search)
        ref = mk_btn("Actualizar", C.ACCENT)
        ref.setFixedWidth(110)
        ref.clicked.connect(self._load)
        top.addWidget(ref)
        root.addLayout(top)

        self._table = StyledTable(5, ["Nombre", "Estado", "Sub-estado", "Habilitado", "Descripcion"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        root.addWidget(self._table)

        btn_row = QHBoxLayout()
        for label, color, action in [
            ("Iniciar",       C.GREEN,  "start"),
            ("Detener",       C.RED,    "stop"),
            ("Reiniciar",     C.AMBER,  "restart"),
            ("Habilitar",     C.ACCENT, "enable"),
            ("Deshabilitar",  C.DIM,    "disable"),
        ]:
            b = mk_btn(label, color)
            b.clicked.connect(lambda _, a=action: self._action(a))
            btn_row.addWidget(b)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._load()

    def _load(self):
        self._table.setRowCount(0)
        self._rows = []
        self._sw = ServicesWorker()
        self._sw.result.connect(self._populate)
        self._sw.start()

    def _populate(self, rows: list):
        self._rows = rows
        self._show(rows)

    def _show(self, rows: list):
        self._table.setRowCount(0)
        for name, active, sub, enabled, desc in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, QTableWidgetItem(name))

            ai = QTableWidgetItem(active)
            ai.setForeground(QColor(
                C.GREEN if active == "active" else
                C.RED   if active == "failed" else C.DIM
            ))
            self._table.setItem(r, 1, ai)
            self._table.setItem(r, 2, QTableWidgetItem(sub))

            ei = QTableWidgetItem(enabled)
            ei.setForeground(QColor(C.CYAN if enabled == "enabled" else C.DIM))
            self._table.setItem(r, 3, ei)
            self._table.setItem(r, 4, QTableWidgetItem(desc))

    def _filter(self, text: str):
        if not text:
            self._show(self._rows)
            return
        t = text.lower()
        self._show([r for r in self._rows if t in r[0].lower() or t in r[4].lower()])

    def _action(self, action: str):
        row = self._table.currentRow()
        if row < 0:
            return
        name = self._table.item(row, 0).text()
        sh(f"systemctl {action} '{name}'", sudo=True)
        QTimer.singleShot(1000, self._load)


# ── STARTUP APPS ──────────────────────────────────────────────────────────────

class StartupPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(section_title("  Aplicaciones de Inicio"))
        top.addStretch()
        ref = mk_btn("Actualizar", C.ACCENT)
        ref.clicked.connect(self._load)
        top.addWidget(ref)
        root.addLayout(top)

        info = QLabel(
            "  Gestiona las aplicaciones que se ejecutan al iniciar sesion. "
            "Los cambios en /etc/xdg/autostart se aplican solo para tu usuario."
        )
        info.setFont(QFont("Ubuntu", 9))
        info.setStyleSheet(f"color:{C.DIM}; background:{C.CARD}; "
                           f"border-radius:8px; padding:8px;")
        info.setWordWrap(True)
        root.addWidget(info)

        self._table = StyledTable(4, ["Nombre", "Habilitado", "Comando", "Archivo"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        root.addWidget(self._table)

        btn_row = QHBoxLayout()
        dis_btn = mk_btn("Deshabilitar seleccionado", C.RED)
        dis_btn.clicked.connect(self._disable)
        open_btn = mk_btn("Abrir directorio", C.DIM)
        open_btn.clicked.connect(lambda: sh(
            f"xdg-open '{Path.home() / '.config/autostart'}'"
        ))
        btn_row.addWidget(dis_btn)
        btn_row.addWidget(open_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._load()

    def _load(self):
        self._table.setRowCount(0)
        dirs = [
            Path.home() / ".config/autostart",
            Path("/etc/xdg/autostart"),
        ]
        for d in dirs:
            if not d.exists():
                continue
            for f in sorted(d.glob("*.desktop")):
                try:
                    txt = f.read_text(errors="replace")
                    data: dict = {}
                    for ln in txt.splitlines():
                        if "=" in ln:
                            k, _, v = ln.partition("=")
                            data[k.strip()] = v.strip()
                    name    = data.get("Name", f.stem)
                    cmd     = data.get("Exec", "")
                    hidden  = data.get("Hidden", "false").lower() == "true"

                    r = self._table.rowCount()
                    self._table.insertRow(r)
                    self._table.setItem(r, 0, QTableWidgetItem(name))

                    st = QTableWidgetItem("No" if hidden else "Si")
                    st.setForeground(QColor(C.DIM if hidden else C.GREEN))
                    self._table.setItem(r, 1, st)
                    self._table.setItem(r, 2, QTableWidgetItem(cmd))
                    self._table.setItem(r, 3, QTableWidgetItem(str(f)))
                except Exception:
                    pass

    def _disable(self):
        row = self._table.currentRow()
        if row < 0:
            return
        path = self._table.item(row, 3).text()
        try:
            p = Path(path)
            if str(p).startswith(str(Path.home())):
                p.unlink()
            else:
                user_dir = Path.home() / ".config/autostart"
                user_dir.mkdir(parents=True, exist_ok=True)
                dest = user_dir / p.name
                content = p.read_text(errors="replace")
                if "Hidden=" in content:
                    content = re.sub(r"Hidden=\S*", "Hidden=true", content)
                else:
                    content += "\nHidden=true\n"
                dest.write_text(content)
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


# ── UNINSTALLER ───────────────────────────────────────────────────────────────

class UninstallerPage(QWidget):
    def __init__(self):
        super().__init__()
        self._all: list = []
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(section_title("  Desinstalador"))
        top.addStretch()
        self._search = mk_search("Buscar paquete...", 260)
        self._search.textChanged.connect(self._filter)
        top.addWidget(self._search)
        load_btn = mk_btn("Cargar paquetes", C.ACCENT)
        load_btn.clicked.connect(self._load)
        top.addWidget(load_btn)
        root.addLayout(top)

        self._table = StyledTable(3, ["Paquete", "Version", "Descripcion"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        root.addWidget(self._table)

        btn_row = QHBoxLayout()
        un_btn = mk_btn("Desinstalar seleccionado", C.RED)
        un_btn.clicked.connect(self._uninstall)
        self._count_lbl = QLabel("Carga los paquetes para comenzar")
        self._count_lbl.setFont(QFont("Ubuntu", 9))
        self._count_lbl.setStyleSheet(f"color:{C.DIM};")
        btn_row.addWidget(un_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._count_lbl)
        root.addLayout(btn_row)

    def _load(self):
        self._table.setRowCount(0)
        self._all = []
        self._count_lbl.setText("Cargando...")
        self._pw = PackagesWorker()
        self._pw.result.connect(self._populate)
        self._pw.start()

    def _populate(self, rows: list):
        self._all = rows
        self._show(rows)

    def _show(self, rows: list):
        self._table.setRowCount(0)
        for name, ver, desc in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, QTableWidgetItem(name))
            self._table.setItem(r, 1, QTableWidgetItem(ver))
            self._table.setItem(r, 2, QTableWidgetItem(desc))
        self._count_lbl.setText(f"{len(rows)} paquetes")

    def _filter(self, text: str):
        if not text:
            self._show(self._all)
            return
        t = text.lower()
        self._show([p for p in self._all
                    if t in p[0].lower() or t in p[2].lower()])

    def _uninstall(self):
        row = self._table.currentRow()
        if row < 0:
            return
        pkg = self._table.item(row, 0).text()
        ans = QMessageBox.question(
            self, "Confirmar desinstalacion",
            f"Desinstalar '{pkg}'?\n\nEsta accion requerira autenticacion.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            sh(f"apt-get remove -y '{pkg}'", sudo=True)
            self._load()


# ── RESOURCES ─────────────────────────────────────────────────────────────────

class ResourcesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._net_max = 1.0
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        root.addWidget(section_title("  Monitor de Recursos"))

        grid = QGridLayout()
        grid.setSpacing(14)

        self._cpu_chart = LiveChart("CPU",       C.CPU)
        self._ram_chart = LiveChart("RAM",       C.RAM)
        self._net_up    = LiveChart("Red subida",C.AMBER)
        self._net_dn    = LiveChart("Red bajada",C.GREEN)
        self._net_up.set_unit("b/s")
        self._net_dn.set_unit("b/s")

        for i, (chart, label) in enumerate([
            (self._cpu_chart, "CPU"),
            (self._ram_chart, "RAM"),
            (self._net_up,    "Red Subida"),
            (self._net_dn,    "Red Bajada"),
        ]):
            card = Card()
            card.setMinimumHeight(150)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 10, 10, 10)
            hdr = QLabel(label)
            hdr.setFont(QFont("Ubuntu", 9, QFont.Bold))
            hdr.setStyleSheet(f"color:{C.DIM};")
            cl.addWidget(hdr)
            cl.addWidget(chart, 1)
            grid.addWidget(card, i // 2, i % 2)

        root.addLayout(grid)

        # Per-core bars
        core_card = Card()
        ccl = QVBoxLayout(core_card)
        ccl.setContentsMargins(16, 12, 16, 12)
        ccl.addWidget(card_title("Uso por nucleo de CPU", C.DIM))

        self._core_bars: list = []
        bars_row = QHBoxLayout()
        bars_row.setSpacing(4)
        bars_row.setAlignment(Qt.AlignLeft)

        n = psutil.cpu_count(logical=True) or 4
        for i in range(n):
            col = QVBoxLayout()
            col.setSpacing(2)
            col.setAlignment(Qt.AlignBottom)

            bar = QProgressBar()
            bar.setOrientation(Qt.Vertical)
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedWidth(22)
            bar.setMinimumHeight(55)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background:{C.BORDER}; border-radius:4px; }}
                QProgressBar::chunk {{ background:{C.CPU}; border-radius:4px; }}
            """)
            lbl = QLabel(f"C{i}")
            lbl.setFont(QFont("Ubuntu", 7))
            lbl.setStyleSheet(f"color:{C.DIM};")
            lbl.setAlignment(Qt.AlignCenter)

            col.addWidget(bar)
            col.addWidget(lbl)
            bars_row.addLayout(col)
            self._core_bars.append(bar)

        ccl.addLayout(bars_row)
        root.addWidget(core_card)
        root.addStretch()

    def update_data(self, d: dict):
        self._cpu_chart.push(d["cpu"])
        self._ram_chart.push(d["ram_pct"])

        up = d["net_up"]
        dn = d["net_dn"]
        self._net_max = max(self._net_max, up, dn, 1.0)
        self._net_up.push(up / self._net_max * 100)
        self._net_dn.push(dn / self._net_max * 100)

        try:
            per_core = psutil.cpu_percent(percpu=True)
            for i, bar in enumerate(self._core_bars):
                if i < len(per_core):
                    bar.setValue(int(per_core[i]))
        except Exception:
            pass


# ── REPOSITORIES ──────────────────────────────────────────────────────────────

class ReposPage(QWidget):
    def __init__(self):
        super().__init__()
        self._entries: list = []
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(section_title("  Repositorios APT"))
        top.addStretch()
        ref = mk_btn("Actualizar", C.ACCENT)
        ref.clicked.connect(self._load)
        top.addWidget(ref)
        root.addLayout(top)

        info = QLabel(
            "  Repositorios configurados en /etc/apt/sources.list y sources.list.d/. "
            "Las modificaciones requieren permisos de administrador."
        )
        info.setFont(QFont("Ubuntu", 9))
        info.setStyleSheet(f"color:{C.DIM}; background:{C.CARD}; "
                           f"border-radius:8px; padding:8px;")
        info.setWordWrap(True)
        root.addWidget(info)

        self._table = StyledTable(4, ["Estado", "Tipo", "Fuente", "Archivo"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        root.addWidget(self._table)

        btn_row = QHBoxLayout()
        tog = mk_btn("Activar / Desactivar", C.AMBER)
        rem = mk_btn("Eliminar repo", C.RED)
        upd = mk_btn("apt-get update", C.GREEN)
        tog.clicked.connect(self._toggle)
        rem.clicked.connect(self._remove)
        upd.clicked.connect(lambda: sh("apt-get update", sudo=True))
        btn_row.addWidget(tog)
        btn_row.addWidget(rem)
        btn_row.addWidget(upd)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._load()

    def _load(self):
        self._table.setRowCount(0)
        self._entries = []

        sources: list = []
        for src in [Path("/etc/apt/sources.list")] + \
                    sorted(Path("/etc/apt/sources.list.d").glob("*.list")
                           if Path("/etc/apt/sources.list.d").exists() else []):
            try:
                for ln in src.read_text(errors="replace").splitlines():
                    sources.append((ln.rstrip(), str(src)))
            except Exception:
                pass

        for raw, fpath in sources:
            stripped = raw.lstrip()
            disabled = stripped.startswith("#")
            clean = stripped.lstrip("# ").strip()
            if not (clean.startswith("deb") or clean.startswith("rpm")):
                continue

            parts = clean.split()
            kind  = parts[0] if parts else "deb"
            body  = " ".join(parts[1:]) if len(parts) > 1 else clean

            r = self._table.rowCount()
            self._table.insertRow(r)

            si = QTableWidgetItem("ACTIVO" if not disabled else "INACTIVO")
            si.setForeground(QColor(C.GREEN if not disabled else C.DIM))
            self._table.setItem(r, 0, si)

            ki = QTableWidgetItem(kind)
            ki.setForeground(QColor(C.CYAN))
            self._table.setItem(r, 1, ki)
            self._table.setItem(r, 2, QTableWidgetItem(body))
            self._table.setItem(r, 3, QTableWidgetItem(Path(fpath).name))

            self._entries.append({
                "raw": raw, "clean": clean, "disabled": disabled, "file": fpath
            })

    def _toggle(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        entry = self._entries[row]
        fpath = entry["file"]
        try:
            content = Path(fpath).read_text(errors="replace")
            if entry["disabled"]:
                new = re.sub(r'^#+\s*(' + re.escape(entry["clean"]) + r')',
                             r'\1', content, flags=re.MULTILINE)
            else:
                new = content.replace(entry["clean"], "# " + entry["clean"], 1)
            self._write_file(fpath, new)
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _remove(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        entry = self._entries[row]
        ans = QMessageBox.question(
            self, "Confirmar", "Eliminar este repositorio?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            try:
                content = Path(entry["file"]).read_text(errors="replace")
                new = content.replace(entry["raw"] + "\n", "")
                new = new.replace(entry["raw"], "")
                self._write_file(entry["file"], new)
                self._load()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _write_file(self, path: str, content: str):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".list", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        sh(f"cp '{tmp_path}' '{path}' && rm -f '{tmp_path}'", sudo=True)


# ─────────────────────── STATUS BAR ──────────────────────────────────────────

class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(28)
        self.setStyleSheet(f"background:{C.SIDEBAR}; border-top:1px solid {C.BORDER};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        self._cpu_lbl  = QLabel("CPU: —")
        self._ram_lbl  = QLabel("RAM: —")
        self._time_lbl = QLabel("")
        self._disk_lbl = QLabel("Disco: —")

        for lbl in (self._cpu_lbl, self._ram_lbl, self._disk_lbl):
            lbl.setFont(QFont("Ubuntu", 8))
            lbl.setStyleSheet(f"color:{C.DIM};")
            layout.addWidget(lbl)

        layout.addStretch()

        self._time_lbl.setFont(QFont("Ubuntu", 8))
        self._time_lbl.setStyleSheet(f"color:{C.DIM};")
        layout.addWidget(self._time_lbl)

        t = QTimer(self)
        t.timeout.connect(self._tick_time)
        t.start(1000)
        self._tick_time()

    def _tick_time(self):
        self._time_lbl.setText(datetime.now().strftime("%A, %d %b %Y  %H:%M:%S"))

    def update_data(self, d: dict):
        self._cpu_lbl.setText(f"CPU: {d['cpu']:.1f}%")
        self._ram_lbl.setText(f"RAM: {d['ram_pct']:.1f}%")
        self._disk_lbl.setText(f"Disco: {d['disk_pct']:.1f}%")


# ─────────────────────── MAIN WINDOW ─────────────────────────────────────────

GLOBAL_QSS = f"""
QMainWindow, QWidget {{ background:{C.BG}; color:{C.TEXT}; }}
QScrollBar:vertical {{
    background:{C.SIDEBAR}; width:6px; border-radius:3px;
}}
QScrollBar::handle:vertical {{
    background:{C.BORDER}; border-radius:3px; min-height:20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:{C.SIDEBAR}; height:6px; }}
QScrollBar::handle:horizontal {{ background:{C.BORDER}; border-radius:3px; }}
QMessageBox {{ background:{C.CARD}; color:{C.TEXT}; }}
QMessageBox QPushButton {{
    background:{C.ACCENT}; color:white; border:none;
    border-radius:6px; padding:6px 16px; min-width:80px;
}}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Stacer 2026  v{VERSION}")
        self.setMinimumSize(1100, 720)
        self.resize(1300, 820)
        self.setStyleSheet(GLOBAL_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Body ────────────────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # ── Sidebar ─────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(224)
        sidebar.setStyleSheet(
            f"background:{C.SIDEBAR}; border-right:1px solid {C.BORDER};"
        )
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(72)
        logo_frame.setStyleSheet(f"background:{C.SIDEBAR};")
        ll = QVBoxLayout(logo_frame)
        ll.setContentsMargins(16, 14, 16, 14)
        top_lbl = QLabel("STACER")
        top_lbl.setFont(QFont("Ubuntu", 20, QFont.Bold))
        top_lbl.setStyleSheet(f"color:{C.ACCENT}; letter-spacing:4px;")
        sub_lbl = QLabel(f"2026  ·  v{VERSION}  ·  Linux Optimizer")
        sub_lbl.setFont(QFont("Ubuntu", 8))
        sub_lbl.setStyleSheet(f"color:{C.DIM};")
        ll.addWidget(top_lbl)
        ll.addWidget(sub_lbl)
        sb.addWidget(logo_frame)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{C.BORDER};")
        sb.addWidget(sep)
        sb.addSpacing(6)

        NAV = [
            ("◈", "Dashboard"),
            ("✦", "Limpiador"),
            ("⚡", "Optimizador"),
            ("⚙", "Servicios"),
            ("↑", "Inicio Automatico"),
            ("✕", "Desinstalador"),
            ("≋", "Recursos"),
            ("⊟", "Repositorios"),
        ]

        self._nav_btns: list = []
        grp = QButtonGroup(self)
        grp.setExclusive(True)

        for icon, label in NAV:
            btn = SidebarBtn(icon, label)
            grp.addButton(btn)
            sb.addWidget(btn)
            self._nav_btns.append(btn)

        sb.addStretch()

        ver = QLabel(f"Andrés Tapia  ·  2026")
        ver.setFont(QFont("Ubuntu", 7))
        ver.setStyleSheet(f"color:{C.BORDER};")
        ver.setAlignment(Qt.AlignCenter)
        sb.addWidget(ver)
        sb.addSpacing(10)

        body.addWidget(sidebar)

        # ── Pages ────────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background:{C.BG}; border:none;")

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{C.BG};")

        self._dash   = DashboardPage()
        self._clean  = CleanerPage()
        self._opt    = OptimizerPage()
        self._svc    = ServicesPage()
        self._start  = StartupPage()
        self._uninst = UninstallerPage()
        self._res    = ResourcesPage()
        self._repo   = ReposPage()

        for page in (self._dash, self._clean, self._opt, self._svc,
                     self._start, self._uninst, self._res, self._repo):
            self._stack.addWidget(page)

        scroll.setWidget(self._stack)
        body.addWidget(scroll, 1)

        main_layout.addLayout(body, 1)

        # ── Status bar ───────────────────────────────────────────────────────
        self._status = StatusBar()
        main_layout.addWidget(self._status)

        # Wire nav
        for i, btn in enumerate(self._nav_btns):
            btn.clicked.connect(lambda _, idx=i: self._switch(idx))

        self._nav_btns[0].setChecked(True)
        self._stack.setCurrentIndex(0)

        # System worker
        self._worker = SystemWorker()
        self._worker.updated.connect(self._on_data)
        self._worker.start()

    def _switch(self, idx: int):
        self._stack.setCurrentIndex(idx)

    def _on_data(self, d: dict):
        self._dash.update_data(d)
        self._res.update_data(d)
        self._status.update_data(d)

    def closeEvent(self, event):
        self._worker.stop()
        event.accept()


# ─────────────────────── ENTRY POINT ─────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Stacer 2026")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("Stacer")

    # Font fallback chain for better unicode/symbol support
    QFont.insertSubstitutions("Ubuntu", [
        "Noto Color Emoji", "Symbola", "DejaVu Sans", "Liberation Sans",
        "Noto Sans", "FreeSans",
    ])

    # Global palette
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor(C.BG))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(C.TEXT))
    pal.setColor(QPalette.ColorRole.Base,            QColor(C.CARD))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(C.CARD2))
    pal.setColor(QPalette.ColorRole.Button,          QColor(C.CARD2))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor(C.TEXT))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(C.ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(C.DIM))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
 
       

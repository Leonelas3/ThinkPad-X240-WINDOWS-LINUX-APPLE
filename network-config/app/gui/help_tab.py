from __future__ import annotations
import math
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QPainter, QFont, QLinearGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextBrowser, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsEllipseItem,
    QGraphicsItem, QLabel, QPushButton, QCheckBox, QGroupBox,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal

import core.config_manager as cfg


# ---------------------------------------------------------------------------
# Ayuda textual por dispositivo
# ---------------------------------------------------------------------------

def _ip(path: str, default: str) -> str:
    return cfg.get(path, default)


_DEVICE_HELP: list[tuple[str, str]] = [
    ("Asus RT-BE50", """
<h2>Asus RT-BE50 — Router principal WiFi 7</h2>
<p><b>IP:</b> 192.168.50.1 &nbsp;|&nbsp; <b>Admin:</b> <code>http://192.168.50.1</code>
&nbsp;(usuario: <i>admin</i>, contraseña: la que asignaste al configurar)</p>

<h3>Puertos físicos</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Velocidad</th><th>Uso en esta red</th></tr>
<tr><td>WAN</td><td>2.5 GbE</td><td>O2/Movistar → Movistar HGU (LAN)</td></tr>
<tr><td>LAN 1</td><td>1 GbE</td><td>HP Pro Mini 400 G9</td></tr>
<tr><td>LAN 2</td><td>1 GbE</td><td>Switch → ThinkPad X250 + otros</td></tr>
<tr><td>LAN 3</td><td>1 GbE</td><td><b>WAN2</b> → Vodafone CGA4233VDF (LAN)</td></tr>
<tr><td>USB 3.0</td><td>—</td><td>Sonoff Dongle Max (alimentación + opcional ser2net)</td></tr>
</table>

<h3>Activar SSH</h3>
<ol>
<li>Entra en <code>http://192.168.50.1</code></li>
<li><b>Administration → System</b></li>
<li><b>Enable SSH → Yes</b> · <b>SSH port: 22</b> · <b>Allow SSH access from: LAN only</b></li>
<li>Clic en <b>Apply</b></li>
<li>Conecta desde el HP Mini: <code>ssh admin@192.168.50.1</code></li>
</ol>

<h3>Activar JFFS (scripts personalizados)</h3>
<ol>
<li><b>Administration → System → Enable JFFS custom scripts → Yes</b></li>
<li>Reinicia el router</li>
<li>Los scripts van en <code>/jffs/scripts/</code> (deben tener <code>chmod +x</code>)</li>
</ol>

<h3>Dual WAN</h3>
<ol>
<li><b>WAN → Dual WAN → Enable Dual WAN → Yes</b></li>
<li>Primary: <code>WAN</code> | Secondary: <code>LAN3</code></li>
<li>Mode: <b>Load Balance</b> · Algorithm: <b>Round Robin</b></li>
<li>Network Monitoring: ping a <code>8.8.8.8</code> (WAN1) y <code>1.1.1.1</code> (WAN2)</li>
</ol>

<h3>Puertos predeterminados de servicio</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Servicio</th><th>Puerto</th><th>Dirección</th></tr>
<tr><td>Interfaz web HTTP</td><td>80</td><td>LAN → router</td></tr>
<tr><td>Interfaz web HTTPS</td><td>443</td><td>LAN → router</td></tr>
<tr><td>SSH</td><td>22</td><td>LAN → router</td></tr>
<tr><td>DNS</td><td>53</td><td>LAN → router</td></tr>
<tr><td>DHCP</td><td>67/68 UDP</td><td>LAN ↔ router</td></tr>
</table>
"""),

    ("Movistar HGU (O2)", """
<h2>Movistar HGU — ONT/Router de fibra O2</h2>
<p><b>IP LAN:</b> 192.168.1.1 &nbsp;|&nbsp; <b>Admin:</b> <code>http://192.168.1.1</code><br>
<b>Función en esta red:</b> solo ONT (convierte fibra a Ethernet).
El Asus RT-BE50 es el router real.</p>

<h3>Puertos físicos típicos HGU</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Uso</th></tr>
<tr><td>GPON / SC-APC</td><td>Cable de fibra óptica desde el distribuidor</td></tr>
<tr><td>LAN 1–4 (1 GbE)</td><td>LAN 1 → puerto WAN del Asus RT-BE50</td></tr>
<tr><td>USB</td><td>Almacenamiento o impresora compartida (opcional)</td></tr>
<tr><td>TEL 1–2</td><td>Telefonía fija (opcional)</td></tr>
</table>

<h3>Modo bridge / PPPoE</h3>
<p>Para evitar doble NAT, configura el HGU en <b>modo bridge</b>
(varía por versión de firmware). El Asus hace todo el enrutamiento.</p>
<ol>
<li>Entra en <code>http://192.168.1.1</code></li>
<li>Busca <b>Internet → Conexión → Tipo: Bridge</b> o <b>PPPoE pass-through</b></li>
<li>Si no aparece la opción, llama a O2 para que lo activen remotamente</li>
</ol>

<h3>SSH</h3>
<p>El HGU de Movistar <b>no expone SSH</b> de forma oficial.
No es necesario en este setup — toda la configuración avanzada se hace desde el Asus.</p>
"""),

    ("Vodafone CGA4233VDF", """
<h2>Vodafone CGA4233VDF — Router cable (DOCSIS)</h2>
<p><b>IP LAN:</b> 192.168.0.1 &nbsp;|&nbsp; <b>Admin:</b> <code>http://192.168.0.1</code><br>
<b>Usuario:</b> <code>vodafone</code> &nbsp;|&nbsp; <b>Contraseña:</b> ver etiqueta inferior del router<br>
<b>Función en esta red:</b> cable modem + puente hacia Asus LAN3 (WAN2)</p>

<h3>Puertos físicos</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Uso</th></tr>
<tr><td>CABLE (coaxial F)</td><td>Cable coaxial de Vodafone</td></tr>
<tr><td>LAN 1–4 (1 GbE)</td><td>LAN 1 → LAN3 del Asus (WAN2)</td></tr>
<tr><td>USB 3.0</td><td>Almacenamiento (no usado)</td></tr>
<tr><td>TEL</td><td>"No usar este puerto" (etiquetado en el propio router)</td></tr>
<tr><td>RESET</td><td>Mantén 10 s para restaurar fábrica</td></tr>
</table>

<h3>Evitar doble NAT</h3>
<p>Con el router conectado como WAN2 del Asus, el Vodafone actúa como router+NAT.
Para evitar doble NAT, configúralo en <b>modo IP Passthrough / Bridge</b>:</p>
<ol>
<li>Entra en <code>http://192.168.0.1</code> con usuario <code>vodafone</code></li>
<li>Busca <b>Advanced → IP Passthrough</b> o <b>Gateway → IP Passthrough</b></li>
<li>Actívalo con la MAC del puerto WAN del Asus como destino</li>
</ol>

<h3>SSH</h3>
<p>El CGA4233VDF <b>no expone SSH</b>. Solo tiene interfaz web.</p>
"""),

    ("ThinkPad X250 — Home Assistant", """
<h2>ThinkPad X250 — Home Assistant OS (HAOS)</h2>
<p><b>IP:</b> 192.168.50.10 &nbsp;|&nbsp; <b>HA Web:</b> <code>http://192.168.50.10:8123</code><br>
<b>Externo:</b> <code>https://leonelastres.duckdns.org</code> (puerto 443 → 8123)</p>

<h3>Puertos que usa HAOS</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Servicio</th></tr>
<tr><td>8123</td><td>Interfaz web de Home Assistant (HTTP/HTTPS)</td></tr>
<tr><td>1883</td><td>MQTT broker (si add-on Mosquitto instalado)</td></tr>
<tr><td>8883</td><td>MQTT over TLS</td></tr>
<tr><td>21064</td><td>HomeKit Bridge (si add-on instalado)</td></tr>
</table>

<h3>Activar SSH en HAOS</h3>
<ol>
<li>En HA: <b>Settings → Add-ons → Add-on Store</b></li>
<li>Instala <b>"Terminal &amp; SSH" (Advanced SSH &amp; Web Terminal)</b></li>
<li>En el add-on: <b>Configuration</b> → añade tu clave pública SSH o contraseña</li>
<li>Puerto por defecto: <b>22222</b> (para no conflictar con otros servicios)</li>
<li>Conecta: <code>ssh root@192.168.50.10 -p 22222</code></li>
</ol>

<h3>Token de larga duración (API)</h3>
<ol>
<li>Abre HA → clic en tu avatar (esquina inferior izquierda)</li>
<li>Baja hasta <b>Tokens de larga duración → Crear token</b></li>
<li>Dale un nombre (ej: "GestionRedDomestica") y copia el token</li>
<li>Pégalo en la app: pestaña ⚙️ Configuración → Home Assistant → Token</li>
</ol>

<h3>Zigbee (Sonoff Dongle Max por LAN)</h3>
<ol>
<li><b>Settings → Integrations → Zigbee Home Automation → Configurar</b></li>
<li>Serial device path: <code>socket://192.168.50.5:6638</code></li>
<li>Baudrate: <code>115200</code> · Guarda y reinicia la integración</li>
</ol>
"""),

    ("HP Pro Mini 400 G9", """
<h2>HP Pro Mini 400 G9 — Windows 11</h2>
<p><b>IP:</b> 192.168.50.20 &nbsp;|&nbsp; <b>OS:</b> Windows 11</p>

<h3>Puertos físicos</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Especificación</th></tr>
<tr><td>RJ45 (LAN)</td><td>1 GbE integrado (Intel I219-LM)</td></tr>
<tr><td>USB 3.2 Type-A ×2</td><td>Frontal</td></tr>
<tr><td>USB 3.2 Type-A ×2</td><td>Trasero</td></tr>
<tr><td>USB-C (Thunderbolt)</td><td>Trasero — datos + vídeo + carga</td></tr>
<tr><td>HDMI 2.1</td><td>Trasero</td></tr>
<tr><td>DisplayPort 1.4</td><td>Trasero</td></tr>
<tr><td>Flex IO (interno)</td><td>Slot propietario HP — 2.5GbE NIC opcional</td></tr>
</table>

<h3>Activar SSH (OpenSSH Server)</h3>
<ol>
<li><b>Inicio → Configuración → Sistema → Características opcionales</b></li>
<li>Clic en <b>Ver características</b> → busca <b>OpenSSH Server</b> → Instalar</li>
<li>Después en <b>Servicios</b> (services.msc): busca <b>OpenSSH SSH Server</b></li>
<li>Tipo de inicio: <b>Automático</b> → clic en <b>Iniciar</b></li>
<li>Conecta: <code>ssh usuario@192.168.50.20</code></li>
</ol>

<h3>Habilitar acceso a carpetas compartidas</h3>
<ol>
<li><b>Configuración → Red e Internet → Opciones de uso compartido</b></li>
<li>Activar <b>Detección de redes</b> y <b>Uso compartido de archivos e impresoras</b></li>
</ol>
"""),

    ("Sonoff Dongle Max", """
<h2>Sonoff Dongle Max — Coordinador Zigbee</h2>
<p><b>IP:</b> 192.168.50.5 &nbsp;|&nbsp; <b>Web:</b> <code>http://192.168.50.5</code><br>
<b>Puerto ZHA:</b> TCP 6638</p>

<h3>Conexión física</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Uso</th></tr>
<tr><td>RJ45</td><td>Cable LAN al switch o Movistar HGU — <b>datos</b></td></tr>
<tr><td>USB-C</td><td>Cargador 5V — <b>solo alimentación eléctrica</b>, NO datos</td></tr>
</table>

<h3>Asignar IP fija</h3>
<ol>
<li>Abre <code>http://IP_ACTUAL_DEL_SONOFF</code> (búscala en el DHCP del Asus)</li>
<li>En la web del Sonoff: <b>Network → IP Configuration → Static</b></li>
<li>Introduce <code>192.168.50.5</code> / máscara <code>255.255.255.0</code> / gateway <code>192.168.50.1</code></li>
<li>O resérvala en el Asus: <b>LAN → DHCP Server → Manually Assigned</b></li>
</ol>

<h3>Puertos de servicio</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse">
<tr><th>Puerto</th><th>Servicio</th></tr>
<tr><td>80</td><td>Interfaz web de configuración</td></tr>
<tr><td>6638</td><td>Coordinador Zigbee — usado por ZHA de Home Assistant</td></tr>
</table>

<h3>SSH</h3>
<p>El Sonoff Dongle Max <b>no tiene SSH</b>. Solo interfaz web en puerto 80.</p>
"""),
]


# ---------------------------------------------------------------------------
# Mapa de red interactivo
# ---------------------------------------------------------------------------

class _ConnectionLine(QGraphicsLineItem):
    def __init__(self, node_a: "_DeviceNode", node_b: "_DeviceNode", label: str = ""):
        super().__init__()
        self._a = node_a
        self._b = node_b
        self._label = label
        pen = QPen(QColor("#4a9eff"), 2, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setZValue(-1)

        self._text = QGraphicsTextItem(label)
        self._text.setDefaultTextColor(QColor("#cdd6f4"))
        self._text.setFont(QFont("Segoe UI", 8))
        self._text.setZValue(1)

        self.update_pos()

    def update_pos(self) -> None:
        a = self._a.sceneBoundingRect().center()
        b = self._b.sceneBoundingRect().center()
        self.setLine(QLineF(a, b))
        mid = QPointF((a.x() + b.x()) / 2 - 20, (a.y() + b.y()) / 2 - 10)
        self._text.setPos(mid)

    def add_to_scene(self, scene: QGraphicsScene) -> None:
        scene.addItem(self)
        scene.addItem(self._text)


class _DeviceNode(QGraphicsRectItem):
    """Nodo arrastrable que representa un dispositivo de red."""

    _W, _H = 130, 72

    def __init__(
        self,
        name: str,
        ip: str,
        color: str,
        ports: list[tuple[str, str]],   # (label, color_hex)
        x: float,
        y: float,
    ):
        super().__init__(0, 0, self._W, self._H)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        self._name = name
        self._ip = ip
        self._connections: list[_ConnectionLine] = []

        grad = QLinearGradient(0, 0, 0, self._H)
        grad.setColorAt(0, QColor(color).lighter(120))
        grad.setColorAt(1, QColor(color))
        self.setBrush(QBrush(grad))
        self.setPen(QPen(QColor(color).lighter(160), 1.5))

        # Nombre
        t_name = QGraphicsTextItem(name, self)
        t_name.setDefaultTextColor(QColor("#ffffff"))
        t_name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        t_name.setPos(6, 4)

        # IP
        t_ip = QGraphicsTextItem(ip, self)
        t_ip.setDefaultTextColor(QColor("#cdd6f4"))
        t_ip.setFont(QFont("Consolas", 8))
        t_ip.setPos(6, 22)

        # Puntos de puerto
        px = 6
        for p_label, p_color in ports[:6]:
            dot = QGraphicsEllipseItem(px, self._H - 18, 10, 10, self)
            dot.setBrush(QBrush(QColor(p_color)))
            dot.setPen(QPen(QColor(p_color).lighter(150), 0.5))
            dot.setToolTip(p_label)
            px += 16

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for conn in self._connections:
                conn.update_pos()
        return super().itemChange(change, value)

    def add_connection(self, conn: "_ConnectionLine") -> None:
        self._connections.append(conn)


def _make_connection(
    scene: QGraphicsScene,
    a: _DeviceNode,
    b: _DeviceNode,
    label: str = "",
) -> _ConnectionLine:
    conn = _ConnectionLine(a, b, label)
    a.add_connection(conn)
    b.add_connection(conn)
    conn.add_to_scene(scene)
    return conn


class _NetworkMap(QGraphicsView):
    def __init__(self):
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor("#1e1e2e")))

        self._build_topology()

    def _build_topology(self) -> None:
        s = self._scene

        # Colores base por tipo de dispositivo
        C_ROUTER   = "#2d5a8e"
        C_MODEM    = "#5a3a8e"
        C_SERVER   = "#1a6b3a"
        C_PC       = "#5a4a1a"
        C_IOT      = "#6b3a1a"

        # Puertos por color: azul=LAN, naranja=WAN, gris=USB, amarillo=coaxial, verde=fibra
        LAN  = ("LAN 1G",  "#4a9eff")
        LAN25= ("LAN 2.5G","#66b3ff")
        WAN  = ("WAN",     "#f38ba8")
        USB  = ("USB",     "#a6adc8")
        COAX = ("COAXIAL", "#f9e2af")
        FIBE = ("FIBRA",   "#a6e3a1")

        # Nodos
        internet = _DeviceNode("Internet", "WAN", "#3a3a5e",
                                [(">", "#4a9eff")], 300, 10)

        movistar = _DeviceNode("Movistar HGU", "192.168.1.1", C_MODEM,
                                [FIBE, LAN, LAN, LAN, LAN, USB], 60, 130)

        asus = _DeviceNode("Asus RT-BE50", "192.168.50.1", C_ROUTER,
                            [WAN, LAN, LAN, ("LAN3/WAN2","#f9a825"), USB], 300, 240)

        vodafone = _DeviceNode("Vodafone\nCGA4233VDF", "192.168.0.1", C_MODEM,
                               [COAX, LAN, LAN, LAN, LAN, USB], 60, 370)

        thinkpad = _DeviceNode("ThinkPad X250\n(HAOS)", "192.168.50.10", C_SERVER,
                               [LAN, USB, USB], 180, 400)

        sonoff = _DeviceNode("Sonoff\nDongle Max", "192.168.50.5", C_IOT,
                             [("RJ45", "#4a9eff"), ("USB-C⚡","#a6adc8")], 180, 510)

        hpmini = _DeviceNode("HP Mini 400 G9", "192.168.50.20", C_PC,
                             [LAN, USB, USB, ("USB-C","#a6adc8")], 420, 400)

        switch = _DeviceNode("Switch", "—", "#3a5a3a",
                             [LAN, LAN, LAN, LAN], 330, 340)

        for node in [internet, movistar, asus, vodafone, thinkpad, sonoff, hpmini, switch]:
            s.addItem(node)

        # Conexiones
        _make_connection(s, internet, movistar,  "fibra O2")
        _make_connection(s, internet, vodafone,  "cable Vodafone")
        _make_connection(s, movistar, asus,      "WAN → Asus")
        _make_connection(s, vodafone, asus,      "LAN→LAN3/WAN2")
        _make_connection(s, asus,     switch,    "LAN2 CAT6")
        _make_connection(s, asus,     hpmini,    "LAN1 CAT6")
        _make_connection(s, switch,   thinkpad,  "CAT6")
        _make_connection(s, thinkpad, sonoff,    "LAN socket:6638")

        # Leyenda
        legend_items = [
            ("#4a9eff", "Puerto LAN"),
            ("#f38ba8", "Puerto WAN"),
            ("#f9e2af", "Puerto coaxial"),
            ("#a6e3a1", "Puerto fibra"),
            ("#a6adc8", "Puerto USB"),
        ]
        lx, ly = 10, 530
        for color, text in legend_items:
            dot = QGraphicsEllipseItem(lx, ly, 10, 10)
            dot.setBrush(QBrush(QColor(color)))
            dot.setPen(QPen(Qt.PenStyle.NoPen))
            s.addItem(dot)
            t = QGraphicsTextItem(text)
            t.setDefaultTextColor(QColor("#cdd6f4"))
            t.setFont(QFont("Segoe UI", 8))
            t.setPos(lx + 14, ly - 2)
            s.addItem(t)
            ly += 18

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


# ---------------------------------------------------------------------------
# Pestaña principal de ayuda
# ---------------------------------------------------------------------------

class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter)

        # --- Panel izquierdo: lista de temas ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 4, 8)

        lbl = QLabel("Temas")
        lbl.setStyleSheet("font-weight: bold; color: #4a9eff; font-size: 13px;")
        left_layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setStyleSheet("QListWidget { background: #2a2a3e; border: none; } "
                                 "QListWidget::item { padding: 8px 6px; color: #cdd6f4; } "
                                 "QListWidget::item:selected { background: #3a3a5e; color: #4a9eff; }")

        for name, _ in _DEVICE_HELP:
            self._list.addItem(QListWidgetItem(name))
        self._list.addItem(QListWidgetItem("🗺  Mapa de red"))

        self._list.currentRowChanged.connect(self._switch_page)
        left_layout.addWidget(self._list)

        zoom_row = QHBoxLayout()
        btn_zoom_in  = QPushButton("+")
        btn_zoom_out = QPushButton("−")
        btn_zoom_in.setFixedWidth(30)
        btn_zoom_out.setFixedWidth(30)
        btn_zoom_in.setToolTip("Zoom in mapa")
        btn_zoom_out.setToolTip("Zoom out mapa")
        btn_zoom_in.clicked.connect(lambda: self._map.scale(1.2, 1.2))
        btn_zoom_out.clicked.connect(lambda: self._map.scale(1/1.2, 1/1.2))
        zoom_row.addWidget(btn_zoom_in)
        zoom_row.addWidget(btn_zoom_out)
        zoom_row.addWidget(QLabel("Zoom mapa"))
        zoom_row.addStretch()
        left_layout.addLayout(zoom_row)

        left.setMaximumWidth(200)
        splitter.addWidget(left)

        # --- Panel derecho: contenido ---
        self._stack = QStackedWidget()
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(1, 1)

        # Páginas de ayuda por dispositivo
        for _, html in _DEVICE_HELP:
            browser = QTextBrowser()
            browser.setOpenExternalLinks(True)
            browser.setHtml(f"""
            <html><head><style>
              body {{ background:#1e1e2e; color:#cdd6f4; font-family:'Segoe UI',sans-serif; font-size:13px; padding:12px; }}
              h2   {{ color:#4a9eff; border-bottom:1px solid #3a3a5e; padding-bottom:6px; }}
              h3   {{ color:#a6e3a1; margin-top:14px; }}
              code {{ background:#2a2a3e; padding:2px 5px; border-radius:3px; color:#f9e2af; }}
              table{{ border-color:#3a3a5e; width:100%; }}
              th   {{ background:#2a2a3e; color:#4a9eff; }}
              td,th{{ padding:5px 8px; }}
              ol,ul{{ line-height:1.9; }}
            </style></head><body>{html}</body></html>
            """)
            self._stack.addWidget(browser)

        # Página del mapa de red
        map_page = QWidget()
        map_layout = QVBoxLayout(map_page)
        map_layout.setContentsMargins(4, 4, 4, 4)
        map_layout.addWidget(QLabel(
            "  Arrastra los dispositivos para reorganizar · Rueda del ratón para zoom"
        ))
        self._map = _NetworkMap()
        map_layout.addWidget(self._map)
        self._stack.addWidget(map_page)

        # Seleccionar el primer ítem por defecto
        self._list.setCurrentRow(0)

    def _switch_page(self, row: int) -> None:
        self._stack.setCurrentIndex(row)

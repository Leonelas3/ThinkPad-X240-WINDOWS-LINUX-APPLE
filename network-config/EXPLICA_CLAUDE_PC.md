# Contexto del proyecto — para Claude Code local

Este archivo resume todo lo que se diseñó y construyó en la sesión de Claude Code en la nube.
Léelo antes de modificar cualquier cosa del proyecto.

---

## ¿Qué es este proyecto?

App de escritorio PyQt6 + scripts de router para gestionar una **red doméstica en Zamora, España**
con doble ISP, router Asus RT-BE50 WiFi 7, Home Assistant OS y automatización Zigbee.

Repo: `https://github.com/Leonelas3/homeassistant-x250-asus-rt-be50-dual-isp`

---

## Hardware real del usuario

| Dispositivo | Modelo | IP fija | Notas |
|---|---|---|---|
| Router principal | Asus RT-BE50 (WiFi 7) | 192.168.50.1 | Dual WAN nativo |
| ISP 1 | O2 fibra simétrica 1 Gbps | WAN1 del Asus | Para uploads SIEMPRE |
| ISP 2 | Vodafone cable 600/50 Mbps | WAN2 del Asus | Pendiente instalación |
| Servidor domótica | ThinkPad X250 con HAOS | 192.168.50.10 | Home Assistant OS nativo |
| PC de trabajo | HP Pro Mini 400 G9 (Win 11) | 192.168.50.20 | A diario, WiFi |
| Coordinador Zigbee | Sonoff Dongle Max | 192.168.50.5 | Conectado por LAN RJ45, puerto TCP 6638 |
| Switch | Barato sin gestión | — | Une dispositivos en sala |

**Nota importante sobre el Sonoff Dongle Max:**
- Tiene su propio puerto RJ45 (datos) y USB-C (solo alimentación — NO conectado al PC)
- Se usa por LAN, no por USB
- ZHA en HA se configura como: `socket://192.168.50.5:6638`

**Nota sobre Vodafone:**
- El router Vodafone puede usarse como switch o para acceder a su panel en 192.168.0.1
- Vodafone NUNCA se usa para uploads (asimétrico, solo 50 Mbps subida)
- Al llegar Vodafone: activar Dual WAN en Asus → Load Balance, WAN2 = Vodafone

---

## Lógica de routing (scripts jffs/)

**Objetivo:** uploads siempre por O2, descargas multi-hilo balanceadas entre ambos ISP.

**`jffs/nat-start`** se sube al router vía SSH y se ejecuta al arrancar:
- `UPLOAD_PORTS = "21,22,990,2283,8123"` → forzados a WAN1 (O2)
- ThinkPad X250 (192.168.50.10) forzado a WAN1 tanto como origen como destino
- Puerto 443 NO está en UPLOAD_PORTS a propósito (para no romper balanceo de descargas HTTPS)
- CONNMARK para persistencia de sesión tras reconexión

**`jffs/wan-event`** re-ejecuta nat-start con `sleep 3` en eventos WAN.

---

## Home Assistant

- **HAOS versión 17.3, HA Core 2026.5.4** en ThinkPad X250
- Acceso externo: `https://leonelastres.duckdns.org` (DuckDNS apunta a WAN1 del Asus)
- Acceso interno: `http://192.168.50.10:8123`
- Acceso cloud (siempre disponible): Nabu Casa activo en el ThinkPad
- Port forwarding en Asus: `443 → 192.168.50.10:8123` y `8123 → 192.168.50.10:8123`
- SSH add-on instalado: puerto 22222, usuario `hassio`
- Interface de red: `enp0s25` (LAN física), en DHCP — reservar MAC → 192.168.50.10 en Asus

**DuckDNS debe apuntar siempre a WAN1 (O2), nunca a WAN2 (Vodafone).**

---

## App PyQt6 — estructura de `app/`

```
app/
├── main.py                  # Punto de entrada — autoinstala deps con pip, notifica fallos
├── requirements.txt         # PyQt6, PyQt6-WebEngine, requests, paramiko
├── config.example.json      # Plantilla de config (copiada a config.json en primer arranque)
│
├── core/
│   ├── config_manager.py    # Lee/escribe config.json (credenciales nunca en git)
│   ├── db.py                # SQLite — log de cambios con rollback
│   ├── scanner.py           # Escaneo de red paralelo (ping + puertos)
│   ├── notifications.py     # Sistema pub/sub de notificaciones (Level: INFO/WARNING/ERROR)
│   └── devices/
│       ├── asus_rt_be50.py      # Login cookie, WAN IPs, subir nat-start por SSH (paramiko)
│       ├── homeassistant_api.py # REST API con Bearer token
│       └── sonoff_zigbee.py     # Check TCP 6638 + HTTP 80
│
└── gui/
    ├── main_window.py       # QMainWindow — toolbar con 🔔 campanita, 5 pestañas
    ├── styles.py            # DARK_STYLESHEET (tema Catppuccin Mocha)
    ├── devices_tab.py       # Tabla de dispositivos detectados, botón escanear
    ├── config_tab.py        # Paneles: Asus / HA / Sonoff / HP Mini con botones de acción
    ├── log_tab.py           # Historial SQLite con botón de deshacer cambios
    ├── browser_tab.py       # QWebEngineView — carga panel web de cada dispositivo
    ├── help_tab.py          # Guías de dispositivos + mapa de red interactivo arrastrable
    ├── setup_wizard.py      # QWizard de primer arranque — pide IPs, usuarios, tokens
    └── notification_bell.py # 🔔 widget toolbar — badge rojo con popup desplegable
```

### Cómo ejecutar la app

```bash
cd app/
python main.py
```

`main.py` instala automáticamente las dependencias con pip antes de arrancar.
Si una instalación falla, aparece como notificación ERROR en la campanita con botón "Reintentar".

### Config segura

`config.json` está en `.gitignore` — nunca se sube a GitHub.
En el primer arranque el wizard pregunta: IP del Asus, usuario/contraseña del Asus,
token de HA, IP del Sonoff, dominio/token de DuckDNS.

---

## Estado actual del proyecto (28 mayo 2026)

- [x] Scripts de router (nat-start, wan-event) completos
- [x] Guía de setup del router (ROUTER-SETUP-GUIDE.md) con todos los pasos
- [x] Guía Zigbee LAN (zigbee-lan/ZIGBEE-LAN-SETUP.md)
- [x] App PyQt6 completa con todas las pestañas
- [x] Sistema de notificaciones con campanita
- [x] Wizard de primer arranque
- [x] Log SQLite con rollback
- [x] Mapa de red interactivo arrastrable
- [ ] Vodafone pendiente de instalación (traslado de domicilio, hasta 15 días)
- [ ] Cuando llegue Vodafone: activar Dual WAN en Asus + probar nat-start

---

## Decisiones técnicas importantes

**¿Por qué no bonding real?**
El bonding verdadero (nivel de paquetes) requiere un servidor externo (VPS) como nodo de agregación.
Sin eso, solo hay load balancing por sesiones — que es lo que hace el Asus nativamente.
Para los casos de uso reales del usuario (Immich multi-upload, cloud sync) el load balance es suficiente.

**¿Por qué el Sonoff va por LAN y no por USB?**
El Sonoff Dongle Max tiene su propio puerto RJ45 Ethernet. Conectarlo por LAN libera el USB
del ThinkPad X250 para una cámara o micrófono. El USB-C del Sonoff es solo alimentación.

**¿Por qué DuckDNS solo en WAN1?**
Google Home y los certificados SSL están atados al dominio `leonelastres.duckdns.org`.
Si DuckDNS apuntara a WAN2 (Vodafone) y esa conexión cae, se pierde acceso externo.
O2 es simétrica (más estable para servicios entrantes).

**¿Por qué el puerto 443 no está en UPLOAD_PORTS?**
Si 443 estuviera en la lista, TODAS las conexiones HTTPS (que son la mayoría de las descargas)
se forzarían a WAN1, rompiendo el balanceo. La regla del ThinkPad X250 ya cubre el caso
de Home Assistant recibiendo en 443 desde el exterior.

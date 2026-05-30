# Log de ejecución del proyecto

Registro cronológico de decisiones, problemas y soluciones durante la instalación de la red doméstica.

---

## Sesión 1 — Diseño inicial del proyecto

### Decisiones de arquitectura
- **Router principal**: Asus RT-BE50 (WiFi 7, Dual WAN nativo)
- **ISP 1**: O2 fibra simétrica 1 Gbps → WAN1 del Asus (uploads siempre por aquí)
- **ISP 2**: Vodafone cable 600/50 Mbps → WAN2 del Asus (pendiente instalación ~15 días)
- **Domótica**: ThinkPad X250 con HAOS nativo en 192.168.50.10
- **Zigbee**: Sonoff Dongle Max por LAN RJ45 (no USB) en 192.168.50.5:6638
- **Subred LAN**: 192.168.50.0/24

### Scripts creados
- `jffs/nat-start`: iptables CONNMARK para forzar uploads a WAN1. UPLOAD_PORTS = 21,22,990,2283,8123. Puerto 443 excluido a propósito para no romper balanceo de descargas HTTPS.
- `jffs/wan-event`: re-ejecuta nat-start con sleep 3 en eventos WAN

### App PyQt6 creada
- 5 pestañas: Dispositivos, Configuración, Historial, Interfaz Web, Ayuda
- Sistema de notificaciones con campanita (🔔) en toolbar
- Wizard de primer arranque para credenciales
- Log SQLite con rollback
- Mapa de red interactivo arrastrable
- Autoinstalación de dependencias pip con notificación de fallos

---

## Sesión 2 — Instalación física (Asus RT-BE50 recibido)

### Estado: Vodafone no disponible aún
- El traslado de domicilio de Vodafone puede tardar hasta 15 días
- Se procede con solo O2 (Mitrastar) de momento
- **Dual WAN desactivado temporalmente** en Asus hasta que llegue Vodafone

### Configuración de Home Assistant antes de cambiar cables
- HA tenía SSL activo solo accesible por `https://leonelastres.duckdns.org:8123`
- Se desactivó SSL en configuration.yaml (comentar ssl_certificate y ssl_key en http:)
- Se activó **Nabu Casa** (trial) para mantener acceso remoto durante el cambio de cables
- Se configuró red en DHCP en HA (interfaz enp0s25)
- Se instaló add-on **Advanced SSH & Web Terminal** (puerto 22222, usuario hassio)

### Información del sistema HA (del terminal SSH)
- HAOS versión: 17.3
- HA Core: 2026.5.4
- Interfaz LAN: enp0s25 → IP actual 192.168.1.81 (en red Movistar)
- URL local confirmada: http://homeassistant.local:8123

---

## Sesión 3 — Diagnóstico: Asus sin internet

### Problema encontrado en syslog
Análisis del syslog del router Asus reveló:

1. **Causa principal**: Dual WAN Load Balance activo con WAN2 vacía (Vodafone no conectado)
   - `WAN(1) Connection: WAN(1) link down` en bucle
   - `firewall: apply rules error(7967)` al fallar la configuración de load balance
   - `wanduck` intentando recuperar WAN2 constantemente, interrumpiendo WAN1
   - `dhcp client: deconfig` + `WAN was exceptionally disconnected` en ciclo

2. **Secundario**: DHCP lease inicial de solo 300 segundos del Mitrastar (normal en primer arranque, sube a 43200s después)

3. **Errores benignos** (no afectan conectividad): mlo_config.ini, regulatory.db, QCA5332.ini — normales en RT-BE50 con WiFi 7

**Solución**: Desactivar Dual WAN en Asus hasta que llegue Vodafone

---

## Sesión 4 — Intento de configurar PPPoE directo en Asus

### Descubrimiento del hardware
- El ONT está **integrado** en el Mitrastar GPT-2742GX4X5v6 (fibra entra por la izquierda, 4 puertos LAN)
- No es posible sacar la fibra del Mitrastar y conectarla directamente al Asus
- Para PPPoE directo en Asus habría que poner el Mitrastar en modo bridge

### Intento de modo bridge en Mitrastar
- Se activó modo bridge en el Mitrastar
- **Resultado**: Sin internet — el firmware propietario de Movistar requiere configuración adicional no documentada
- **Decisión**: Revertir a configuración funcional (Mitrastar hace PPPoE, Asus recibe DHCP)

### Configuración actual que funciona
```
Fibra → Mitrastar GPT-2742GX4X5v6 (PPPoE con O2, da DHCP)
           ↓ LAN
        Asus RT-BE50 WAN → IP: 192.168.1.102 (fija por MAC)
           ↓
        Red LAN 192.168.50.0/24
```
Doble NAT pero funcional.

### Credenciales PPPoE
- Las credenciales del Mitrastar (O2) son válidas para PPPoE directo en Asus si en el futuro se logra el bridge
- O2 usa la misma infraestructura que Movistar → mismas credenciales que extrae el HGU
- VLAN requerida para Movistar/O2 en España: **VLAN ID 6**

---

## Sesión 5 — Port forwarding con doble NAT

### Problema: Mitrastar con firmware capado
- NAT → General: solo checkboxes de habilitar NAT (sin port forwarding)
- NAT → Asignación de direcciones: One-to-One NAT (solo útil con IP pública estática)
- NAT → Port Triggering: dinámico, no sirve para HA
- **Conclusión**: Firmware de Movistar tiene capado el port forwarding en interfaz avanzada

### Limitación adicional descubierta
- La interfaz simple del Mitrastar ("Puertos") solo permite **una regla por IP destino**
- Impide abrir tanto el 443 como el 8123 hacia la misma IP del Asus
- Esta limitación fue la razón original de comprar el Asus RT-BE50

### Plan de port forwarding acordado

**Ahora mismo (un solo router disponible):**
| Router | Puerto | Destino |
|---|---|---|
| Mitrastar | 443 TCP | 192.168.1.102 (Asus WAN) |
| Asus | 443 | 192.168.50.10:8123 (HA) |

**Cuando llegue Vodafone (dos routers, un puerto cada uno):**
| Router | Puerto | Destino |
|---|---|---|
| Mitrastar → Asus WAN1 | 443 TCP | 192.168.50.10:8123 — para DuckDNS/HTTPS |
| Vodafone → Asus WAN2 | 8123 TCP | 192.168.50.10:8123 — para app nativa HA |

### Configuración HA para que el app funcione con 443
En HA → Configuración → Sistema → Red:
```
URL externa: https://leonelastres.duckdns.org
URL interna: http://192.168.50.10:8123
```

### Nabu Casa
- Activo en trial temporal para mantener acceso remoto durante la instalación
- **No se va a mantener** — alternativa: DuckDNS + puerto 443
- Desactivar cuando port forwarding esté funcional

### WiFi del Mitrastar
- Pendiente de desactivar para reducir carga del HGU
- Ruta: Configuración de red → WiFi → desactivar cada banda

---

## Estado actual (30 mayo 2026)

### Funciona ✅
- Internet por O2 vía Mitrastar → Asus (DHCP, doble NAT)
- Red LAN 192.168.50.x activa
- Home Assistant accesible localmente: http://homeassistant.local:8123
- SSH a HA: `ssh hassio@192.168.50.10 -p 22222`
- Nabu Casa (temporal): acceso remoto activo

### Pendiente ⏳
- [ ] Desactivar WiFi en el Mitrastar
- [ ] Añadir regla puerto 443 en Mitrastar → 192.168.1.102
- [ ] Configurar URL externa en HA: https://leonelastres.duckdns.org
- [ ] Instalar Vodafone (traslado domicilio, ~15 días)
- [ ] Al llegar Vodafone: activar Dual WAN en Asus, añadir puerto 8123 en Asus WAN2
- [ ] Subir nat-start al Asus por SSH cuando Dual WAN esté activo
- [ ] Conectar Sonoff Dongle Max por LAN → reservar 192.168.50.5 en DHCP Asus
- [ ] Configurar ZHA en HA: socket://192.168.50.5:6638
- [ ] Desactivar Nabu Casa cuando port forwarding esté funcional

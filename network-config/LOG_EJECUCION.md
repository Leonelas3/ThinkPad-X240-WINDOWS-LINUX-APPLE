# Log de ejecución del proyecto

Registro cronológico de decisiones, problemas y soluciones durante la instalación de la red doméstica.

---

## Sesión 1 — Diseño inicial del proyecto

### Decisiones de arquitectura
- **Router principal**: Asus RT-BE50 (WiFi 7, Dual WAN nativo)
- **ISP 1**: O2 fibra simétrica 600 Mbps → WAN1 del Asus (uploads siempre por aquí)
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
        Asus RT-BE50 WAN → IP: 192.168.1.102 (fija por MAC, DHCP)
           ↓
        Red LAN 192.168.50.0/24
```
Doble NAT pero funcional.

### Credenciales PPPoE
- Las credenciales del Mitrastar (O2) son válidas para PPPoE directo en Asus si en el futuro se logra el bridge
- O2 usa la misma infraestructura que Movistar → mismas credenciales que extrae el HGU
- VLAN requerida para Movistar/O2 en España: **VLAN ID 6**
- En la pantalla GPON del Mitrastar se confirma: VID/Prioridad 6/1, PPPoE ✅

### IP pública O2
- IP pública actual: **83.58.202.207** (dinámica, sin servicio de IP fija en O2)
- O2 no ofrece IP fija en su catálogo (Movistar la ofrece a 30€/mes pero es otra marca)
- Solución: DuckDNS actualiza automáticamente cuando cambia la IP

---

## Sesión 5 — Port forwarding con doble NAT

### Problema: Mitrastar con firmware capado
- NAT → General: solo checkboxes de habilitar NAT (sin port forwarding)
- NAT → Asignación de direcciones: One-to-One NAT (solo útil con IP pública estática)
- NAT → Port Triggering: dinámico, no sirve para HA
- **Conclusión**: Firmware de Movistar tiene capado el port forwarding en interfaz avanzada

### Solución encontrada: cambiar NAT a "Función completa"
- La interfaz GPON del Mitrastar tenía NAT en modo **Solo SUA** (básico, una regla por IP)
- Cambiando a **Función completa** se desbloquea el port forwarding completo
- También se deshabilitó el **acceso remoto MGMT** del Mitrastar (que bloqueaba el puerto 443)

### Reglas configuradas en el Mitrastar (interfaz simple → Puertos)
| Nombre | Proto | Puerto externo | Puerto interno | IP destino | Estado |
|---|---|---|---|---|---|
| Google home 443 | TCP | 443 | 8123 | 192.168.1.102 | ON |
| ha | TCP+UDP | 8123 | 8123 | 192.168.1.102 | ON |
| immich | TCP | 2283 | 2283 | 192.168.1.102 | ON |

### Reglas a configurar en el Asus (segundo salto)
| Nombre | Puerto externo | IP destino | Puerto interno |
|---|---|---|---|
| HA HTTPS | 443 | 192.168.50.10 | 8123 |
| HA directa | 8123 | 192.168.50.10 | 8123 |
| Immich | 2283 | 192.168.50.20 | 2283 |

### Plan con dos ISP (cuando llegue Vodafone)
| Router | Puerto | Destino | Uso |
|---|---|---|---|
| Mitrastar → Asus WAN1 | 443 | 192.168.50.10:8123 | DuckDNS/HTTPS |
| Vodafone → Asus WAN2 | 8123 | 192.168.50.10:8123 | App nativa HA |

---

## Sesión 6 — Diagnóstico y corrección de red Asus

### Problemas encontrados y resueltos
1. **WAN con IP estática y máscara 255.255.255.255** → sin internet
   - Causa: se configuró como estática con máscara incorrecta
   - Solución: cambiar máscara a 255.255.255.0 y luego WAN a DHCP ✅

2. **Dual WAN en modo Load Balance** con WAN2 vacía → cortes periódicos
   - Pendiente de desactivar completamente

3. **DNS DHCP añadidos**: 1.1.1.1 (Cloudflare) y 9.9.9.9 (Quad9) ✅

### Resultado speedtest (fast.com desde móvil por WiFi Asus)
- **Descarga: 760 Mbps** (contratado: 600 Mbps — un 27% por encima)
- **Subida: 480 Mbps**
- **Latencia descarga: 13 ms**
- Doble NAT no penaliza la velocidad ✅
- IP pública confirmada: 83.58.202.207, Zamora ES, Telefonica-Movistar

### Reservas DHCP configuradas en Asus
| Hostname | MAC | IP fija |
|---|---|---|
| HA-LAN | 50:7B:9D:77:51:A5 | 192.168.50.10 |
| miniPC | 30:24:32:B3:E0:C5 | 192.168.50.20 |

### Red IoT (_iot)
- El Asus crea automáticamente una red `_iot` separada por seguridad
- Dispositivos en red principal (necesitan HA local): deshumidificador, enchufes WiFi, dispositivos Tuya/ESPHome
- Dispositivos en red _iot (solo nube): Google TV, Alexa
- Zigbee (Sonoff LAN): no afectado por WiFi, usa cable

---

## Sesión 7 — Port forwarding Asus + Dual WAN desactivado

### Dual WAN desactivado
- **Panel Asus → WAN → Dual WAN → OFF** ✅
- Causa raíz de los cortes periódicos y Disney+ freezing eliminada
- Con Dual WAN desactivado, todo el tráfico va por WAN1 (O2) sin interrupciones

### Port forwarding configurado en el Asus (segundo salto del doble NAT)
**Panel Asus → WAN → Virtual Server / Port Forwarding**

| Nombre | Puerto externo | IP local destino | Puerto interno | Protocolo |
|---|---|---|---|---|
| HA-HTTPS | 443 | 192.168.50.10 | 8123 | TCP |
| HA-directo | 8123 | 192.168.50.10 | 8123 | TCP+UDP |
| Immich | 2283 | 192.168.50.20 | 2283 | TCP |

### Cadena completa de port forwarding operativa
```
Internet → IP pública 83.58.202.207
  → Mitrastar (443→192.168.1.102:443, 8123→:8123, 2283→:2283)
    → Asus WAN 192.168.1.102 (443→192.168.50.10:8123, 8123→:8123, 2283→192.168.50.20:2283)
      → HA en ThinkPad X250 :8123
      → Immich en HP Mini :2283
```

---

## Estado actual (31 mayo 2026)

### ✅ Completado
- Internet funcionando: 760 Mbps descarga vía Mitrastar → Asus (doble NAT)
- Red LAN 192.168.50.x activa
- DNS: 1.1.1.1 / 9.9.9.9 configurados en DHCP del Asus
- IPs fijas por MAC: ThinkPad X250 (50.10), HP Mini (50.20)
- WiFi Mitrastar desactivada (libera recursos del HGU)
- SSID Asus renombrado igual que la red Movistar anterior (reconexión automática de dispositivos)
- Port forwarding en Mitrastar: 443→8123, 8123→8123, 2283→2283 todos a 192.168.1.102
- NAT Mitrastar: cambiado a "Función completa"
- MGMT remoto Mitrastar: deshabilitado (liberó puerto 443)
- **Dual WAN desactivado en Asus** (elimina cortes y freezing Disney+)
- **Port forwarding en Asus**: 443→50.10:8123, 8123→50.10:8123, 2283→50.20:2283
- Home Assistant accesible localmente: http://homeassistant.local:8123
- SSH a HA: `ssh hassio@192.168.50.10 -p 22222`
- Cadena doble NAT completa: internet → Mitrastar → Asus → HA / Immich

### ⏳ Pendiente
- [ ] Actualizar DuckDNS con IP pública: 83.58.202.207
- [ ] Activar add-on DuckDNS en HA para actualización automática de IP
- [ ] Configurar URL externa en HA (Settings → System → Network): `https://leonelastres.duckdns.org`
- [ ] Reactivar SSL en HA (configuration.yaml): ssl_certificate + ssl_key bajo http:
- [ ] Probar acceso externo completo: https://leonelastres.duckdns.org → HA
- [ ] Desactivar Nabu Casa cuando acceso externo esté confirmado
- [ ] Instalar Vodafone (traslado domicilio, ~15 días)
- [ ] Al llegar Vodafone: activar Dual WAN en Asus (Load Balance), WAN2 = Vodafone
- [ ] Al llegar Vodafone: añadir port forwarding 8123 en router Vodafone → Asus WAN2
- [ ] Subir nat-start al Asus por SSH cuando Dual WAN esté activo
- [ ] Conectar Sonoff Dongle Max por LAN → reservar 192.168.50.5 en DHCP Asus
- [ ] Configurar ZHA en HA: socket://192.168.50.5:6638

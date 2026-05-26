# Guía de configuración — Asus RT-BE50 Dual WAN + Home Assistant

**Red:** 192.168.50.0/24  
**WAN1:** O2/Movistar fibra 1 Gbps simétrico (puerto WAN 2.5G)  
**WAN2:** Vodafone cable 600/50 Mbps (puerto LAN3 como WAN2)  
**HA Server:** ThinkPad X250 → 192.168.50.10  
**HP Mini:** HP Pro Mini 400 G9 → 192.168.50.20  

---

## Sección 1 — Configuración Dual WAN

1. Accede a la interfaz web del router: `http://192.168.50.1`
2. Ve a **WAN → Dual WAN**.
3. Activa **Enable Dual WAN**.
4. Configura:
   - **Primary WAN:** WAN (puerto físico WAN 2.5G) → O2/Movistar
   - **Secondary WAN:** LAN3 (el puerto LAN3 configurado como segunda WAN) → Vodafone
5. **Dual WAN Mode:** `Load Balance`
6. **Load Balance Algorithm:** `Round Robin`
   - Round Robin distribuye conexiones alternando entre ambas WANs, lo que aprovecha mejor el ancho de banda agregado en descargas multi-hilo.
7. Activa **Network Monitoring** para detectar caídas automáticamente. Usa `8.8.8.8` (WAN1) y `1.1.1.1` (WAN2) como destinos de ping.
8. Guarda con **Apply**.

> **Nota:** En algunos firmwares AsusWRT el algoritmo aparece como "By Traffic" o "Round-Robin". Elige Round Robin o el equivalente más cercano.

---

## Sección 2 — IPs estáticas (DHCP Reservations)

Ve a **LAN → DHCP Server → Manually Assigned IP around the DHCP list**.

Antes de crear las reservas, obtén las MACs de cada dispositivo:
- **ThinkPad X250 (HAOS):** en la consola de HAOS ejecuta `ip link show` o mírala en `Settings → System → Network`.
- **HP Mini (Windows 11):** `ipconfig /all` en cmd, busca "Physical Address" de la NIC activa.

| Nombre        | MAC Address       | IP asignada    |
|---------------|-------------------|----------------|
| ThinkPad-X250-HA | _rellenar_     | 192.168.50.10  |
| HP-Mini-400G9    | _rellenar_     | 192.168.50.20  |

Añade cada entrada y pulsa **Add** → **Apply**.

---

## Sección 3 — Port Forwarding para Home Assistant

Ve a **WAN → Virtual Server / Port Forwarding**.

Añade las siguientes reglas:

| Nombre de servicio | Protocolo | Puerto externo | IP interna   | Puerto interno |
|--------------------|-----------|----------------|--------------|----------------|
| HA_HTTPS           | TCP       | 443            | 192.168.50.10 | 8123          |
| HA_8123            | TCP       | 8123           | 192.168.50.10 | 8123          |

- **HA_HTTPS** permite que `https://leonelastres.duckdns.org` (sin puerto) funcione — el tráfico HTTPS del puerto estándar 443 llega al puerto 8123 de HA.
- **HA_8123** mantiene compatibilidad con apps nativas de HA y usuarios que usan `:8123` explícitamente.

Pulsa **Add** por cada regla → **Apply**.

---

## Sección 4 — Habilitar JFFS y SSH

JFFS es la partición flash del router donde viven los scripts personalizados. Sin ella, los scripts no persisten entre reinicios.

1. Ve a **Administration → System**.
2. **Enable JFFS custom scripts and configs:** `Yes`.
3. **Format JFFS partition at next boot:** solo actívalo si es la primera vez (formateará la partición). En usos posteriores déjalo en `No`.
4. **Enable SSH:** `Yes` — **Access from:** `LAN only` (nunca expongas SSH a WAN).
5. Pulsa **Apply** y reinicia el router.

Tras el reinicio, verifica que JFFS está montado:
```sh
ssh admin@192.168.50.1 "ls /jffs"
```
Deberías ver el directorio `scripts/` (puede estar vacío inicialmente).

---

## Sección 5 — Instalar los scripts de routing

Desde un equipo en la LAN (Linux/Mac/WSL en Windows):

```sh
# Copia los scripts al router
scp network-config/jffs/nat-start  admin@192.168.50.1:/jffs/scripts/nat-start
scp network-config/jffs/wan-event  admin@192.168.50.1:/jffs/scripts/wan-event

# Hazlos ejecutables
ssh admin@192.168.50.1 "chmod +x /jffs/scripts/nat-start /jffs/scripts/wan-event"

# Ejecuta nat-start manualmente para aplicar las reglas sin reiniciar
ssh admin@192.168.50.1 "/jffs/scripts/nat-start"
```

**Verificar que las reglas están activas:**
```sh
ssh admin@192.168.50.1 "iptables -t mangle -L PREROUTING -n -v"
```
Debes ver líneas con `MARK set 0x1` asociadas a la IP `192.168.50.10` y a los puertos 22, 21, 990, 2283.

**Verificar que el tráfico del HA server sale por WAN1:**
```sh
# Desde el ThinkPad X250 (HAOS), abre una consola y ejecuta:
curl -s https://ifconfig.me
# Debe devolver la IP pública de O2, no la de Vodafone.
# Compara con la IP que ves en el estado de WAN2 del router.
```

**Ver el log del script:**
```sh
ssh admin@192.168.50.1 "logread | grep nat-start"
```

---

## Sección 6 — Configurar DDNS / DuckDNS

DuckDNS debe apuntar a la IP pública de **WAN1 (O2)**, no a la de Vodafone, porque el port forwarding para HA está en WAN1.

**Opción A — DDNS integrado en AsusWRT:**

1. Ve a **WAN → DDNS**.
2. **Server:** `WWW.DUCKDNS.ORG`.
3. **Host Name:** `leonelastres`.
4. **Username/Key:** tu token de DuckDNS (obtenlo en [duckdns.org](https://www.duckdns.org) → tu dominio → "token").
5. Verifica que **WAN IP used for DDNS** está configurado para usar **WAN1**. Si el campo no existe en tu firmware, AsusWRT suele usar la IP de WAN primaria por defecto.
6. **Apply**.

**Verificar que DuckDNS apunta a WAN1:**
```sh
# Consulta la IP que tiene registrada DuckDNS
curl -s "https://www.duckdns.org/update?domains=leonelastres&token=TU_TOKEN&verbose=true"

# Compara con la IP de WAN1 que muestra el router en WAN → Internet Status
```
Ambas IPs deben coincidir.

**Opción B — Script propio en JFFS (si el cliente integrado no funciona bien con dual WAN):**

Crea `/jffs/scripts/duckdns.sh`:
```sh
#!/bin/sh
# Obtiene la IP de WAN1 explícitamente y la actualiza en DuckDNS
TOKEN="TU_TOKEN_AQUI"
DOMAIN="leonelastres"
# nvram get wan0_ipaddr devuelve la IP de WAN1 en AsusWRT
WAN1_IP=$(nvram get wan0_ipaddr)
curl -sk "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${WAN1_IP}"
logger -t duckdns "IP actualizada: $WAN1_IP"
```

Añade una entrada cron en `/jffs/scripts/services-start`:
```sh
cru a duckdns "*/5 * * * * /jffs/scripts/duckdns.sh"
```

---

## Sección 7 — Configurar Home Assistant

**Requisito previo:** el add-on **File Editor** (o Studio Code Server) instalado en HAOS.

1. Abre Home Assistant → **Settings → Add-ons → File Editor → Open Web UI**.
2. Navega a `/config/configuration.yaml`.
3. Añade el contenido de `network-config/homeassistant/configuration_additions.yaml` al archivo.
   - Si ya tienes bloques `homeassistant:` o `http:` existentes, fusiona las claves en lugar de duplicar los bloques.
4. Guarda el archivo.
5. Ve a **Developer Tools → YAML → Check Configuration** para validar antes de reiniciar.
6. Reinicia HA: **Settings → System → Restart**.

**Verificar acceso externo:**

| URL | Debe funcionar para |
|-----|---------------------|
| `https://leonelastres.duckdns.org` | Google Home, integraciones que usan HTTPS estándar |
| `https://leonelastres.duckdns.org:8123` | App móvil de Home Assistant, acceso manual |

Prueba ambas desde fuera de tu red (datos móviles del teléfono, con WiFi desactivado).

**Verificar integración Google Home:**

En Google Home → añadir dispositivo → Works with Google → busca "Home Assistant". Si ya estaba vinculado, puede que necesites desvincular y vincular de nuevo para que tome la nueva `external_url`.

---

## Sección 8 — Limitaciones conocidas

### Por qué las subidas del HP Mini pueden salir por Vodafone

TCP es bidireccional: una conexión TCP única (un socket) usa **el mismo camino para subir y bajar**. El router asigna WAN1 o WAN2 al primer paquete SYN y toda la sesión sigue ese camino.

En load balance Round Robin, si el router asigna la sesión a WAN2 (Vodafone), **tanto la subida como la bajada de esa sesión van por Vodafone**. No es posible —sin hardware adicional— dividir el upload del download de un mismo socket entre dos WANs.

**Lo que sí consiguen los scripts:**
- El ThinkPad X250 (HA server) va **siempre** por WAN1, sin excepción.
- Conexiones iniciadas hacia puertos de subida conocidos (SSH/22, FTP/21, FTPS/990, Immich/2283) van por WAN1 para cualquier dispositivo de la LAN.

**Lo que no se puede conseguir sin hardware adicional:**
- Garantizar que las subidas del HP Mini vayan por WAN1 cuando la descarga de esa misma sesión está en WAN2. Para lograrlo necesitarías una segunda NIC en el HP Mini y enrutar el tráfico de subida por una ruta estática diferente a nivel de sistema operativo.

### Solución futura si añades una segunda NIC al HP Mini

Con una segunda NIC en el HP Mini conectada a un puerto LAN diferente (que puedas poner en una VLAN o subred separada), podrías:
1. Configurar esa segunda NIC como interfaz de "solo subida".
2. En aplicaciones como rclone, usar `--bind <IP_segunda_NIC>` para forzar las subidas por esa interfaz.
3. En el router, rutear esa segunda subred siempre por WAN1.

Hasta entonces, la limitación es inherente al diseño dual-WAN con un solo punto de entrada por dispositivo.

---

## Referencia rápida de IPs y puertos

| Recurso | Valor |
|---------|-------|
| Router (admin web) | http://192.168.50.1 |
| HA interno | http://192.168.50.10:8123 |
| HA externo (sin puerto) | https://leonelastres.duckdns.org |
| HA externo (con puerto) | https://leonelastres.duckdns.org:8123 |
| WAN1 nvram key | `wan0_ipaddr` |
| WAN2 nvram key | `wan1_ipaddr` |
| Marca iptables WAN1 | `0x01/0x0f` |
| Marca iptables WAN2 | `0x02/0x0f` |

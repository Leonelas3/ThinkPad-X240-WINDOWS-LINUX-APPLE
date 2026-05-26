# Sonoff Dongle Max — ZigBee por LAN via Asus RT-BE50

El Sonoff Dongle Max se conecta al **puerto USB del Asus RT-BE50** (que está en la sala
junto al ThinkPad X250). El router expone el dongle como puerto serie TCP mediante
`ser2net`, y Home Assistant ZHA se conecta a él por red local.

**Sin hardware adicional. Sin coste extra.**

```
[Sala]
Sonoff Dongle Max
       │ USB
Asus RT-BE50 ── ser2net escucha en TCP 20108
       │ LAN (192.168.50.0/24)
ThinkPad X250 — Home Assistant OS
       └── ZHA → socket://192.168.50.1:20108
```

---

## Paso 1 — Instalar Entware en el Asus RT-BE50

Entware es el gestor de paquetes para routers ASUS. Requiere JFFS habilitado
(ya configurado en la guía principal).

Conéctate al router por SSH (usuario: `admin`, contraseña: la del router):

```sh
ssh admin@192.168.50.1
```

Instala Entware:

```sh
entware-setup.sh
```

> Si el comando no existe, el router aún no tiene Entware. Ejecútalo así:
> ```sh
> curl -sL https://bin.entware.net/armv7sf-k3.10/installer/generic.sh | sh
> ```
> (AsusWRT usa arquitectura ARM — usar el paquete armv7sf)

---

## Paso 2 — Instalar ser2net y el driver CP2102N

```sh
# Actualizar lista de paquetes
opkg update

# Instalar ser2net
opkg install ser2net

# Verificar que el driver CP210x está cargado (Sonoff usa chip CP2102N)
modprobe cp210x 2>/dev/null || true
ls /dev/ttyUSB*   # debe mostrar /dev/ttyUSB0 con el dongle conectado
```

Si `/dev/ttyUSB0` no aparece, el kernel del router puede no incluir el módulo cp210x.
En ese caso la alternativa es un Raspberry Pi Zero W (~€12) con ser2net como puente.

---

## Paso 3 — Copiar la configuración de ser2net

Desde el PC (en la carpeta `network-config/zigbee-lan/`):

```sh
scp ser2net.yaml admin@192.168.50.1:/opt/etc/ser2net.yaml
```

O pégalo manualmente en el router con `vi /opt/etc/ser2net.yaml`.

---

## Paso 4 — Arrancar ser2net y habilitarlo al inicio

```sh
# Arrancar ahora
ser2net -c /opt/etc/ser2net.yaml -n &

# Verificar que escucha en el puerto
netstat -tlnp | grep 20108

# Habilitar arranque automático via JFFS (se añade al script wan-event existente)
echo 'ser2net -c /opt/etc/ser2net.yaml -n 2>/dev/null &' >> /jffs/scripts/services-start
chmod +x /jffs/scripts/services-start
```

---

## Paso 5 — Reconfigurar ZHA en Home Assistant

1. **Settings → Integrations → Zigbee Home Automation → Configure**
2. Cambia el **Serial device path**:
   - De: `/dev/ttyUSB0` (USB directo al ThinkPad)
   - A: `socket://192.168.50.1:20108`
3. **Baudrate:** 115200
4. Guarda — ZHA se reconecta sin perder los dispositivos emparejados.

> Haz un backup de HAOS antes de cambiar el transporte:
> **Settings → System → Backups → Create backup**

---

## Verificación

```sh
# Desde el ThinkPad X250 (terminal en HAOS o SSH)
nc -z 192.168.50.1 20108 && echo "ser2net accesible" || echo "no responde"
```

---

## Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `/dev/ttyUSB0` no aparece | Driver CP210x no cargado | `modprobe cp210x` — si falla, el kernel no incluye el módulo |
| `netstat` no muestra el puerto 20108 | ser2net no arrancó | Revisar logs: `ser2net -c /opt/etc/ser2net.yaml` (sin `-n`) |
| ZHA conecta pero sin dispositivos | Red ZigBee reconstruyéndose | Esperar 60 s; los dispositivos se reintegran solos |
| Dongle aparece como `ttyUSB1` | Otro USB conectado al router | Cambiar `ttyUSB0` por `ttyUSB1` en `ser2net.yaml` |

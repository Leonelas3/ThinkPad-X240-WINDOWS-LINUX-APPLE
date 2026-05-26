# Sonoff Dongle Max — Cambio de USB a LAN

El Sonoff Dongle Max tiene puerto RJ45 propio. No necesita ningún dispositivo
intermediario — se conecta directamente a la red y Home Assistant ZHA accede
a él por su IP.

```
[Sala]
Sonoff Dongle Max
  ├── USB-C → cargador de móvil / fuente USB (SOLO alimentación, NO datos)
  └── RJ45  → switch o Movistar HGU (LAN)
                    │
             ThinkPad X250 (HA)
             ZHA → socket://SONOFF_IP:6638
```

---

## Pasos

### 1. Conectar el Sonoff a la red

- **RJ45** → cualquier puerto LAN libre del switch o del Movistar HGU
- **USB-C** → **cargador de móvil o fuente de alimentación USB** (5 V, solo
  alimentación eléctrica — **no conectar al ThinkPad X250 ni a ningún PC**).
  El USB-C del Sonoff Dongle Max no transmite datos; su único rol es suministrar
  corriente al dispositivo. Conectarlo a un ordenador no aportaría nada y podría
  causar confusión con el modo USB-serie que usaba antes.
- El cable USB que antes iba al ThinkPad X250 ya no es necesario en absoluto
  (ni para datos ni para alimentación, salvo que uses el puerto USB del router
  como fuente de corriente en lugar de un cargador independiente).

### 2. Encontrar la IP del Sonoff

En el Asus RT-BE50, ve a **Network Map → Clients** o **LAN → DHCP Leases**
y busca el dispositivo con nombre "Sonoff" o similar.

También puedes acceder a la interfaz web del Sonoff directamente:
`http://SONOFF_IP` — desde ahí confirmas la IP y puedes fijar una IP estática.

> Recomendado: reservar IP estática en el Asus para el Sonoff (igual que para
> el ThinkPad y el HP Mini) para que la dirección nunca cambie.
> **LAN → DHCP Server → Manually Assigned IP** → añade la MAC del Sonoff → `192.168.50.5`

### 3. Verificar el puerto de red del Sonoff

El Sonoff Dongle Max en modo LAN expone el coordinador Zigbee en **TCP 6638**
(puerto estándar de su firmware). Puedes confirmarlo en su interfaz web.

### 4. Cambiar la conexión en Home Assistant ZHA

> Haz un backup antes: **Settings → System → Backups → Create backup**

1. **Settings → Integrations → Zigbee Home Automation → Configure**
2. Cambia el **Serial device path**:
   - De: `/dev/ttyUSB0`
   - A: `socket://192.168.50.5:6638`
3. Guarda — ZHA se reconecta y los dispositivos emparejados se mantienen.

---

## Verificación rápida

Desde el terminal de HAOS (o SSH al ThinkPad):

```sh
nc -z 192.168.50.5 6638 && echo "Sonoff accesible" || echo "no responde"
```

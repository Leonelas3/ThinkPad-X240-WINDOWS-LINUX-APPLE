# Sonoff Dongle Max — ZigBee por LAN

Mueve el coordinador ZigBee del USB del ThinkPad X250 al HP Mini 400 G9,
exponiéndolo como puerto serie TCP para que Home Assistant lo use por red.

**Flujo final:**
```
Sonoff Dongle Max (USB)
        │
HP Mini 400 G9 — Windows 11
  └── WSL2 Ubuntu + usbipd-win + ser2net → TCP 20108
        │ LAN (192.168.50.0/24)
ThinkPad X250 — Home Assistant OS
  └── ZHA → socket://192.168.50.20:20108
```

---

## Requisitos previos

| Requisito | Estado |
|---|---|
| HP Mini con Windows 11 actualizado | ✓ |
| Virtualización habilitada en BIOS del HP Mini | Verificar |
| Puerto TCP 20108 libre en red local | No requiere apertura en router (solo LAN) |

---

## Instalación (una sola vez)

### En el HP Mini — PowerShell como Administrador

```powershell
# Desde la carpeta network-config/zigbee-lan/
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-hp-mini.ps1
```

El script hace todo automáticamente:
1. Instala **usbipd-win** (comparte USB por red interna)
2. Instala **WSL2** con Ubuntu 22.04 (si no está)
3. Instala **ser2net** en WSL2
4. Copia la configuración `ser2net.yaml`
5. Te pide el BUSID del dongle y lo vincula
6. Crea la tarea de inicio automático `ZigbeeUSBLAN`

> Si Windows pide reinicio en algún paso, reinicia y vuelve a ejecutar el script.

---

## Reconfigurar ZHA en Home Assistant

1. **Settings → Integrations → Zigbee Home Automation → Configure**
2. Cambia el **Serial device path** de:
   ```
   /dev/ttyUSB0   ← valor actual (USB directo)
   ```
   a:
   ```
   socket://192.168.50.20:20108
   ```
3. **Baudrate:** 115200
4. **Flow control:** Software (o None)
5. Guarda y reinicia la integración ZHA (no hace falta reiniciar HA completo)

> Los dispositivos ZigBee ya emparejados se mantienen — ZHA guarda la base de datos
> de dispositivos por separado. Solo cambia el transporte físico.

---

## Verificación

### Desde el HP Mini (WSL2)

```bash
# Comprobar que el dongle está en WSL2
ls /dev/ttyUSB*          # debe mostrar /dev/ttyUSB0

# Comprobar que ser2net escucha
ss -tlnp | grep 20108    # debe mostrar 0.0.0.0:20108

# Test manual de conectividad
nc -z 192.168.50.20 20108 && echo "OK" || echo "NO RESPONDE"
```

### Desde el ThinkPad X250 (HAOS — Terminal add-on)

```bash
# Verificar conectividad al ser2net del HP Mini
nc -z 192.168.50.20 20108 && echo "Puerto accesible" || echo "No alcanzable"
```

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `/dev/ttyUSB*` no aparece en WSL2 | usbipd no adjuntó el USB | Ejecutar manualmente: `usbipd attach --wsl --busid X-X` |
| ser2net no escucha en el puerto | Falló el arranque | En WSL2: `sudo ser2net -c /etc/ser2net.yaml -n` |
| ZHA no conecta por socket | IP o puerto incorrecto | Verificar IP del HP Mini con `ipconfig` en Windows |
| ZHA conecta pero sin dispositivos | Dongle reiniciado, red ZigBee reestablecida | Esperar ~60 s; los dispositivos se reintegran solos |
| Dongle aparece como `ttyUSB1` | Otro dispositivo USB serie presente | Editar `/etc/ser2net.yaml` en WSL2: cambiar `ttyUSB0` por `ttyUSB1` |

---

## Notas importantes

- **El puerto TCP 20108 es solo LAN** — no hace falta abrir este puerto en el router
  ni crear reglas de port forwarding. ZHA se conecta desde la misma red local.
- **No quitar el dongle del HP Mini sin detener ZHA** — puede corromper el estado
  del coordinador ZigBee. Secuencia segura: pausar ZHA → quitar dongle → reemplazar.
- **Backup de ZigBee antes de migrar:** en HAOS, descarga el backup del coordinador
  desde Settings → System → Backups antes de cambiar el transporte.

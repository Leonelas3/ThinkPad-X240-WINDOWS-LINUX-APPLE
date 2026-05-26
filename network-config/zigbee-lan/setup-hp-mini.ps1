# setup-hp-mini.ps1
# Ejecutar como Administrador en el HP Pro Mini 400 G9 (Windows 11)
# Instala y configura usbipd-win + WSL2 + ser2net para el Sonoff Dongle Max

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"
$DONGLE_NAME     = "CP210x"            # nombre parcial del dispositivo en usbipd
$WSL_DISTRO      = "Ubuntu-22.04"
$SER2NET_PORT    = 20108
$SER2NET_CONFIG  = "/etc/ser2net.yaml"

Write-Host "=== Paso 1: Instalar usbipd-win ===" -ForegroundColor Cyan
winget install --id dorssel.usbipd-win --exact --silent --accept-package-agreements
Write-Host "usbipd-win instalado. Puede requerir reinicio antes de continuar." -ForegroundColor Yellow

Write-Host "`n=== Paso 2: Instalar WSL2 con Ubuntu 22.04 ===" -ForegroundColor Cyan
$wslInstalled = wsl --list --quiet 2>$null | Where-Object { $_ -match "Ubuntu" }
if (-not $wslInstalled) {
    wsl --install -d $WSL_DISTRO
    Write-Host "WSL2 instalado. Reinicia el equipo y vuelve a ejecutar este script para continuar." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "WSL2 con Ubuntu ya está presente." -ForegroundColor Green
}

Write-Host "`n=== Paso 3: Instalar ser2net dentro de WSL2 ===" -ForegroundColor Cyan
wsl -d $WSL_DISTRO -- bash -c "sudo apt-get update -qq && sudo apt-get install -y ser2net"

Write-Host "`n=== Paso 4: Copiar configuracion ser2net al WSL2 ===" -ForegroundColor Cyan
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configSrc = Join-Path $scriptDir "ser2net.yaml"
if (Test-Path $configSrc) {
    $wslPath = wsl -d $WSL_DISTRO -- wslpath -a "$configSrc"
    wsl -d $WSL_DISTRO -- bash -c "sudo cp '$wslPath' $SER2NET_CONFIG"
    Write-Host "Configuracion copiada a $SER2NET_CONFIG" -ForegroundColor Green
} else {
    Write-Host "No se encontro ser2net.yaml junto a este script. Copialo manualmente a $SER2NET_CONFIG en WSL2." -ForegroundColor Red
}

Write-Host "`n=== Paso 5: Identificar el Sonoff Dongle en usbipd ===" -ForegroundColor Cyan
Write-Host "Lista de dispositivos USB compartibles:" -ForegroundColor White
usbipd list
Write-Host "`nBusca la linea con '$DONGLE_NAME' o 'Sonoff' y anota su BUSID (ej: 1-3)." -ForegroundColor Yellow
$busId = Read-Host "Introduce el BUSID del Sonoff Dongle Max"

Write-Host "`n=== Paso 6: Vincular el dongle para que usbipd pueda compartirlo ===" -ForegroundColor Cyan
usbipd bind --busid $busId
Write-Host "Dongle vinculado con BUSID $busId" -ForegroundColor Green

Write-Host "`n=== Paso 7: Crear tarea de inicio automatico en el Programador de tareas ===" -ForegroundColor Cyan
# Genera el XML de la tarea con el BUSID real
$taskXml = Get-Content (Join-Path $scriptDir "startup-task.xml") -Raw
$taskXml = $taskXml -replace "BUSID_PLACEHOLDER", $busId
$taskXml = $taskXml -replace "DISTRO_PLACEHOLDER", $WSL_DISTRO
$taskXml = $taskXml -replace "PORT_PLACEHOLDER", $SER2NET_PORT

$tempXml = Join-Path $env:TEMP "zigbee-startup-task.xml"
$taskXml | Out-File -FilePath $tempXml -Encoding Unicode
schtasks /Create /TN "ZigbeeUSBLAN" /XML $tempXml /F
Remove-Item $tempXml
Write-Host "Tarea 'ZigbeeUSBLAN' creada en el Programador de tareas." -ForegroundColor Green

Write-Host "`n=== Configuracion completada ===" -ForegroundColor Green
Write-Host "El dongle se compartira automaticamente al iniciar Windows." -ForegroundColor White
Write-Host "Home Assistant ZHA: cambia el puerto serie a socket://192.168.50.20:$SER2NET_PORT" -ForegroundColor Cyan

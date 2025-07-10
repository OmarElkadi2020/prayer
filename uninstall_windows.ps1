# PowerShell script for Prayer Player Uninstallation on Windows
# Requires PowerShell 5.1 or later

# Exit on error
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# --- Function to check for Admin privileges ---
function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# --- Relaunch as Admin if necessary ---
if (-not (Test-Admin)) {
    Write-Warning "Administrative privileges are required to remove the Windows Service."
    Write-Host "Attempting to restart script with elevated privileges..."
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Definition)`""
    exit
}

Write-Host "Running with administrative privileges."
Write-Host "Prayer Player Uninstallation for Windows"

# --- 1. Stop and remove the Windows Service ---
$envDir = "myenv"
$venvPython = Join-Path $PSScriptRoot $envDir "Scripts\python.exe"
$serviceScript = Join-Path $PSScriptRoot "src\prayer\windows_service.py"

if (Test-Path $venvPython -and (Test-Path $serviceScript)) {
    Write-Host "Attempting to stop and remove the PrayerPlayer service..."
    
    # Check if the service exists before trying to stop it
    $service = Get-Service -Name "PrayerPlayer" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "Stopping service..."
        & "$venvPython" "$serviceScript" stop
    }

    # Remove the service
    Write-Host "Removing service..."
    & "$venvPython" "$serviceScript" remove

    Write-Host "Service removed successfully."
} else {
    Write-Warning "Could not find Python executable or service script. Skipping service removal."
    Write-Warning "You may need to remove the 'PrayerPlayer' service manually (using 'sc delete PrayerPlayer' in an admin command prompt)."
}

# --- 2. Remove project files ---
Write-Host "`nThe following items will be removed:"
Write-Host " - Virtual environment (myenv\)"
Write-Host " - Configuration files (src\prayer\config\config.json)"
Write-Host " - Google Calendar token (src\prayer\auth\token.json)"

$confirm = Read-Host "Are you sure you want to permanently delete these files? (y/N)"
if ($confirm -ne 'y') {
    Write-Host "Uninstallation cancelled."
    exit 0
}

Write-Host "Removing virtual environment..."
if (Test-Path $envDir) {
    Remove-Item -Recurse -Force -Path $envDir
}

Write-Host "Removing configuration files..."
$configFile = Join-Path $PSScriptRoot "src\prayer\config\config.json"
if (Test-Path $configFile) {
    Remove-Item -Force $configFile
}

$tokenFile = Join-Path $PSScriptRoot "src\prayer\auth\token.json"
if (Test-Path $tokenFile) {
    Remove-Item -Force $tokenFile
}

Write-Host "Uninstallation complete."
Write-Host "The project directory '$PSScriptRoot' has not been removed. You can delete it manually if you wish."

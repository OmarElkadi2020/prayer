# PowerShell script for Prayer Player Uninstallation on Windows
# Requires PowerShell 5.1 or later

# Exit on error
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host "`nPrayer Player Uninstallation for Windows`n"

# --- 1. Stop and remove the Scheduled Task ---
$taskName = "PrayerPlayerScheduler"

Write-Host "Attempting to unregister scheduled task '$taskName'..."
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    Write-Host "Scheduled task '$taskName' removed successfully."
} catch {
    Write-Warning "Could not remove scheduled task '$taskName'. It might not exist or you lack permissions. Error: $($_.Exception.Message)"
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

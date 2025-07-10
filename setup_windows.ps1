# PowerShell script for Prayer Player Setup on Windows
# Requires PowerShell 5.1 or later

# Exit on error
$ErrorActionPreference = "Stop"

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host "`nPrayer Player Setup for Windows`n"

# --- Function to check for Admin privileges ---
function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# --- 1. Check for Python and pip ---
Write-Host "Checking for Python and pip..."
$pythonPath = (Get-Command python3 -ErrorAction SilentlyContinue).Path
if (-not $pythonPath) {
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
}

if (-not $pythonPath) {
    Write-Error "Python 3 is not installed or not found in PATH. Please install Python 3 to proceed."
    exit 1
}

$pipPath = (Get-Command pip3 -ErrorAction SilentlyContinue).Path
if (-not $pipPath) {
    $pipPath = (Get-Command pip -ErrorAction SilentlyContinue).Path
}

if (-not $pipPath) {
    Write-Error "pip is not installed or not found in PATH. Please install pip to proceed."
    exit 1
}

Write-Host "Python found at: $pythonPath"
Write-Host "pip found at: $pipPath"

# --- 2. Create and activate virtual environment ---
$envDir = "myenv"
if (-not (Test-Path $envDir)) {
    Write-Host "Creating virtual environment..."
    & "$pythonPath" -m venv "$envDir"
}

# Activate virtual environment (for current session)
# Note: This activation is for the script's context. For subsequent manual runs, user needs to activate.
$activateScript = Join-Path $envDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . "$activateScript"
    Write-Host "Virtual environment activated."
} else {
    Write-Warning "Could not find virtual environment activation script. Proceeding without activation."
}

# --- 3. Install project dependencies ---
Write-Host "Installing project dependencies..."
& "$pipPath" install --upgrade pip
& "$pipPath" install -e .

# --- 4. Get user configuration ---
$city = Read-Host "Enter your city (e.g., Deggendorf)"
$country = Read-Host "Enter your country (e.g., Germany)"

# --- 5. Choose run mode ---
Write-Host "`nHow would you like to run Prayer Player?"
Write-Host "1) Run in background (as a Windows Service - recommended)"
Write-Host "2) Run in foreground (for testing or temporary use)"
$runChoice = Read-Host "Enter your choice (1 or 2)"

if ($runChoice -eq "1") {
    Write-Host "Setting up Prayer Player as a Windows Service..."

    if (-not (Test-Admin)) {
        Write-Warning "Administrative privileges are required to install a Windows Service."
        Write-Host "Attempting to restart script with elevated privileges..."
        Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\setup_windows.ps1`" -RunAsService -City `"$city`" -Country `"$country`""
        exit
    }

    # If script is restarted with admin privileges, these parameters will be passed
    param(
        [switch]$RunAsService,
        [string]$City,
        [string]$Country
    )

    if ($RunAsService) {
        Write-Host "Running with administrative privileges. Installing service..."
        # Use the full path to the python executable within the virtual environment
        $venvPython = Join-Path $PSScriptRoot $envDir "Scripts\python.exe"
        $serviceScript = Join-Path $PSScriptRoot "src\prayer\windows_service.py"

        # Install the service
        Write-Host "Installing PrayerPlayer service..."
        & "$venvPython" "$serviceScript" install

        # Start the service
        Write-Host "Starting PrayerPlayer service..."
        & "$venvPython" "$serviceScript" start

        Write-Host "Service setup complete. Prayer Player is now running in the background."
        Write-Host "To manage the service, open 'Services' (services.msc) or use:"
        Write-Host "  `"$venvPython`" `"$serviceScript`" stop/start/restart/remove"
    } else {
        Write-Error "Failed to elevate privileges. Service cannot be installed."
        exit 1
    }

} elseif ($runChoice -eq "2") {
    Write-Host "Running Prayer Player in the foreground..."
    Write-Host "Press Ctrl+C to stop the application."
    # Use the full path to the prayer-player executable within the virtual environment
    $playerExecutable = Join-Path $PSScriptRoot $envDir "Scripts\prayer-player.exe"
    if (-not (Test-Path $playerExecutable)) {
        # Fallback if .exe is not created by pip install -e .
        $playerExecutable = Join-Path $PSScriptRoot $envDir "Scripts\prayer-player"
    }
    
    & "$playerExecutable" --city "$city" --country "$country"

} else {
    Write-Error "Invalid choice. Please run the script again and choose 1 or 2."
    exit 1
}

Write-Host "Setup script finished."

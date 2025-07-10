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

# --- 1.5. Check for Tkinter (for GUI) and FFmpeg (for audio) ---
Write-Host "Checking for Tkinter..."
try {
    & "$pythonPath" -c "import tkinter" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tkinter module not found. This is required for the setup GUI."
        Write-Error "Please ensure you have a full Python 3 installation that includes Tkinter."
        Write-Error "Consider reinstalling Python from python.org, ensuring Tkinter is selected during installation."
        exit 1
    }
    Write-Host "Tkinter found."
} catch {
    Write-Error "An error occurred while checking for Tkinter: $($_.Exception.Message)"
    exit 1
}

Write-Host "Checking for ffmpeg (for audio playback)..."
$ffplayPath = (Get-Command ffplay.exe -ErrorAction SilentlyContinue).Path
if (-not $ffplayPath) {
    Write-Warning "ffplay (from ffmpeg) is not found in your system's PATH."
    Write-Warning "Please install ffmpeg to enable audio playback. You can install it via Chocolatey (recommended) or manually:"
    Write-Warning "  1. Install Chocolatey: Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    Write-Warning "  2. Then install ffmpeg: choco install ffmpeg"
    Write-Warning "  Alternatively, download ffmpeg binaries from ffmpeg.org and add them to your system PATH."
    # Do not exit, allow script to continue, but audio playback will not work without ffplay
} else {
    Write-Host "ffmpeg (ffplay) found at: $ffplayPath"
}

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

# --- 4. User Configuration via GUI ---
Write-Host "`nLaunching the Prayer Player Setup GUI for configuration...`n"
Write-Host "Please enter your City and Country in the GUI and click 'Save Configuration'."
Write-Host "Also, click 'Authenticate Google Calendar' in the GUI to set up calendar integration."
Write-Host "After saving and authenticating, close the GUI to continue with the setup.`n"

# Launch the GUI and wait for it to close
& "$pythonPath" "$PSScriptRoot\setup_gui.py"

Write-Host "Configuration GUI closed. Continuing with service setup...`n"

# --- 5. Apply run mode based on GUI configuration ---

# If script is restarted with admin privileges, these parameters will be passed
param(
    [switch]$RunAsService
)

$configFilePath = Join-Path $PSScriptRoot "src\prayer\config\config.json"
$runMode = "background" # Default value

if (Test-Path $configFilePath) {
    try {
        $configContent = Get-Content -Raw -Path $configFilePath | ConvertFrom-Json
        $runMode = $configContent.run_mode
    } catch {
        Write-Warning "Could not read config.json. Defaulting to background service. Error: $($_.Exception.Message)"
    }
}

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
} elseif ($runMode -eq "background") {
    Write-Host "Setting up Prayer Player as a Windows Service..."

    if (-not (Test-Admin)) {
        Write-Warning "Administrative privileges are required to install a Windows Service."
        Write-Host "Attempting to restart script with elevated privileges..."
        Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\setup_windows.ps1`" -RunAsService"
        exit
    } else {
        # This branch should ideally not be hit if -RunAsService works correctly
        Write-Error "Unexpected state: Admin but not -RunAsService. Exiting."
        exit 1
    }
} elseif ($runMode -eq "foreground") {
    Write-Host "Running Prayer Player in the foreground..."
    Write-Host "Press Ctrl+C to stop the application."
    # Use the full path to the prayer-player executable within the virtual environment
    $playerExecutable = Join-Path $PSScriptRoot $envDir "Scripts\prayer-player.exe"
    if (-not (Test-Path $playerExecutable)) {
        # Fallback if .exe is not created by pip install -e .
        $playerExecutable = Join-Path $PSScriptRoot $envDir "Scripts\prayer-player"
    }
    
    & "$playerExecutable"

} else {
    Write-Error "Invalid run mode specified in config.json. Defaulting to foreground run."
    Write-Host "Running Prayer Player in the foreground..."
    Write-Host "Press Ctrl+C to stop the application."
    # Use the full path to the prayer-player executable within the virtual environment
    $playerExecutable = Join-Path $PSScriptRoot $envDir "Scripts\prayer-player.exe"
    if (-not (Test-Path $playerExecutable)) {
        # Fallback if .exe is not created by pip install -e .
        $playerExecutable = Join-Path $PSScriptRoot $envDir "Scripts\prayer-player"
    }
    
    & "$playerExecutable"
}

Write-Host "Setup script finished."

# Set the execution policy for this session without changing the machine policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# Navigate to the script's directory and activate the virtual environment
Push-Location -Path $PSScriptRoot
.\venv\Scripts\Activate.ps1

# Change the window title
$Host.UI.RawUI.WindowTitle = "Autopilot - Development Environment"

# Install the required Python packages
pip install -r requirements.txt

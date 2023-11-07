# setup.ps1
# PowerShell script to set up the Autopilot project on a Windows machine

# Check for Administrator rights
If (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as an Administrator!"
    Exit
}

# Clone the repo (if necessary)
git clone https://github.com/name/autopilot.git

# Navigate to the project directory
Set-Location -Path "autopilot"

# ... do stuff ...

Write-Host "Autopilot setup complete!"
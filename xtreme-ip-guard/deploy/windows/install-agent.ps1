# Ionomegax Mersal Guard — Windows agent setup
$InstallDir = "C:\Program Files\Ionomegax\MersalGuard"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Recurse -Force "$PSScriptRoot\..\..\*" $InstallDir
$TaskAction = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$InstallDir\agent.py`" daemon --config `"$InstallDir\config\agent.json`""
$TaskTrigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "MersalGuardAgent" -Action $TaskAction -Trigger $TaskTrigger -RunLevel Highest -Force
Write-Host "Mersal Guard agent scheduled. Start server separately or point config to your Command Center URL."

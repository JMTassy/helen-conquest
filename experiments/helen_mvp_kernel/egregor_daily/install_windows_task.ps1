# Register EGREGOR DAILY in the Windows Task Scheduler (current user, runs only when you are logged on,
# because the Claude and Codex CLIs use your logged-in subscriptions).
#   powershell -ExecutionPolicy Bypass -File install_windows_task.ps1 -Time 07:30
#   powershell -ExecutionPolicy Bypass -File install_windows_task.ps1 -Remove
param(
  [string]$Time = "07:30",
  [string]$Python = "python",
  [string]$Config = "$PSScriptRoot\egregor.config.yaml",
  [switch]$Remove
)
$Name = "HELEN EGREGOR DAILY"
if ($Remove) { Unregister-ScheduledTask -TaskName $Name -Confirm:$false; Write-Host "Removed '$Name'."; exit 0 }
if (-not (Test-Path $Config)) { Write-Error "Config not found: $Config (copy egregor.config.example.yaml first)"; exit 1 }

$LogDir = Join-Path $env:USERPROFILE "HELEN_EGREGOR\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Script = Join-Path $PSScriptRoot "egregor_daily.py"
$Cmd = "/c `"$Python`" `"$Script`" --config `"$Config`" >> `"$LogDir\egregor.log`" 2>&1"

$Action   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $Cmd -WorkingDirectory $PSScriptRoot
$Trigger  = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $Name -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
Write-Host "Registered '$Name' daily at $Time (missed runs start when the PC is next on). Log: $LogDir\egregor.log"
Write-Host "Test it now: Start-ScheduledTask -TaskName '$Name'"

# 在這台 Windows 上登記兩個工作排程，實際執行的是 ops/*.sh。
# 備份 05:00，同步 06:00。電腦要開著、使用者要登入、Docker Desktop 要在跑。
# 手動：powershell -NoProfile -ExecutionPolicy Bypass -File ops\register_schedules.ps1

$ErrorActionPreference = "Stop"

$Bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
if (-not (Test-Path $Bash)) {
    throw "找不到 Git Bash：$Bash"
}

$Root = Split-Path -Parent $PSScriptRoot
$sync = Join-Path $PSScriptRoot "daily_sync.sh"
$backup = Join-Path $PSScriptRoot "backup_db.sh"

function Register-FootballTask([string]$Name, [string]$Script, [string]$At) {
    $action = New-ScheduledTaskAction -Execute $Bash -Argument "`"$Script`"" -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -Daily -At $At
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 12)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Output "registered $Name daily at $At -> $Script"
}

Register-FootballTask -Name "FootballPredictionDbBackup" -Script $backup -At "05:00"
Register-FootballTask -Name "FootballPredictionDailySync" -Script $sync -At "06:00"

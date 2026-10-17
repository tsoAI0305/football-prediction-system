# 在這台 Windows 上登記兩個工作排程。電腦要開著、使用者要登入、Docker Desktop 要在跑。
# 備份 05:00，同步 06:00，錯開。關機或睡眠錯過的時間，醒來後會補跑。
# 手動：powershell -NoProfile -ExecutionPolicy Bypass -File ops\register_schedules.ps1

$ErrorActionPreference = "Stop"

$sync = Join-Path $PSScriptRoot "daily_sync.ps1"
$backup = Join-Path $PSScriptRoot "backup_db.ps1"

function Register-FootballTask([string]$Name, [string]$Script, [string]$At) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $At
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 12)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Output "registered $Name daily at $At"
}

Register-FootballTask -Name "FootballPredictionDbBackup" -Script $backup -At "05:00"
Register-FootballTask -Name "FootballPredictionDailySync" -Script $sync -At "06:00"

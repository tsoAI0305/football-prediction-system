# 每天跑一次資料同步。只負責切到專案目錄、確認容器、寫日誌、執行 master_sync.py。
# 爬蟲仍由 backend/scripts/master_sync.py 負責。
#
# 手動：
#   powershell -NoProfile -ExecutionPolicy Bypass -File ops\daily_sync.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File ops\daily_sync.ps1 --dry-run
#
# 需要 Docker Desktop 已啟動，且 api 容器在跑（docker compose up -d）。
# 容器裡的環境是啟動當下的 backend/.env；改了 .env 要重新 up 才會進去。

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$MasterSyncArgs
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("daily_sync_{0:yyyyMMdd}.log" -f (Get-Date))

function Write-Log([string]$Message) {
    $line = "{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $Message
    Add-Content -Path $Log -Value $line -Encoding utf8
}

Write-Log "start cwd=$Root"

$psOutput = & docker compose ps --status running --services 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "docker compose ps failed: $psOutput"
    exit 1
}
if (@($psOutput) -notcontains "api") {
    Write-Log "api 容器沒有在跑。先在專案目錄執行 docker compose up -d"
    exit 1
}

$stdout = Join-Path $env:TEMP ("football_daily_sync_out_{0}.log" -f $PID)
$stderr = Join-Path $env:TEMP ("football_daily_sync_err_{0}.log" -f $PID)
$argList = @("compose", "exec", "-T", "api", "python", "scripts/master_sync.py")
if ($MasterSyncArgs) {
    $argList += $MasterSyncArgs
}

$proc = Start-Process -FilePath "docker" -ArgumentList $argList -WorkingDirectory $Root -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
if (Test-Path $stdout) {
    Get-Content -Path $stdout -Encoding Unicode -ErrorAction SilentlyContinue | Add-Content -Path $Log -Encoding utf8
}
if (Test-Path $stderr) {
    Get-Content -Path $stderr -Encoding Unicode -ErrorAction SilentlyContinue | Add-Content -Path $Log -Encoding utf8
}
Remove-Item $stdout, $stderr -ErrorAction SilentlyContinue

$code = $proc.ExitCode
if ($null -eq $code) { $code = 1 }
Write-Log "exit $code"
exit $code

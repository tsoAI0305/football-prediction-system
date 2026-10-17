# 備份 Postgres，gzip 後保留 14 天。跟每日同步分開跑。
# 手動：powershell -NoProfile -ExecutionPolicy Bypass -File ops\backup_db.ps1
# 需要 Docker Desktop 已啟動，且 db 容器在跑。

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$BackupDir = Join-Path $PSScriptRoot "backups"
$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $BackupDir, $LogDir | Out-Null
$Log = Join-Path $LogDir ("backup_db_{0:yyyyMMdd}.log" -f (Get-Date))

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
if (@($psOutput) -notcontains "db") {
    Write-Log "db 容器沒有在跑。先在專案目錄執行 docker compose up -d"
    exit 1
}

$stamp = Get-Date -Format "yyyyMMdd"
$sql = Join-Path $env:TEMP "football_db_$stamp.sql"
$err = Join-Path $env:TEMP "football_db_$stamp.err"
$dest = Join-Path $BackupDir "football_db_$stamp.sql.gz"

# 密碼與 docker-compose.yml 的本機開發帳號相同，不寫進日誌。
$argList = @(
    "compose", "exec", "-T",
    "-e", "PGPASSWORD=football_pass",
    "db", "pg_dump", "-U", "football_user", "-d", "football_db", "--no-owner"
)
$proc = Start-Process -FilePath "docker" -ArgumentList $argList -WorkingDirectory $Root -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $sql -RedirectStandardError $err
if ($proc.ExitCode -ne 0) {
    $errText = ""
    if (Test-Path $err) { $errText = (Get-Content -Path $err -Encoding Unicode -Raw) }
    Write-Log "pg_dump failed exit $($proc.ExitCode) $errText"
    Remove-Item $sql, $err -ErrorAction SilentlyContinue
    exit $(if ($proc.ExitCode) { $proc.ExitCode } else { 1 })
}
if (-not (Test-Path $sql) -or (Get-Item $sql).Length -lt 100) {
    Write-Log "pg_dump 沒有寫出有效的 SQL"
    Remove-Item $sql, $err -ErrorAction SilentlyContinue
    exit 1
}

$inStream = [System.IO.File]::OpenRead($sql)
$outStream = [System.IO.File]::Create($dest)
try {
    $gzip = New-Object System.IO.Compression.GzipStream(
        $outStream,
        [System.IO.Compression.CompressionMode]::Compress
    )
    $inStream.CopyTo($gzip)
    $gzip.Dispose()
}
finally {
    $inStream.Dispose()
    $outStream.Dispose()
}
Remove-Item $sql, $err -ErrorAction SilentlyContinue

$cutoff = (Get-Date).AddDays(-14)
$removed = 0
Get-ChildItem -Path $BackupDir -Filter "football_db_*.sql.gz" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    ForEach-Object {
        Remove-Item $_.FullName
        $removed += 1
    }

Write-Log "wrote $dest removed=$removed"
exit 0

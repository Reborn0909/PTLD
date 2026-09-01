param(
    [string]$DataRootWsl = "/mnt/f/spatialecotyper_reproduction",
    [string]$DataRootWindows = "F:\spatialecotyper_reproduction"
)

$ErrorActionPreference = "Stop"
$runnerWindows = Join-Path $PSScriptRoot "complete_paper_reproduction.sh"
if (-not (Test-Path -LiteralPath $runnerWindows -PathType Leaf)) {
    throw "Completion runner not found: $runnerWindows"
}
$runnerForWsl = $runnerWindows -replace '\\', '/'
$runnerWsl = (wsl.exe -d Ubuntu -- wslpath -a $runnerForWsl).Trim()
if (-not $runnerWsl) {
    throw "Could not resolve WSL runner path"
}

$statusDir = Join-Path $DataRootWindows "results\reproducibility"
$logDir = Join-Path $DataRootWindows "results\logs"
$pidPath = Join-Path $statusDir "paper-completion.host.pid"
$statusPath = Join-Path $statusDir "paper-completion-status.tsv"
$stdoutPath = Join-Path $logDir "paper-completion.stdout.log"
$stderrPath = Join-Path $logDir "paper-completion.stderr.log"
New-Item -ItemType Directory -Force -Path $statusDir, $logDir | Out-Null

if (Test-Path -LiteralPath $pidPath) {
    $existingPid = (Get-Content -LiteralPath $pidPath -Raw).Trim()
    if ($existingPid -match '^\d+$' -and (Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue)) {
        Write-Output "Paper reproduction completion already running: host pid=$existingPid"
        exit 0
    }
}

$startedUtc = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$statusTemp = "$statusPath.part"
@(
    "status`tlast_step`texit_code`tstarted_utc`tcompleted_utc"
    "RUNNING`tbackground_runner`t`t$startedUtc`t"
) | Set-Content -LiteralPath $statusTemp -Encoding utf8NoBOM
Move-Item -LiteralPath $statusTemp -Destination $statusPath -Force

$arguments = @(
    "-d", "Ubuntu", "--", "bash", $runnerWsl, $DataRootWsl
)
$process = Start-Process -FilePath "wsl.exe" -ArgumentList $arguments `
    -WindowStyle Hidden -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath -PassThru
Set-Content -LiteralPath $pidPath -Value $process.Id -Encoding ascii -NoNewline
Write-Output "Paper reproduction completion launched: host pid=$($process.Id)"
Write-Output "stdout=$stdoutPath"
Write-Output "stderr=$stderrPath"

# scripts/run_benchmark.ps1
# ============================================================
# NT531 Benchmark Automation — PowerShell version cho Windows
# ============================================================
# Usage:
#   .\scripts\run_benchmark.ps1 -Strategy static_k2 -Profile spike -Runs 5 -Host http://192.168.1.100
#   .\scripts\run_benchmark.ps1 -Strategy hpa -Profile stable
# ============================================================

param(
    [Parameter(Mandatory=$true)][string]$Strategy,
    [Parameter(Mandatory=$true)][string]$Profile,
    [int]$Runs = 5,
    [string]$Host = "http://192.168.1.100",
    [int]$ResetWait = 420,
    [string]$Config = "config/default.yaml"
)

Write-Host "============================================================"
Write-Host "  NT531 BENCHMARK"
Write-Host "  Strategy:  $Strategy"
Write-Host "  Profile:   $Profile"
Write-Host "  Runs:      $Runs"
Write-Host "  Host:      $Host"
Write-Host "============================================================"

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

for ($i = 1; $i -le $Runs; $i++) {
    $RunId = "${Strategy}_${Profile}_run${i}"
    $Seed = 42 + $i

    Write-Host "`n--- Run ${i}/${Runs}: ${RunId} (seed=${Seed}) ---"
    Write-Host "    Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    # Set env vars
    $env:PROFILE = $Profile
    $env:LOCUST_CONFIG = $Config
    $env:LOCUST_SEED = $Seed
    $env:RUN_ID = $RunId

    if ($Profile -eq "stable") {
        # Stable: read users/duration from config
        $cfg = python -c "import yaml; c=yaml.safe_load(open('$Config')); print(c['profiles']['stable']['users'], c['profiles']['stable']['duration'])"
        $parts = $cfg -split ' '
        $Users = $parts[0]
        $Duration = $parts[1]

        locust -f locustfile.py `
            --host $Host `
            --headless `
            --users $Users `
            --spawn-rate $Users `
            --run-time "${Duration}s" `
            --csv "results/${RunId}" `
            --csv-full-history
    } else {
        locust -f locustfile.py `
            --host $Host `
            --headless `
            --csv "results/${RunId}" `
            --csv-full-history
    }

    Write-Host "    [DONE] Run ${i} completed."

    if ($i -lt $Runs) {
        Write-Host "    [WAIT] Waiting ${ResetWait}s for cluster reset..."
        Start-Sleep -Seconds $ResetWait
    }
}

Write-Host "`n============================================================"
Write-Host "  ALL ${Runs} RUNS COMPLETED: ${Strategy}/${Profile}"
Write-Host "============================================================"

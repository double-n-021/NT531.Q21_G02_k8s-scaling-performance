# scripts/run_kb2_suite.ps1
# ============================================================
# NT531 Automated Suite — Kịch bản 2: Reactive Scaling (HPA)
# ============================================================

$Strategy = "reactive-hpa"
$Config = "config/hpa_scenario.yaml"
$HostURL = if ($args[0]) { $args[0] } else { "http://localhost:8000" }
$Repeats = if ($args[1]) { $args[1] } else { 3 }

$Profiles = @("stable", "ramp", "spike", "spike_recovery", "oscillating")

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NT531 MASTER SUITE: STRATEGY $Strategy"
Write-Host "  Target Host: $HostURL"
Write-Host "  Config:      $Config"
Write-Host "  Executing all $($Profiles.Count) profiles, each with $Repeats repeats..."
Write-Host "============================================================" -ForegroundColor Cyan

if (-not (Test-Path "results")) { New-Item -ItemType Directory -Path "results" }

foreach ($P in $Profiles) {
    Write-Host "`n>>> STARTING PROFILE: $P <<<" -ForegroundColor Yellow
    
    $env:LOCUST_CONFIG = $Config
    
    # Lấy reset_wait từ config
    $WaitTime = python -c "import yaml; c=yaml.safe_load(open('$Config')); print(c['experiment'].get('reset_wait', 180))"
    
    & ./scripts/run_benchmark.ps1 $Strategy $P $Repeats $HostURL $WaitTime
    
    Write-Host ">>> FINISHED PROFILE: $P <<<" -ForegroundColor Green
    Write-Host "------------------------------------------------------------"
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SUITE COMPLETED: $Strategy"
Write-Host "============================================================" -ForegroundColor Cyan

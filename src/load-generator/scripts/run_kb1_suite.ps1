# scripts/run_kb1_suite.ps1
# ============================================================
# NT531 Master Suite — Chạy trọn bộ 5 Profiles cho Static Baseline
# ============================================================
# Usage:
#   .\scripts\run_kb1_suite.ps1 -K 2 -Host http://<IP_KIEN>:8000
# ============================================================

param(
    [Parameter(Mandatory=$true)][int]$K,
    [Parameter(Mandatory=$true)][string]$Host,
    [int]$Repeats = 5
)

$Profiles = @("stable", "ramp", "spike", "spike_recovery", "oscillating")
$Config = "config/k${K}.yaml"
$Strategy = "static-k${K}"

if (-not (Test-Path $Config)) {
    Write-Error "Khong tim thay file config: $Config. Hay chay lenh tu thu muc src/load-generator/"
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NT531 MASTER SUITE: STRATEGY $Strategy" -ForegroundColor Cyan
Write-Host "  Target Host: $Host"
Write-Host "  Executing all 5 profiles, each with $Repeats repeats..."
Write-Host "============================================================" -ForegroundColor Cyan

foreach ($P in $Profiles) {
    Write-Host "`n>>> STARTING PROFILE: $P <<<" -ForegroundColor Yellow
    
    # Goi script benchmark thuc thi
    & ".\scripts\run_benchmark.ps1" -Strategy $Strategy -Profile $P -Runs $Repeats -Host $Host -Config $Config
    
    Write-Host ">>> FINISHED PROFILE: $P <<<" -ForegroundColor Green
    Write-Host "------------------------------------------------------------"
}

Write-Host "`n[CONGRATS] Hoan thanh tron bo kịch bản Static cho K=$K!" -ForegroundColor Magentastartcall:default_api:write_to_file{CodeContent:# scripts/run_kb1_suite.ps1
# ============================================================
# NT531 Master Suite — Chạy trọn bộ 5 Profiles cho Static Baseline
# ============================================================
# Usage:
#   .\scripts\run_kb1_suite.ps1 -K 2 -Host http://<IP_KIEN>:8000
# ============================================================

param(
    [Parameter(Mandatory=$true)][int]$K,
    [Parameter(Mandatory=$true)][string]$Host,
    [int]$Repeats = 5
)

$Profiles = @("stable", "ramp", "spike", "spike_recovery", "oscillating")
$Config = "config/k${K}.yaml"
$Strategy = "static-k${K}"

# Dam bao dang o thu muc load-generator
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

if (-not (Test-Path $Config)) {
    Write-Error "Khong tim thay file config: $Config. Hay dam bao ban dang chay tu thu muc src/load-generator/"
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NT531 MASTER SUITE: STRATEGY $Strategy" -ForegroundColor Cyan
Write-Host "  Target Host: $Host"
Write-Host "  Config:      $Config"
Write-Host "  Executing all 5 profiles, each with $Repeats repeats..."
Write-Host "============================================================" -ForegroundColor Cyan

foreach ($P in $Profiles) {
    Write-Host "`n>>> STARTING PROFILE: $P <<<" -ForegroundColor Yellow
    
    # Goi script benchmark thuc thi
    # Chu y: run_benchmark.ps1 can file config tuong ung
    & ".\scripts\run_benchmark.ps1" -Strategy $Strategy -Profile $P -Runs $Repeats -Host $Host -Config $Config
    
    Write-Host ">>> FINISHED PROFILE: $P <<<" -ForegroundColor Green
    Write-Host "------------------------------------------------------------"
}

Write-Host "`n[SUCCESS] Hoan thanh tron bo kịch bản Static cho K=$K!" -ForegroundColor Magenta
Write-Host "Data da duoc luu tai thu muc: results/"
,Description:Tạo script PowerShell tự động chạy trọn bộ 5 profile cho kịch bản Static Baseline phục vụ đồ án NT531.,IsArtifact:false,Overwrite:true,TargetFile:f:\HK_VI_2026\NT531_Danh-gia-hieu-nang-he-thong-mang-may-tinh\_repo_clone\src\load-generator\scripts\run_kb1_suite.ps1,toolAction:Creating master suite script,toolSummary:Create run_kb1_suite.ps1}

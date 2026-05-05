param(
    [switch]$PushAndroidFront,
    [switch]$SkipAndroid,
    [switch]$FullRebuildSupabase,
    [string]$GitHubOwner = "GTIImmo",
    [string]$GitHubRepo = "vitrine",
    [string]$GitHubBranch = "main",
    [string]$GitHubPath = "exports/catalogue_vitrine.json",
    [string]$GitHubTokenFile = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$logDir = Join-Path $projectRoot ".tmp"

if (-not $GitHubTokenFile) {
    $GitHubTokenFile = Join-Path $projectRoot "Ecrans Android\github_token.txt"
}

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at $pythonExe"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runLog = Join-Path $logDir "full_pipeline_$timestamp.log"

function Write-RunLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Output $line
    Add-Content -Path $runLog -Value $line
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-RunLog "START $Label"
    & $pythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label (exit code $LASTEXITCODE)"
    }
    Write-RunLog "DONE  $Label"
}

Set-Location $projectRoot

Write-RunLog "Pipeline started"
Write-RunLog "Log file: $runLog"
Write-RunLog "Options: PushAndroidFront=$PushAndroidFront SkipAndroid=$SkipAndroid FullRebuildSupabase=$FullRebuildSupabase"

Invoke-Step -Label "phase1 sync_raw update" -Arguments @(
    "sync_raw.py",
    "--mode", "update",
    "--resources", "annonces", "contacts", "mandats", "offres", "compromis", "ventes", "broadcasts",
    "--missing-only"
)

Invoke-Step -Label "normalize_source" -Arguments @(
    "normalize_source.py"
)

Invoke-Step -Label "build_case_index" -Arguments @(
    "build_case_index.py"
)

Invoke-Step -Label "phase2 bootstrap" -Arguments @(
    "phase2\bootstrap_phase2.py"
)

Invoke-Step -Label "phase2 refresh views" -Arguments @(
    "phase2\refresh_views.py"
)

Invoke-Step -Label "phase2 quality checks" -Arguments @(
    "phase2\checks\run_quality_checks.py"
)

$supabaseArgs = @(
    "phase2\sync\push_upgrade_to_supabase.py",
    "--dossier-batch-size", "50",
    "--detail-batch-size", "25",
    "--work-item-batch-size", "50",
    "--filter-batch-size", "50"
)
if ($FullRebuildSupabase) {
    $supabaseArgs = @("phase2\sync\push_upgrade_to_supabase.py", "--full-rebuild") + $supabaseArgs[1..($supabaseArgs.Length - 1)]
}
Invoke-Step -Label "phase2 push upgrade to supabase" -Arguments $supabaseArgs

Invoke-Step -Label "phase2 push hektor directory to supabase" -Arguments @(
    "phase2\sync\push_hektor_directory_to_supabase.py"
)

Invoke-Step -Label "phase2 sync Matterport links to supabase" -Arguments @(
    "phase2\sync\sync_matterport_models.py",
    "--max-models", "0",
    "--supabase-upsert"
)

Invoke-Step -Label "backfill appointment public links" -Arguments @(
    "backend\scripts\backfill_appointment_public_links.py",
    "--quiet"
)

if (-not $SkipAndroid) {
    if (-not (Test-Path $GitHubTokenFile)) {
        throw "GitHub token file not found: $GitHubTokenFile"
    }

    $androidArgs = @(
        "Ecrans Android\export_project_vitrine.py",
        "--push-github",
        "--github-owner", $GitHubOwner,
        "--github-repo", $GitHubRepo,
        "--github-branch", $GitHubBranch,
        "--github-path", $GitHubPath,
        "--github-token-file", $GitHubTokenFile
    )
    if ($PushAndroidFront) {
        $androidArgs += "--push-front"
    }

    Invoke-Step -Label "android vitrine export and push" -Arguments $androidArgs
}
else {
    Write-RunLog "SKIP android vitrine export and push"
}

Write-RunLog "Pipeline finished successfully"

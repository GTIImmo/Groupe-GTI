param(
    [switch]$PushAndroidFront,
    [switch]$SkipAndroid,
    [switch]$SkipContactDetails,
    [int]$DailyRawMaxPages = 0,
    [int]$ContactDetailLimit = 1000,
    [int]$ContactDetailBatchSize = 1000,
    [int]$ContactDetailMaxAttempts = 1,
    [int]$ContactDetailRetryDelaySeconds = 600,
    [double]$ContactDetailRequestDelaySeconds = 0.1,
    [int]$ContactDetailBatchPauseSeconds = 60,
    [int]$ContactDetailMaxHardErrors = 1,
    [int]$ContactDetailMaxConsecutiveHardErrors = 1,
    [int]$ContactDetailMax404Errors = 0,
    [int]$ContactDetailMaxConsecutive404Errors = 0,
    [int]$ContactDetailClientMaxRetries = 1,
    [switch]$FailOnContactDetailsError,
    [switch]$SkipHektorChauffage,
    [ValidateSet("all", "current")]
    [string]$HektorChauffageScope = "current",
    [int]$HektorChauffageLimit = 50,
    [int]$HektorChauffageStaleDays = 30,
    [double]$HektorChauffageDelaySeconds = 0.5,
    [int]$HektorChauffageBatchSize = 50,
    [int]$HektorChauffageBatchPauseSeconds = 30,
    [string]$HektorChauffageStorageState = "",
    [switch]$HektorChauffageForce,
    [switch]$HektorChauffageSkipJobCheck,
    [bool]$HektorChauffageRefreshSession = $true,
    [switch]$RunConsoleMissingFields,
    [switch]$SkipConsoleMissingFields,
    [ValidateSet("all", "current")]
    [string]$ConsoleMissingFieldsAnnonceScope = "all",
    [int]$ConsoleMissingFieldsLimit = 25,
    [int]$ConsoleMissingFieldsStaleDays = 30,
    [double]$ConsoleMissingFieldsDelaySeconds = 10,
    [int]$ConsoleMissingFieldsBatchSize = 10,
    [int]$ConsoleMissingFieldsBatchPauseSeconds = 60,
    [string]$ConsoleMissingFieldsStorageState = "",
    [switch]$ConsoleMissingFieldsForce,
    [switch]$ConsoleMissingFieldsSkipJobCheck,
    [switch]$ConsoleMissingFieldsRefreshSession,
    [switch]$PushContactsToSupabase,
    [switch]$ContactsEligibleOnly,
    [switch]$IncludeArchivedContactRelations,
    [switch]$IncludeArchivedContactSearches,
    [ValidateSet("full", "update")]
    [string]$MatterportPushMode = "update",
    [switch]$FullRebuildSupabase,
    [string]$SupabaseSinceWatermark = "",
    [switch]$AllowStaleSupabaseDeletes,
    [switch]$EnqueueConsoleDocuments,
    [switch]$EnqueueAllConsoleDocumentsLocal,
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

function Invoke-OptionalStepWithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [int]$MaxAttempts = 1,
        [int]$RetryDelaySeconds = 120,
        [switch]$FailOnError,
        [ref]$Succeeded
    )

    if ($Succeeded) {
        $Succeeded.Value = $false
    }
    $attempts = [Math]::Max(1, $MaxAttempts)
    for ($attempt = 1; $attempt -le $attempts; $attempt++) {
        Write-RunLog "START $Label attempt $attempt/$attempts"
        & $pythonExe @Arguments
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            Write-RunLog "DONE  $Label attempt $attempt/$attempts"
            if ($Succeeded) {
                $Succeeded.Value = $true
            }
            return
        }

        Write-RunLog "WARN  $Label failed attempt $attempt/$attempts (exit code $exitCode)"
        if ($attempt -lt $attempts) {
            Write-RunLog "WAIT  $Label retry in $RetryDelaySeconds seconds"
            Start-Sleep -Seconds ([Math]::Max(1, $RetryDelaySeconds))
        }
    }

    if ($FailOnError) {
        throw "Step failed: $Label after $attempts attempt(s)"
    }

    Write-RunLog "SKIP  $Label after $attempts failed attempt(s); pipeline continues with existing local contact details"
    return
}

Set-Location $projectRoot

Write-RunLog "Pipeline started"
Write-RunLog "Log file: $runLog"
Write-RunLog "Options: PushAndroidFront=$PushAndroidFront SkipAndroid=$SkipAndroid FullRebuildSupabase=$FullRebuildSupabase SupabaseSinceWatermark=$SupabaseSinceWatermark AllowStaleSupabaseDeletes=$AllowStaleSupabaseDeletes SkipContactDetails=$SkipContactDetails DailyRawMaxPages=$DailyRawMaxPages ContactDetailLimit=$ContactDetailLimit ContactDetailBatchSize=$ContactDetailBatchSize ContactDetailMaxAttempts=$ContactDetailMaxAttempts ContactDetailRetryDelaySeconds=$ContactDetailRetryDelaySeconds ContactDetailRequestDelaySeconds=$ContactDetailRequestDelaySeconds ContactDetailBatchPauseSeconds=$ContactDetailBatchPauseSeconds ContactDetailMaxHardErrors=$ContactDetailMaxHardErrors ContactDetailMaxConsecutiveHardErrors=$ContactDetailMaxConsecutiveHardErrors ContactDetailMax404Errors=$ContactDetailMax404Errors ContactDetailMaxConsecutive404Errors=$ContactDetailMaxConsecutive404Errors ContactDetailClientMaxRetries=$ContactDetailClientMaxRetries FailOnContactDetailsError=$FailOnContactDetailsError SkipHektorChauffage=$SkipHektorChauffage HektorChauffageScope=$HektorChauffageScope HektorChauffageLimit=$HektorChauffageLimit HektorChauffageStaleDays=$HektorChauffageStaleDays HektorChauffageDelaySeconds=$HektorChauffageDelaySeconds HektorChauffageBatchSize=$HektorChauffageBatchSize HektorChauffageBatchPauseSeconds=$HektorChauffageBatchPauseSeconds HektorChauffageForce=$HektorChauffageForce HektorChauffageSkipJobCheck=$HektorChauffageSkipJobCheck RunConsoleMissingFields=$RunConsoleMissingFields SkipConsoleMissingFields=$SkipConsoleMissingFields ConsoleMissingFieldsAnnonceScope=$ConsoleMissingFieldsAnnonceScope ConsoleMissingFieldsLimit=$ConsoleMissingFieldsLimit ConsoleMissingFieldsStaleDays=$ConsoleMissingFieldsStaleDays ConsoleMissingFieldsDelaySeconds=$ConsoleMissingFieldsDelaySeconds ConsoleMissingFieldsBatchSize=$ConsoleMissingFieldsBatchSize ConsoleMissingFieldsBatchPauseSeconds=$ConsoleMissingFieldsBatchPauseSeconds ConsoleMissingFieldsForce=$ConsoleMissingFieldsForce ConsoleMissingFieldsSkipJobCheck=$ConsoleMissingFieldsSkipJobCheck PushContactsToSupabase=$PushContactsToSupabase ContactsEligibleOnly=$ContactsEligibleOnly MatterportPushMode=$MatterportPushMode"

Invoke-Step -Label "phase1 sync_raw update" -Arguments @(
    "sync_raw.py",
    "--mode", "update",
    "--resources", "negos", "annonces", "contacts", "mandats", "offres", "compromis", "ventes", "broadcasts",
    "--max-pages", [string]$DailyRawMaxPages,
    "--missing-only"
)

Invoke-Step -Label "normalize_source" -Arguments @(
    "normalize_source.py"
)

if (-not $SkipContactDetails) {
    $contactDetailsOk = $false
    $contactDetailRequestDelayArg = $ContactDetailRequestDelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    Invoke-OptionalStepWithRetry -Label "contact details delta" -Arguments @(
        "phase2\sync\sync_contact_details.py",
        "--limit", [string]$ContactDetailLimit,
        "--batch-size", [string]$ContactDetailBatchSize,
        "--skip-listing-refresh",
        "--changed-only",
        "--request-delay-seconds", $contactDetailRequestDelayArg,
        "--batch-pause-seconds", [string]$ContactDetailBatchPauseSeconds,
        "--max-hard-errors", [string]$ContactDetailMaxHardErrors,
        "--max-consecutive-hard-errors", [string]$ContactDetailMaxConsecutiveHardErrors,
        "--max-404-errors", [string]$ContactDetailMax404Errors,
        "--max-consecutive-404-errors", [string]$ContactDetailMaxConsecutive404Errors,
        "--client-max-retries", [string]$ContactDetailClientMaxRetries,
        "--no-normalize"
    ) -MaxAttempts $ContactDetailMaxAttempts -RetryDelaySeconds $ContactDetailRetryDelaySeconds -FailOnError:$FailOnContactDetailsError -Succeeded ([ref]$contactDetailsOk)

    if ($contactDetailsOk) {
        Invoke-Step -Label "normalize_source after contact details" -Arguments @(
            "normalize_source.py"
        )
    }
    else {
        Write-RunLog "SKIP normalize_source after contact details because contact detail delta did not complete"
    }
}
else {
    Write-RunLog "SKIP contact details delta"
}

Invoke-Step -Label "build_case_index" -Arguments @(
    "build_case_index.py"
)

Invoke-Step -Label "phase2 bootstrap" -Arguments @(
    "phase2\bootstrap_phase2.py"
)

Invoke-Step -Label "phase2 refresh views" -Arguments @(
    "phase2\refresh_views.py"
)

Invoke-Step -Label "phase2 build contacts layer" -Arguments @(
    "phase2\contacts\build_contacts_layer.py",
    "--no-reports"
)

Invoke-Step -Label "phase2 quality checks" -Arguments @(
    "phase2\checks\run_quality_checks.py"
)

Invoke-Step -Label "phase2 contact sync status" -Arguments @(
    "phase2\checks\contact_sync_status.py"
)

if (-not $SkipHektorChauffage -and $HektorChauffageLimit -gt 0) {
    $hektorChauffageDelayArg = $HektorChauffageDelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    $hektorChauffageArgs = @(
        "phase2\sync\sync_hektor_chauffages.py",
        "--scope", $HektorChauffageScope,
        "--limit", [string]$HektorChauffageLimit,
        "--stale-days", [string]$HektorChauffageStaleDays,
        "--delay-seconds", $hektorChauffageDelayArg,
        "--batch-size", [string]$HektorChauffageBatchSize,
        "--batch-pause-seconds", [string]$HektorChauffageBatchPauseSeconds
    )
    if ($HektorChauffageStorageState) {
        $hektorChauffageArgs += @("--storage-state", $HektorChauffageStorageState)
    }
    if ($HektorChauffageForce) {
        $hektorChauffageArgs += "--force"
    }
    if ($HektorChauffageSkipJobCheck) {
        $hektorChauffageArgs += "--skip-job-check"
    }
    if ($HektorChauffageRefreshSession) {
        $hektorChauffageArgs += "--refresh-session-on-expired"
    }
    Invoke-Step -Label "hektor chauffage delta" -Arguments $hektorChauffageArgs
}
else {
    Write-RunLog "SKIP hektor chauffage delta"
}

if ($RunConsoleMissingFields -and -not $SkipConsoleMissingFields -and $ConsoleMissingFieldsLimit -gt 0) {
    $consoleMissingDelayArg = $ConsoleMissingFieldsDelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    $consoleMissingArgs = @(
        "phase2\sync\sync_console_missing_fields.py",
        "--annonce-scope", $ConsoleMissingFieldsAnnonceScope,
        "--limit", [string]$ConsoleMissingFieldsLimit,
        "--stale-days", [string]$ConsoleMissingFieldsStaleDays,
        "--delay-seconds", $consoleMissingDelayArg,
        "--batch-size", [string]$ConsoleMissingFieldsBatchSize,
        "--batch-pause-seconds", [string]$ConsoleMissingFieldsBatchPauseSeconds
    )
    if ($ConsoleMissingFieldsStorageState) {
        $consoleMissingArgs += @("--storage-state", $ConsoleMissingFieldsStorageState)
    }
    if ($ConsoleMissingFieldsForce) {
        $consoleMissingArgs += "--force"
    }
    if ($ConsoleMissingFieldsSkipJobCheck) {
        $consoleMissingArgs += "--skip-job-check"
    }
    if ($ConsoleMissingFieldsRefreshSession) {
        $consoleMissingArgs += "--refresh-session-on-expired"
    }
    Invoke-Step -Label "console missing fields delta" -Arguments $consoleMissingArgs
}
else {
    Write-RunLog "SKIP console missing fields delta (not requested)"
}

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
else {
    $supabaseArgs += "--all-local-current"
}
if ($SupabaseSinceWatermark) {
    $supabaseArgs += @("--since-watermark", $SupabaseSinceWatermark)
}
if (-not $AllowStaleSupabaseDeletes) {
    $supabaseArgs += "--skip-stale-deletes"
}
Invoke-Step -Label "phase2 push upgrade to supabase" -Arguments $supabaseArgs

Invoke-Step -Label "phase2 push hektor directory to supabase" -Arguments @(
    "phase2\sync\push_hektor_directory_to_supabase.py"
)

if ($PushContactsToSupabase) {
    $contactsScope = if ($ContactsEligibleOnly) { "eligible" } else { "active_or_eligible" }
    $contactsPushArgs = @(
        "phase2\sync\push_contacts_to_supabase.py",
        "--push-mode", "update",
        "--contacts-scope", $contactsScope
    )
    if ($IncludeArchivedContactRelations) {
        $contactsPushArgs += "--include-archived-relations"
    }
    if ($IncludeArchivedContactSearches) {
        $contactsPushArgs += "--include-archived-searches"
    }
    Invoke-Step -Label "phase2 push contacts to supabase" -Arguments $contactsPushArgs
}
else {
    Write-RunLog "SKIP phase2 push contacts to supabase"
}

if ($EnqueueConsoleDocuments -or $EnqueueAllConsoleDocumentsLocal) {
    $nodeCandidates = @(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe",
        "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    $nodeExe = if ($nodeCandidates.Count -gt 0) { $nodeCandidates[0] } else { "node.exe" }
    $consoleScript = Join-Path $projectRoot "Console\enqueue_console_sync_jobs.js"
    if (-not (Test-Path -LiteralPath $consoleScript)) {
        throw "Console enqueue script not found: $consoleScript"
    }
    $scope = if ($EnqueueAllConsoleDocumentsLocal) { "all-local" } else { "daily-cloud" }
    Write-RunLog "START enqueue console documents ($scope)"
    & $nodeExe $consoleScript "--scope" $scope
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: enqueue console documents (exit code $LASTEXITCODE)"
    }
    Write-RunLog "DONE  enqueue console documents ($scope)"
}

Invoke-Step -Label "phase2 sync Matterport links to supabase" -Arguments @(
    "phase2\sync\sync_matterport_models.py",
    "--max-models", "0",
    "--supabase-upsert",
    "--supabase-push-mode", $MatterportPushMode
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

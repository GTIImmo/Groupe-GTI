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
    [int]$HektorChauffageBatchPauseSeconds = 0,
    [string]$HektorChauffageStorageState = "",
    [switch]$HektorChauffageForce,
    [switch]$HektorChauffageSkipJobCheck,
    [bool]$HektorChauffageRefreshSession = $true,
    [switch]$SkipContactMissing,
    [int]$ContactMissingLimit = 50,
    [int]$ContactMissingStaleDays = 30,
    [bool]$ContactMissingRefreshSession = $true,
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

function Send-Heartbeat {
    # Palier 1 / Lot 1.2 : signale l'execution d'un worker dans app_worker_registry.
    # Best-effort STRICT : ne doit JAMAIS interrompre le pipeline ni polluer $LASTEXITCODE.
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkerKey,
        [Parameter(Mandatory = $true)]
        [ValidateSet("success", "error", "running")]
        [string]$Status
    )

    try {
        $hbScript = Join-Path $projectRoot "monitoring\heartbeat.py"
        if (Test-Path -LiteralPath $hbScript) {
            & $pythonExe $hbScript "--worker" $WorkerKey "--status" $Status | Out-Null
        }
    }
    catch {
        Write-RunLog "WARN heartbeat report failed for $WorkerKey ($Status): $($_.Exception.Message)"
    }
    finally {
        $global:LASTEXITCODE = 0
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$WorkerKey = ""
    )

    Write-RunLog "START $Label"
    & $pythonExe @Arguments
    $stepExit = $LASTEXITCODE
    if ($stepExit -ne 0) {
        if ($WorkerKey) { Send-Heartbeat -WorkerKey $WorkerKey -Status "error" }
        throw "Step failed: $Label (exit code $stepExit)"
    }
    Write-RunLog "DONE  $Label"
    if ($WorkerKey) { Send-Heartbeat -WorkerKey $WorkerKey -Status "success" }
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
        [ref]$Succeeded,
        [string]$WorkerKey = ""
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
            if ($WorkerKey) { Send-Heartbeat -WorkerKey $WorkerKey -Status "success" }
            return
        }

        Write-RunLog "WARN  $Label failed attempt $attempt/$attempts (exit code $exitCode)"
        if ($attempt -lt $attempts) {
            Write-RunLog "WAIT  $Label retry in $RetryDelaySeconds seconds"
            Start-Sleep -Seconds ([Math]::Max(1, $RetryDelaySeconds))
        }
    }

    if ($WorkerKey) { Send-Heartbeat -WorkerKey $WorkerKey -Status "error" }

    if ($FailOnError) {
        throw "Step failed: $Label after $attempts attempt(s)"
    }

    Write-RunLog "SKIP  $Label after $attempts failed attempt(s); pipeline continues with existing local contact details"
    return
}

Set-Location $projectRoot

# Panier Brouillon : active l'exclusion isDraft du scope actif + l'alimentation de
# l'index brouillon (lu par phase2/sync/export_app_payload.py via le push).
$env:APP_BROUILLON_BUCKET_ENABLED = "1"

$hektorChauffageDailyMax = 50
if (-not $SkipHektorChauffage -and $HektorChauffageLimit -gt $hektorChauffageDailyMax) {
    throw "Safety stop: le run quotidien chauffage est limite a $hektorChauffageDailyMax annonces. Utiliser phase2\sync\sync_hektor_chauffages.py directement pour un rattrapage."
}
if (-not $SkipHektorChauffage -and $HektorChauffageLimit -gt 0 -and $HektorChauffageBatchSize -lt $HektorChauffageLimit) {
    throw "Safety stop: le run quotidien chauffage doit rester sur un seul lot. HektorChauffageBatchSize doit etre superieur ou egal a HektorChauffageLimit."
}

Write-RunLog "Pipeline started"
Write-RunLog "Log file: $runLog"
Write-RunLog "Options: PushAndroidFront=$PushAndroidFront SkipAndroid=$SkipAndroid FullRebuildSupabase=$FullRebuildSupabase SupabaseSinceWatermark=$SupabaseSinceWatermark AllowStaleSupabaseDeletes=$AllowStaleSupabaseDeletes SkipContactDetails=$SkipContactDetails DailyRawMaxPages=$DailyRawMaxPages ContactDetailLimit=$ContactDetailLimit ContactDetailBatchSize=$ContactDetailBatchSize ContactDetailMaxAttempts=$ContactDetailMaxAttempts ContactDetailRetryDelaySeconds=$ContactDetailRetryDelaySeconds ContactDetailRequestDelaySeconds=$ContactDetailRequestDelaySeconds ContactDetailBatchPauseSeconds=$ContactDetailBatchPauseSeconds ContactDetailMaxHardErrors=$ContactDetailMaxHardErrors ContactDetailMaxConsecutiveHardErrors=$ContactDetailMaxConsecutiveHardErrors ContactDetailMax404Errors=$ContactDetailMax404Errors ContactDetailMaxConsecutive404Errors=$ContactDetailMaxConsecutive404Errors ContactDetailClientMaxRetries=$ContactDetailClientMaxRetries FailOnContactDetailsError=$FailOnContactDetailsError SkipHektorChauffage=$SkipHektorChauffage HektorChauffageScope=$HektorChauffageScope HektorChauffageLimit=$HektorChauffageLimit HektorChauffageStaleDays=$HektorChauffageStaleDays HektorChauffageDelaySeconds=$HektorChauffageDelaySeconds HektorChauffageBatchSize=$HektorChauffageBatchSize HektorChauffageBatchPauseSeconds=$HektorChauffageBatchPauseSeconds HektorChauffageForce=$HektorChauffageForce HektorChauffageSkipJobCheck=$HektorChauffageSkipJobCheck RunConsoleMissingFields=$RunConsoleMissingFields SkipConsoleMissingFields=$SkipConsoleMissingFields ConsoleMissingFieldsAnnonceScope=$ConsoleMissingFieldsAnnonceScope ConsoleMissingFieldsLimit=$ConsoleMissingFieldsLimit ConsoleMissingFieldsStaleDays=$ConsoleMissingFieldsStaleDays ConsoleMissingFieldsDelaySeconds=$ConsoleMissingFieldsDelaySeconds ConsoleMissingFieldsBatchSize=$ConsoleMissingFieldsBatchSize ConsoleMissingFieldsBatchPauseSeconds=$ConsoleMissingFieldsBatchPauseSeconds ConsoleMissingFieldsForce=$ConsoleMissingFieldsForce ConsoleMissingFieldsSkipJobCheck=$ConsoleMissingFieldsSkipJobCheck PushContactsToSupabase=$PushContactsToSupabase ContactsEligibleOnly=$ContactsEligibleOnly MatterportPushMode=$MatterportPushMode"

# La ressource "mandats" a ete retiree le 21/07/2026. Elle declenchait deux appels
# qui n'apportent plus rien :
#   - ListMandat : n'expose que les mandats n 1 a 18339 (dernier au 30/01/2026) et
#     s'arrete la. Verifie par appels reels, sur 7 fenetres de dates jusqu'a
#     2000-01-01 -> 2099-12-31, et confirme par le rapatriement complet du 30/03/2026
#     (6 490 mandats, aucun posterieur au 30/01). Les 392 mandats plus recents
#     (n 18340 a 18767) n'y figurent pas. Redemander ces 25 pages chaque nuit ne
#     ramenait donc que des mandats deja en base.
#   - MandatById : gele depuis le 21/05/2026 faute de nouveaux identifiants a traiter,
#     et redondant (memes champs que MandatsByIdAnnonce).
# Aucune donnee n'est perdue : les reponses ListMandat deja stockees ne sont jamais
# purgees (prune_raw_listing_pages ne s'applique qu'aux listings d'annonces), et
# normalize_source continue de les lire pour alimenter les 23 644 mandats anciens.
# La fraicheur des mandats vient entierement de MandatsByIdAnnonce, appele avec le
# detail de chaque annonce (voir sync_annonce_details_with_mandats), ainsi que du
# read-through -- tous deux inchanges.
Invoke-Step -Label "phase1 sync_raw update" -Arguments @(
    "sync_raw.py",
    "--mode", "update",
    "--resources", "negos", "annonces", "contacts", "offres", "compromis", "ventes", "broadcasts",
    "--max-pages", [string]$DailyRawMaxPages,
    "--missing-only"
) -WorkerKey "phase1.sync_raw"

Invoke-Step -Label "normalize_source" -Arguments @(
    "normalize_source.py"
) -WorkerKey "phase1.normalize_source"

# Panier Brouillon : rafraichit l'etat isDraft (GraphQL Console, lecture seule) dans
# hektor_annonce_draft_state. Non bloquant : si la session est expiree, le run continue.
Invoke-OptionalStepWithRetry -Label "hektor drafts sweep (isDraft)" -Arguments @(
    "phase2\sync\sync_hektor_drafts.py"
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
    ) -MaxAttempts $ContactDetailMaxAttempts -RetryDelaySeconds $ContactDetailRetryDelaySeconds -FailOnError:$FailOnContactDetailsError -Succeeded ([ref]$contactDetailsOk) -WorkerKey "contacts.sync_detail"

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

# Filet mandats, purement ADDITIF : depuis que la cle primaire porte le couple
# (annonce, mandat), normalize_source reconstruit hektor_mandat correctement tout seul
# -- mesure sur copie : 1 seule annonce active sans dates, sans cette etape.
# Elle ne sert donc que de securite : hektor_annonce_detail.mandats_json vit dans une
# table permanente, la ou les reponses brutes d'API peuvent etre purgees. Le jour ou
# cela arrive, les mandats sont rattrapes ici. Cout : ~1 seconde.
# Optionnelle a dessein : une simple securite ne doit jamais interrompre le run.
Invoke-OptionalStepWithRetry -Label "backfill mandats depuis mandats_json" -Arguments @(
    "phase2\sync\backfill_hektor_mandats.py"
) -WorkerKey "phase1.backfill_mandats"

Invoke-Step -Label "build_case_index" -Arguments @(
    "build_case_index.py"
) -WorkerKey "phase1.build_case_index"

Invoke-Step -Label "phase2 bootstrap" -Arguments @(
    "phase2\bootstrap_phase2.py"
) -WorkerKey "phase2.bootstrap"

Invoke-Step -Label "phase2 refresh views" -Arguments @(
    "phase2\refresh_views.py"
) -WorkerKey "phase2.refresh_views"

# C.7 25/08 -- L'ENDROIT OU L'ECART SE RESOUT.
# ICI, et l'ordre n'est pas negociable : l'etape juste au-dessus vient de DETRUIRE et
# de refaire app_view_generale depuis le miroir -- donc Hektor vient de regagner sur
# tout. C'est maintenant, et seulement maintenant, qu'on relit dans Supabase ce que
# l'app detient et qu'on le repose. Et c'est AVANT le push, qui enverra la table deja
# arbitree : le push lui-meme ne change pas d'un iota.
# AUJOURD'HUI ELLE NE FAIT RIEN : le contrat d'annonce est vide, donc « Hektor gagne
# partout », donc comportement identique. La machinerie existe ; l'interrupteur est
# dans phase2/identite/contrat_autorite.py.
Invoke-Step -Label "phase2 appliquer le contrat d autorite" -Arguments @(
    "phase2\identite\appliquer_contrat.py"
) -WorkerKey "phase2.contrat_autorite"

# 26bis-(1) 26/08 -- LES ANNONCES QUE L'APP CONNAIT ET QUE LE MIROIR IGNORE.
# Le contrat ci-dessus sait METTRE A JOUR une ligne d'app_view_generale ; il ne sait pas
# en CREER. Or une annonce NEE DANS L'APP n'a aucune ligne dans le miroir, donc aucune
# dans la vue : le serveur ne la connait pas du tout. Cette etape la RECENSE, en relisant
# Supabase en direct (la copie locale a 22 h de retard a 05:30 -- meme raison que C.7).
# ON NE BRANCHE QUE --recenser, PAS --injecter. Poser ces lignes dans app_view_generale
# changerait ce que le push envoie vers Supabase, avec 84 colonnes vides sur 130 : c'est
# l'etape C, elle se decide plus tard, champ par champ. Ici on OBSERVE, personne ne lit.
# AUJOURD'HUI : ZERO annonce dans ce cas (mesure du 26/08). L'etape est donc inerte.
Invoke-Step -Label "phase2 annonces connues de l app seule" -Arguments @(
    "phase2\identite\annonces_app_seule.py",
    "--recenser"
) -WorkerKey "phase2.annonces_app_seule"

Invoke-Step -Label "phase2 build contacts layer" -Arguments @(
    "phase2\contacts\build_contacts_layer.py",
    "--no-reports"
) -WorkerKey "phase2.contacts_layer"

# C.2b 25/08 -- le registre d'identite des contacts (app_contact).
# ICI et pas ailleurs : il se nourrit de app_contact_current, que l'etape juste au-dessus
# vient de reconstruire. Un registre qui ne se maintient pas rote des le lendemain --
# constate le jour meme de sa creation : 15 contacts crees la veille etaient deja dans
# Supabase et pas encore en local. Idempotent : sans nouveaute il affiche 0/0/0.
Invoke-Step -Label "phase2 registre identite contacts" -Arguments @(
    "phase2\identite\registre_contacts.py"
) -WorkerKey "phase2.registre_contacts"

Invoke-Step -Label "phase2 quality checks" -Arguments @(
    "phase2\checks\run_quality_checks.py"
) -WorkerKey "phase2.quality_checks"

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
    # 2026-08-19 : etape rendue NON BLOQUANTE (meme patron que Matterport plus bas).
    # POURQUOI. Le 19/08, ce scrape a echoue apres la panne de l'API Hektor de 03h00 --
    # sa session Playwright etait morte. Comme il etait appele par Invoke-Step (bloquant),
    # son `throw` a tue le run a l'etape 13 sur 23 : le ledger d'affaires, LES TROIS
    # PUBLICATIONS VERS SUPABASE, Matterport, les liens RDV et l'export vitrine n'ont
    # jamais tourne. L'app est restee sur les donnees de la veille, et il a fallu
    # rattraper la publication a la main.
    # Le chauffage est une etape de CONFORT : 50 fiches par nuit, avec un rattrapage
    # automatique a 30 jours. Elle ne doit pas pouvoir bloquer la publication -- exactement
    # le raisonnement deja applique a Matterport (cf. plus bas).
    # -> 2 essais, non bloquant : sur echec final, une ligne WARN dans le log et le run
    # se poursuit. Le rattrapage a 30 jours reprendra les fiches manquees.
    # PAS de -WorkerKey : aucune cle chauffage n'existe dans app_worker_registry, et un
    # heartbeat sur une cle absente ecrit dans le vide (PATCH ...?worker_key=eq.X renvoie
    # 2xx avec 0 ligne modifiee). A ajouter au registre pour rendre l'echec visible dans
    # l'ecran Sante.
    $chauffageOk = $false
    Invoke-OptionalStepWithRetry -Label "hektor chauffage delta" -Arguments $hektorChauffageArgs `
        -MaxAttempts 2 -RetryDelaySeconds 60 -Succeeded ([ref]$chauffageOk)
    if (-not $chauffageOk) {
        Write-RunLog "WARN  hektor chauffage delta non execute cette nuit (echec non bloquant) - pipeline poursuivi ; rattrapage automatique a 30 jours"
    }
}
else {
    Write-RunLog "SKIP hektor chauffage delta"
}

# Contact champs manquants (naissance/lieu/matrimonial) : Hektor ne les rend pas par l'API.
# Scraper Console leger, cache local resumable, recents d'abord. Limite a un seul lot (50)
# comme le chauffage ; les gros rattrapages passent par la commande dediee en vagues.
if (-not $SkipContactMissing -and $ContactMissingLimit -gt 0) {
    if ($ContactMissingLimit -gt 50) {
        throw "Safety stop: le quotidien contact champs-manquants est limite a 50 (rattrapage via la commande dediee en vagues)."
    }
    $contactMissingArgs = @(
        "phase2\sync\sync_console_contact_missing.py",
        "--scope", "eligible",
        "--limit", [string]$ContactMissingLimit,
        "--stale-days", [string]$ContactMissingStaleDays,
        "--batch-size", [string]$ContactMissingLimit,
        "--batch-pause-seconds", "0",
        "--delay-seconds", "0.4"
    )
    if ($ContactMissingRefreshSession) {
        $contactMissingArgs += "--refresh-session-on-expired"
    }
    Invoke-Step -Label "contact champs manquants (naissance/lieu/matrimonial) delta" -Arguments $contactMissingArgs
}
else {
    Write-RunLog "SKIP contact champs manquants delta"
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

# Niveau B/B+ : ledger d'affaires app-owned (offre/compromis/vente). UPSERT sur l'id stable
# (changements d'etat refletes) mais JAMAIS supprime : si Hektor retire une affaire on la conserve
# (present_in_hektor=false). AVANT le push registre : le registre lit les affaires disparues depuis
# ce ledger (filet B+), il faut donc que present_in_hektor soit a jour au moment du build. Lit le
# miroir Hektor rafraichi par normalize_source ci-dessus, pousse vers Supabase.
Invoke-Step -Label "phase2 affaire ledger refresh+push" -Arguments @(
    "phase2\sync\affaire_ledger.py",
    "--refresh",
    "--push"
) -WorkerKey "supabase.affaire_ledger"

Invoke-Step -Label "phase2 push upgrade to supabase" -Arguments $supabaseArgs -WorkerKey "supabase.push_upgrade"

Invoke-Step -Label "phase2 push hektor directory to supabase" -Arguments @(
    "phase2\sync\push_hektor_directory_to_supabase.py"
) -WorkerKey "supabase.push_hektor_directory"

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
    Invoke-Step -Label "phase2 push contacts to supabase" -Arguments $contactsPushArgs -WorkerKey "supabase.push_contacts"

    # C.2b 25/08 -- Supabase RECOIT la serie, il ne la fabrique jamais (regle du 19/08,
    # etablie apres la divergence des numeros d'annonce). Apres le push contacts, donc :
    # les fiches neuves sont arrivees, on peut leur poser leur numero.
    Invoke-Step -Label "phase2 pousser numeros de contact" -Arguments @(
        "phase2\identite\pousser_numeros_contact.py"
    ) -WorkerKey "supabase.push_contact_ids"
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

# Matterport = etape non critique (SaaS externe). Un plantage cote Matterport (ex. 500
# GraphQL transitoire) ne doit PAS tuer le pipeline ni bloquer le heartbeat pipeline.full.
# -> 2 essais, non bloquant (pas de -FailOnError) : sur echec final, ecrit un heartbeat
# error sur matterport.sync_models (criticality medium -> warning visible dans l'ecran
# Sante, sans email/WhatsApp) + une ligne WARN dans le log. Le run global se poursuit.
$matterportOk = $false
Invoke-OptionalStepWithRetry -Label "phase2 sync Matterport links to supabase" -Arguments @(
    "phase2\sync\sync_matterport_models.py",
    "--max-models", "0",
    "--supabase-upsert",
    "--supabase-push-mode", $MatterportPushMode
) -MaxAttempts 2 -RetryDelaySeconds 60 -Succeeded ([ref]$matterportOk) -WorkerKey "matterport.sync_models"
if (-not $matterportOk) {
    Write-RunLog "WARN  Matterport non synchronise cette nuit (echec non bloquant) - pipeline poursuivi ; voir heartbeat matterport.sync_models"
}

Invoke-Step -Label "backfill appointment public links" -Arguments @(
    "backend\scripts\backfill_appointment_public_links.py",
    "--quiet"
) -WorkerKey "appointments.backfill_public_links"

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

Send-Heartbeat -WorkerKey "pipeline.full" -Status "success"
Write-RunLog "Pipeline finished successfully"

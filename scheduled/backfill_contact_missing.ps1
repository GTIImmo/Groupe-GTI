# Rattrapage GLOBAL contact champs-manquants (naissance / lieu / matrimonial).
# Calque sur la NOTE chauffage : vagues de 2000, lots de 100, pauses. RESUMABLE via le
# cache local hektor_contact_missing_detail (les contacts deja done/inchanges sont sautes),
# RECENTS d'abord (ORDER BY date_maj DESC). A lancer UNE fois ; peut etre coupe/relance.
# Lecture seule cote Hektor ; ecrit Supabase avec dirty-skip.
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = "$root\.venv\Scripts\python.exe"
$logDir = "$root\logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "backfill_contact_missing_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
Set-Location $root
try {
    for ($i = 1; $i -le 40; $i++) {
        Write-Output "=== Vague $i/40 demarree $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
        & $py -m phase2.sync.sync_console_contact_missing `
            --scope eligible --limit 2000 --batch-size 100 `
            --batch-pause-seconds 20 --delay-seconds 0.4 --stale-days 0 `
            --refresh-session-on-expired
        $code = $LASTEXITCODE
        Write-Output "=== Vague $i terminee (exit $code) ==="
        if ($code -ne 0) { Write-Output "STOP : vague $i en erreur (code $code)"; break }
        Start-Sleep -Seconds 30
    }
    Write-Output "=== Rattrapage contact termine $(Get-Date -Format 'HH:mm:ss') ==="
} finally {
    Stop-Transcript | Out-Null
}

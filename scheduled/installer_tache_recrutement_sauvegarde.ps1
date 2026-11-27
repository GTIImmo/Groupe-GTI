# Enregistre « GTI Recrutement Sauvegarde » : CHAQUE JOUR a 09:30                         24/11/2026
#
# Note : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §14 (R6.8 = R5 bis).
# ═══════════════════════════════════════════════════════════════════════════════
# ⚠⚠ A LANCER DANS UNE POWERSHELL ADMINISTRATEUR (sans elevation, Register-ScheduledTask echoue).
#    C'est Frederic qui la lance : le terminal de Claude n'est pas administrateur, et la garde du chantier
#    lui interdit de toucher une tache planifiee (delegation du 20/11, note §15).
#
# Recopie de scheduled/installer_tache_recrutement.ps1 (24/11), en plus simple : la soeur « GTI Menage
#   Temporaires » est DEJA quotidienne (declencheur journalier, limite 1 h, S4U) -- on recopie TOUS ses
#   reglages, et la seule difference voulue est l'HEURE : 09:30, apres « GTI Descente » (07:45) et
#   « GTI Sauvegarde » (08:00), et une demi-heure avant le run de deux mois (le dimanche a 10:00).
#
# CE QU'ELLE LANCE : scheduled/run_recrutement_sauvegarde.ps1 (voir son en-tete). Elle ne fait RIEN tant que
#   l'interrupteur RECRUTEMENT_SAUVEGARDE_QUOTIDIENNE n'est pas a 1, ni pendant que le run de deux mois tourne.
#
# DECLAREE AVANT d'etre enregistree dans monitoring/check_gti_health.py (« warning », 24/11).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_recrutement_sauvegarde.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_recrutement_sauvegarde.ps1 -Essai
#       (-Essai : relit la soeur et dit ce qui serait enregistre, n'enregistre RIEN, pas besoin d'etre administrateur)

param(
    [switch]$Essai
)

$ErrorActionPreference = "Stop"

$nom    = "GTI Recrutement Sauvegarde"
$soeur  = "GTI Menage Temporaires"
$script = "C:\Hektor\Projet\scheduled\run_recrutement_sauvegarde.ps1"
$heure  = "09:30"

if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }
$ref = Get-ScheduledTask -TaskName $soeur -ErrorAction SilentlyContinue
if (-not $ref) { throw "La tache de reference « $soeur » est introuvable : impossible de recopier ses reglages." }

if ($Essai) {
    Write-Host "ESSAI : rien n'est enregistre."
    Write-Host "  tache      : $nom"
    Write-Host "  script     : $script"
    Write-Host "  heure      : $heure, chaque jour"
    Write-Host "  soeur      : $soeur ($($ref.Principal.LogonType), $($ref.Settings.MultipleInstances), limite $($ref.Settings.ExecutionTimeLimit), declencheur $($ref.Triggers[0].CimClass.CimClassName))"
    if (Get-ScheduledTask -TaskName $nom -ErrorAction SilentlyContinue) { Write-Host "  ⚠ la tache existe deja : elle serait REMPLACEE" }
    exit 0
}

# ── ADMINISTRATEUR ? on le dit AVANT d'echouer a moitie ──────────────────────
$moi = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $moi.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "STOP : ouvrez une PowerShell ADMINISTRATEUR (clic droit > Executer en tant qu'administrateur)."
    exit 1
}

if (Get-ScheduledTask -TaskName $nom -ErrorAction SilentlyContinue) {
    Write-Host "La tache « $nom » existe deja -- elle va etre REMPLACEE (meme script, reglages reappliques)."
}

$action    = New-ScheduledTaskAction -Execute "powershell.exe" `
             -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger   = New-ScheduledTaskTrigger -Daily -At $heure
$principal = New-ScheduledTaskPrincipal -UserId $ref.Principal.UserId -LogonType S4U -RunLevel Limited
$settings  = New-ScheduledTaskSettingsSet -Compatibility Win7 `
             -MultipleInstances IgnoreNew `
             -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
             -DontStopOnIdleEnd
$settings.UseUnifiedSchedulingEngine = $true
$settings.StartWhenAvailable = $false
Register-ScheduledTask -TaskName $nom -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "`nEnregistree. On VERIFIE maintenant, reglage par reglage, contre « $soeur ».`n"

# ═══════════════════════════════════════════════════════════════════════════════
# LA VERIFICATION -- UNE LIGNE PAR REGLAGE, NOMMEE (« un controle qui agrege perd ce qui sert a agir »)
# ═══════════════════════════════════════════════════════════════════════════════
$t = Get-ScheduledTask -TaskName $nom
$rouges = @()
function Comparer {
    param([string]$Quoi, $Mien, $Attendu)
    if ([string]$Mien -eq [string]$Attendu) { Write-Host ("  OK   {0,-26} {1}" -f $Quoi, $Mien) }
    else {
        Write-Host ("  ROUGE {0,-26} {1}   (attendu : {2})" -f $Quoi, $Mien, $Attendu)
        $script:rouges += $Quoi
    }
}
Comparer "UserId"             $t.Principal.UserId                      $ref.Principal.UserId
Comparer "LogonType"          $t.Principal.LogonType                   $ref.Principal.LogonType
Comparer "RunLevel"           $t.Principal.RunLevel                    $ref.Principal.RunLevel
Comparer "Compatibility"      $t.Settings.Compatibility                $ref.Settings.Compatibility
Comparer "UseUnifiedEngine"   $t.Settings.UseUnifiedSchedulingEngine   $ref.Settings.UseUnifiedSchedulingEngine
Comparer "MultipleInstances"  $t.Settings.MultipleInstances            $ref.Settings.MultipleInstances
Comparer "StartWhenAvailable" $t.Settings.StartWhenAvailable           $ref.Settings.StartWhenAvailable
Comparer "limite d'execution" $t.Settings.ExecutionTimeLimit           $ref.Settings.ExecutionTimeLimit
Comparer "type de declencheur" $t.Triggers[0].CimClass.CimClassName    $ref.Triggers[0].CimClass.CimClassName
Comparer "un seul declencheur" $t.Triggers.Count                       1
Comparer "etat"               $t.State                                 "Ready"
# ⚠ VOLONTAIREMENT DIFFERENTE DE LA SOEUR : verifiee contre la valeur VOULUE.
Comparer "heure de depart"    (([datetime]$t.Triggers[0].StartBoundary).ToString("HH:mm")) $heure
# ET LE SCRIPT APPELE : une tache qui pointe le mauvais fichier est verte et inutile.
Comparer "script appele"      ($t.Actions[0].Arguments -like "*\scheduled\run_recrutement_sauvegarde.ps1*") $true

$prochaine = (Get-ScheduledTaskInfo -TaskName $nom).NextRunTime
Write-Host ""
Write-Host "Prochain passage : $prochaine"
if ($rouges.Count -gt 0) {
    Write-Host "⛔ $($rouges.Count) reglage(s) ROUGE(S) : $($rouges -join ', ')"
    exit 1
}
Write-Host "✅ TOUT VERT -- reglages identiques a « $soeur » (sauf l'heure, differente EXPRES)."
Write-Host "Elle ne fait rien tant que RECRUTEMENT_SAUVEGARDE_QUOTIDIENNE=0 (recrutement_donnees\interrupteurs.env)."
Write-Host "Pour la desactiver :   Disable-ScheduledTask -TaskName `"$nom`""
exit 0

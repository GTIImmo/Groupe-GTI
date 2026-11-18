# Enregistre « GTI Menage Temporaires » a 13:00                           18/11/2026
# ═══════════════════════════════════════════════════════════════════════════════
# ⚠⚠ A LANCER DANS UNE POWERSHELL ADMINISTRATEUR (sans elevation,
#    Register-ScheduledTask echoue).
#
# Recopie de scheduled/installer_tache_balayage_photos.ps1 (19/10) : les REGLAGES
#   vivent dans le depot, et le script RELIT la tache enregistree pour la comparer
#   REGLAGE PAR REGLAGE a une soeur qui marche (« GTI Entretien Documents »).
#   SEULE DIFFERENCE VOULUE : la limite d'execution est PT1H -- le menage lit le
#   coffre et supprime quelques fichiers en moins d'une minute.
#
# CE QU'ELLE LANCE : scheduled/run_menage_temporaires.ps1, qui appelle
#   Console/nettoyer_temporaires_orphelins.js --supprimer (les quatre gardes du
#   script decident fichier par fichier ; la liste datee est ecrite AVANT).
#
# DECLAREE AVANT d'etre enregistree dans monitoring/check_gti_health.py
#   (« warning » : une journee ratee se rattrape le lendemain).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_menage_temporaires.ps1

$ErrorActionPreference = "Stop"

$nom     = "GTI Menage Temporaires"
$soeur   = "GTI Entretien Documents"
$script  = "C:\Hektor\Projet\scheduled\run_menage_temporaires.ps1"

if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

# ── ADMINISTRATEUR ? on le dit AVANT d'echouer a moitie ──────────────────────
$moi = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $moi.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "STOP : ouvrez une PowerShell ADMINISTRATEUR (clic droit > Executer en tant qu'administrateur)."
    exit 1
}

# ── LA SOEUR DOIT EXISTER : c'est elle qui donne les reglages ────────────────
$ref = Get-ScheduledTask -TaskName $soeur -ErrorAction SilentlyContinue
if (-not $ref) { throw "La tache de reference « $soeur » est introuvable : impossible de recopier ses reglages." }

if (Get-ScheduledTask -TaskName $nom -ErrorAction SilentlyContinue) {
    Write-Host "La tache « $nom » existe deja -- elle va etre REMPLACEE (meme script, reglages reappliques)."
}

$action    = New-ScheduledTaskAction -Execute "powershell.exe" `
             -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger   = New-ScheduledTaskTrigger -Daily -At "13:00"
$principal = New-ScheduledTaskPrincipal -UserId $ref.Principal.UserId `
             -LogonType S4U -RunLevel Limited
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
# LA VERIFICATION -- UNE LIGNE PAR REGLAGE, NOMMEE
# ⚠ « un controle qui AGREGE perd ce qui sert a agir » : on n'ecrit pas
#   « 9 sur 9 », on ecrit chaque reglage avec sa valeur des DEUX cotes.
# ═══════════════════════════════════════════════════════════════════════════════
$t = Get-ScheduledTask -TaskName $nom
$rouges = @()

function Comparer {
    param([string]$Quoi, $Mien, $Attendu)
    $ok = ([string]$Mien -eq [string]$Attendu)
    if ($ok) { Write-Host ("  OK   {0,-26} {1}" -f $Quoi, $Mien) }
    else {
        Write-Host ("  ROUGE {0,-26} {1}   (attendu : {2})" -f $Quoi, $Mien, $Attendu)
        $script:rouges += $Quoi
    }
}

Comparer "UserId"            $t.Principal.UserId                      $ref.Principal.UserId
Comparer "LogonType"         $t.Principal.LogonType                   $ref.Principal.LogonType
Comparer "RunLevel"          $t.Principal.RunLevel                    $ref.Principal.RunLevel
Comparer "Compatibility"     $t.Settings.Compatibility                $ref.Settings.Compatibility
Comparer "UseUnifiedEngine"  $t.Settings.UseUnifiedSchedulingEngine   $ref.Settings.UseUnifiedSchedulingEngine
Comparer "MultipleInstances" $t.Settings.MultipleInstances            $ref.Settings.MultipleInstances
Comparer "StartWhenAvailable" $t.Settings.StartWhenAvailable          $ref.Settings.StartWhenAvailable
Comparer "classe declencheur" ($t.Triggers[0].CimClass.CimClassName)  "MSFT_TaskDailyTrigger"
Comparer "intervalle (jours)" ($t.Triggers[0].DaysInterval)           1
Comparer "etat"              $t.State                                 "Ready"

# ⚠ CELLE-CI EST VOLONTAIREMENT DIFFERENTE DE LA SOEUR : on la verifie contre la
#   valeur VOULUE, pas contre la sienne. Une divergence assumee se VERIFIE aussi.
Comparer "limite d'execution" $t.Settings.ExecutionTimeLimit          "PT1H"

# L'heure, lue sur le declencheur reellement enregistre.
$heure = ([datetime]$t.Triggers[0].StartBoundary).ToString("HH:mm")
Comparer "heure de depart"   $heure                                   "13:00"

# ET LE SCRIPT APPELE : une tache qui pointe le mauvais fichier est verte et inutile.
$arg = $t.Actions[0].Arguments
Comparer "script appele" ($arg -like "*run_menage_temporaires.ps1*") $true

Write-Host ""
if ($rouges.Count -gt 0) {
    Write-Host "⛔ $($rouges.Count) reglage(s) ROUGE(S) : $($rouges -join ', ')"
    Write-Host "   NE PAS laisser la tache ainsi -- corriger avant la premiere nuit."
    exit 1
}
Write-Host "✅ TOUT VERT -- 13 reglages identiques a « $soeur » (sauf la limite, differente EXPRES)."
Write-Host ""
Write-Host "⛔ ELLE TOURNERA A 13:00. Pour la desactiver en attendant :"
Write-Host "      Disable-ScheduledTask -TaskName `"$nom`""
Write-Host "   Pour un essai a blanc tout de suite, sans rien poser :"
Write-Host "      .\scheduled\run_menage_temporaires.ps1 -DryRun"
exit 0

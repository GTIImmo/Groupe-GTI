# Enregistre « GTI Balayage Photos Masquees » a 00:00                   19/10/2026
# ═══════════════════════════════════════════════════════════════════════════════
# ⚠⚠ A LANCER DANS UNE POWERSHELL ADMINISTRATEUR. Sans elevation,
#    Register-ScheduledTask echoue (et le projet s'est fait prendre : la tache du
#    15/10 avait fini en « Interactive », SEULE DES NEUF).
#
# ⭐⭐ POURQUOI UN SCRIPT ET PAS UNE COMMANDE COLLEE DANS UNE CONVERSATION :
#   parce que les REGLAGES doivent vivre dans le depot, pas dans un message qui
#   defile. Et parce que ce script porte sa propre VERIFICATION : il relit la
#   tache enregistree et la compare REGLAGE PAR REGLAGE a une soeur qui marche.
#   C'est la lecon du 15/10 transformee en code -- « une tache neuve se compare
#   reglage par reglage a une tache qui marche ; "enregistree" ne veut pas dire
#   "configuree comme ses soeurs" ». Les deux defauts de cette nuit-la (principal
#   Interactive, limite a 72 h) seraient sortis en ROUGE ici.
#
# LES REGLAGES SONT RECOPIES DE « GTI Entretien Documents » (releve du 19/10) :
#     UserId admin · LogonType S4U · RunLevel Limited · Compatibility Win7
#     UseUnifiedSchedulingEngine True · MultipleInstances IgnoreNew
#     StartWhenAvailable False · declencheur MSFT_TaskDailyTrigger, interval 1
#   SEULE DIFFERENCE VOULUE : la limite d'execution est PT1H et non PT4H --
#   l'empileur ne parle pas a Hektor, il pose des travaux et sort en moins d'une
#   minute. Une heure est deja dix fois le besoin.
#
# POURQUOI 00:00 : « GTI Entretien Documents » part a 22:00 et finit 23:17 a
#   23:25 (trois nuits mesurees) ; « GTI Recherches Actives » part a 03:00. Le
#   creux va de ~23:18 a 03:00 ; 00:00 garde 40 min de marge apres l'entretien.
#
# ⭐ LE PLAFOND RESTE AU DEFAUT DU SCRIPT (1 000 annonces) et c'est VOLONTAIRE :
#   1 000 est la valeur mesuree qui tient A LA FOIS le temps (medianne 10 s par
#   travail -> ~2 h 45) et le quota (2 000 requetes + les ~4 500 de la nuit =
#   ~6 500, sous la cible du 20/08). ⚠ Et le CALIBRAGE EST AUTOMATIQUE : si le
#   worker ne digere pas son lot, la nuit suivante le refus « file non vide »
#   sort en 1 et le DIT. Pas besoin de rampe a la main.
#   (⚠ J'avais ecrit « 1 200 les 2 premieres nuits puis 1 000 » -- c'etait a
#    l'envers : un calibrage part en DESSOUS de la cible, pas au-dessus.)
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_balayage_photos.ps1

$ErrorActionPreference = "Stop"

$nom     = "GTI Balayage Photos Masquees"
$soeur   = "GTI Entretien Documents"
$script  = "C:\Hektor\Projet\scheduled\run_balayage_photos_masquees.ps1"

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
$trigger   = New-ScheduledTaskTrigger -Daily -At "00:00"
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
Comparer "heure de depart"   $heure                                   "00:00"

# ET LE SCRIPT APPELE : une tache qui pointe le mauvais fichier est verte et inutile.
$arg = $t.Actions[0].Arguments
Comparer "script appele" ($arg -like "*run_balayage_photos_masquees.ps1*") $true

Write-Host ""
if ($rouges.Count -gt 0) {
    Write-Host "⛔ $($rouges.Count) reglage(s) ROUGE(S) : $($rouges -join ', ')"
    Write-Host "   NE PAS laisser la tache ainsi -- corriger avant la premiere nuit."
    exit 1
}
Write-Host "✅ TOUT VERT -- 13 reglages identiques a « $soeur » (sauf la limite, differente EXPRES)."
Write-Host ""
Write-Host "⛔ ELLE TOURNERA A 00:00 CETTE NUIT. Pour la desactiver en attendant :"
Write-Host "      Disable-ScheduledTask -TaskName `"$nom`""
Write-Host "   Pour un essai a blanc tout de suite, sans rien poser :"
Write-Host "      .\scheduled\run_balayage_photos_masquees.ps1 -DryRun -IgnorerFenetre"
exit 0

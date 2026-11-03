# Bascule « GTI Recherches Actives » sur la nuit des contacts           03/11/2026
# ===============================================================================
# Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md sections 44 a 48.
#
# CE QUI CHANGE SUR LA TACHE -- trois reglages, rien d'autre (meme nom, meme compte,
#   memes reglages de fond ; le moniteur la surveille deja sous ce nom) :
#     action    run_recherches_actives.ps1  ->  run_nuit_contacts_et_recherches.ps1
#               (qui lance la liste, les fiches, PUIS run_recherches_actives.ps1
#               inchange, jamais avant 02:00)
#     depart    02:00+01:00  ->  00:20+01:00
#     limite    PT2H         ->  PT4H  (coupe a 04:20 au lieu de 04:00 : la liste et
#               les fiches ont 1 h 40 devant les recherches, qui gardent leurs 2 h)
#
# PAR DEFAUT IL NE FAIT RIEN : il montre l'avant et l'apres.
#     -Appliquer   fait la bascule, puis relit la tache et VERIFIE chaque reglage
#     -Retour      remet exactement l'ancienne action, 02:00 et PT2H
# A LANCER DANS UNE POWERSHELL ADMINISTRATEUR (Set-ScheduledTask l'exige).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_nuit_contacts.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_nuit_contacts.ps1 -Appliquer

param(
    [switch]$Appliquer,
    [switch]$Retour
)

$ErrorActionPreference = "Stop"
$nom = "GTI Recherches Actives"
$ancienScript = "C:\Hektor\Projet\scheduled\run_recherches_actives.ps1"
$nouveauScript = "C:\Hektor\Projet\scheduled\run_nuit_contacts_et_recherches.ps1"
$psExe = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

if ($Appliquer -and $Retour) { Write-Host "STOP : -Appliquer OU -Retour, pas les deux."; exit 2 }

if ($Retour) { $script = $ancienScript; $heure = "02:00:00"; $limite = "PT2H" }
else         { $script = $nouveauScript; $heure = "00:20:00"; $limite = "PT4H" }
if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

$t = Get-ScheduledTask -TaskName $nom
$bornesAvant = $t.Triggers[0].StartBoundary
# On garde la date et le fuseau ecrits (« 2026-06-20T02:00:00+01:00 ») : seule l'heure change.
if ($bornesAvant -notmatch '^(\d{4}-\d{2}-\d{2}T)\d{2}:\d{2}:\d{2}(.*)$') { throw "Declencheur illisible : $bornesAvant" }
$bornesApres = $Matches[1] + $heure + $Matches[2]
$argApres = "-NoProfile -ExecutionPolicy Bypass -File `"$script`""

Write-Host "Tache : $nom   (etat $($t.State))"
Write-Host ("  action   {0}`n        -> {1}" -f $t.Actions[0].Arguments, $argApres)
Write-Host ("  depart   {0}  ->  {1}" -f $bornesAvant, $bornesApres)
Write-Host ("  limite   {0}  ->  {1}" -f $t.Settings.ExecutionTimeLimit, $limite)

if (-not ($Appliquer -or $Retour)) {
    Write-Host "`n(a blanc : rien n'est change ; -Appliquer pour basculer, -Retour pour revenir)"
    exit 0
}

$moi = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $moi.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "STOP : ouvrez une PowerShell ADMINISTRATEUR."
    exit 1
}
if ($t.State -eq "Running") { Write-Host "STOP : la tache tourne en ce moment. Reessayer apres sa fin."; exit 1 }

$t.Actions[0].Execute = $psExe
$t.Actions[0].Arguments = $argApres
$t.Triggers[0].StartBoundary = $bornesApres
$t.Settings.ExecutionTimeLimit = $limite
Set-ScheduledTask -InputObject $t | Out-Null

# LA VERIFICATION, sur la tache RELUE -- une ligne par reglage, nommee.
$v = Get-ScheduledTask -TaskName $nom
$rouges = @()
function Comparer {
    param([string]$Quoi, $Mien, $Attendu)
    if ([string]$Mien -eq [string]$Attendu) { Write-Host ("  OK    {0,-18} {1}" -f $Quoi, $Mien) }
    else { Write-Host ("  ROUGE {0,-18} {1}   (attendu : {2})" -f $Quoi, $Mien, $Attendu); $script:rouges += $Quoi }
}
Comparer "action"   $v.Actions[0].Arguments           $argApres
Comparer "depart"   $v.Triggers[0].StartBoundary      $bornesApres
Comparer "limite"   $v.Settings.ExecutionTimeLimit    $limite
Comparer "compte"   $v.Principal.UserId               $t.Principal.UserId
Comparer "etat"     $v.State                          "Ready"
if ($rouges.Count -gt 0) { Write-Host "ROUGE : $($rouges -join ', ') -- corriger avant la nuit."; exit 1 }
Write-Host "TOUT VERT."
exit 0

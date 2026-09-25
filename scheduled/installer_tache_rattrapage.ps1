# Cree la tache planifiee « GTI Rattrapage Documents » (23:00).
#                                                                        25/09/2026
# A LANCER UNE SEULE FOIS, dans un PowerShell ADMINISTRATEUR :
#   Register-ScheduledTask exige l'elevation -- une session normale recoit « Acces refuse ».
#
# Calque sur les taches existantes : compte admin, ouverture de session S4U (tourne sans
# session ouverte), niveau limite. La tache ne fait que POSER un lot de travaux ; c'est le
# worker documents, lui en LocalSystem, qui parle ensuite a Hektor.
#
# Pour l'enlever :  Unregister-ScheduledTask -TaskName "GTI Rattrapage Documents" -Confirm:$false

$ErrorActionPreference = "Stop"
$nom = "GTI Rattrapage Documents"
$script = "C:\Hektor\Projet\scheduled\run_rattrapage_documents.ps1"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
      ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ARRET : cette fenetre n'est PAS administrateur." -ForegroundColor Red
    Write-Host "Menu Demarrer -> taper 'powershell' -> clic droit -> Executer en tant qu'administrateur."
    exit 1
}
if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

if (Get-ScheduledTask -TaskName $nom -ErrorAction SilentlyContinue) {
    Write-Host "La tache existe deja : on la remplace." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $nom -Confirm:$false
}

$action = New-ScheduledTaskAction `
    -Execute "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At 23:00
$principal = New-ScheduledTaskPrincipal -UserId "admin" -LogonType S4U -RunLevel Limited
# 1 h suffit largement : la tache ne fait que poser le lot (moins d'une minute).
# IgnoreNew : si par accident elle se declenchait deux fois, la seconde ne demarre pas.
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew
$desc = "Rattrapage documents : pose un lot de 3000 annonces par nuit (archive -> historique " +
        "-> brouillon). Ne parle pas a Hektor : le worker documents travaille ensuite a sa " +
        "cadence. S'arrete seule si la file n'est pas vide ou si 20 erreurs en 24 h. " +
        "~15 nuits a partir du 25/09/2026."

Register-ScheduledTask -TaskName $nom -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Description $desc | Out-Null

$t = Get-ScheduledTask -TaskName $nom
Write-Host ""
Write-Host "TACHE CREEE" -ForegroundColor Green
Write-Host ("  nom         : " + $t.TaskName)
Write-Host ("  etat        : " + $t.State)
Write-Host ("  declencheur : " + ($t.Triggers[0].StartBoundary))
Write-Host ("  prochaine   : " + (Get-ScheduledTaskInfo -TaskName $nom).NextRunTime)
Write-Host ("  compte      : " + $t.Principal.UserId + " / " + $t.Principal.LogonType)
Write-Host ""
Write-Host "Suivre l'avancement a tout moment :"
Write-Host "  node C:\Hektor\Projet\Console\enqueue_empreinte_lot.js --scope auto --dry-run"

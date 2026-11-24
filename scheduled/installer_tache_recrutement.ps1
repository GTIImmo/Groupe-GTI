# Enregistre « GTI Recrutement » : le 1er dimanche, TOUS LES DEUX MOIS, a 10:00   20/11 -> 24/11/2026
#
# ⭐ 24/11/2026 -- DECISION DE FREDERIC : « peut-on le passer a tous les 2 mois ». La tache s'appelait
#   « GTI Recrutement Mensuel » (enregistree le 24/11 au matin) : elle est RENOMMEE « GTI Recrutement »
#   (plus de frequence dans le nom, il ne mentira plus si on la rechange) et ce script RETIRE
#   l'ancienne. Les mois : decembre, fevrier, avril, juin, aout, octobre -- le 1er passage reste le 06/12.
# ═══════════════════════════════════════════════════════════════════════════════
# ⚠⚠ A LANCER DANS UNE POWERSHELL ADMINISTRATEUR (sans elevation, Register-ScheduledTask
#    echoue). C'est Frederic qui la lance : le terminal de Claude n'est pas administrateur, et la
#    garde du chantier lui interdit de toucher une tache planifiee (delegation du 20/11, note §15).
#
# Recopie de scheduled/installer_tache_menage_temporaires.ps1 (18/11) : les REGLAGES vivent dans
#   le depot, et le script RELIT la tache enregistree pour la comparer REGLAGE PAR REGLAGE a une
#   soeur qui marche (« GTI Menage Temporaires »).
#   DEUX DIFFERENCES VOULUES, verifiees contre la valeur VOULUE (pas contre la soeur) :
#     - le declencheur : CALENDRIER, le 1er dimanche des mois pairs de l'annee scolaire (decembre,
#       fevrier, avril, juin, aout, octobre) a 10:00 (heure locale).
#       PowerShell ne sait pas creer un declencheur mensuel : on enregistre d'abord la tache comme
#       la soeur, puis on remplace son declencheur dans le XML (meme forme que la seule tache
#       calendrier du serveur, « Hektor-IngestSemestriel », relue le 20/11) ;
#     - la limite d'execution : PT8H (la 1re collecte complete : 2 a 3 heures estimees le 20/11).
#
# CE QU'ELLE LANCE : scheduled/run_recrutement.ps1 (8 etapes ; voir son en-tete).
#
# DECLAREE AVANT d'etre enregistree dans monitoring/check_gti_health.py (« warning », 20/11 ; le nom
#   « GTI Recrutement » et le seuil de 64 jours le 24/11).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_recrutement.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\installer_tache_recrutement.ps1 -Essai
#       (-Essai : fabrique et affiche le declencheur, n'enregistre RIEN, pas besoin d'etre administrateur)

param(
    [switch]$Essai
)

$ErrorActionPreference = "Stop"

$nom       = "GTI Recrutement"
$ancienNom = "GTI Recrutement Mensuel"   # le nom du 24/11 au matin : retire par ce script
$soeur     = "GTI Menage Temporaires"
$script    = "C:\Hektor\Projet\scheduled\run_recrutement.ps1"
$heure     = "10:00"
$limite    = "PT8H"
# Les mois, DANS L'ORDRE DU CALENDRIER (le schema du Planificateur l'exige) : tous les deux mois.
$MOIS      = @("February", "April", "June", "August", "October", "December")

if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

# Le declencheur, au format du Planificateur (1re semaine, dimanche, les mois de $MOIS).
function New-DeclencheurMensuel {
    $aujourdhui = Get-Date
    $premier = Get-Date -Year $aujourdhui.Year -Month $aujourdhui.Month -Day 1
    $debut = $premier.AddMonths(1).ToString("yyyy-MM-01") + "T" + $heure + ":00"
    $mois = ($MOIS | ForEach-Object { "<$_ />" }) -join ""
    return "<Triggers><CalendarTrigger><StartBoundary>$debut</StartBoundary><Enabled>true</Enabled>" +
           "<ScheduleByMonthDayOfWeek><Weeks><Week>1</Week></Weeks><DaysOfWeek><Sunday /></DaysOfWeek>" +
           "<Months>$mois</Months></ScheduleByMonthDayOfWeek></CalendarTrigger></Triggers>"
}

if ($Essai) {
    Write-Host "ESSAI : rien n'est enregistre."
    Write-Host "Declencheur fabrique :"
    Write-Host (New-DeclencheurMensuel)
    $ref = Get-ScheduledTask -TaskName $soeur -ErrorAction SilentlyContinue
    if ($ref) { Write-Host "Soeur trouvee : $soeur ($($ref.Principal.LogonType), $($ref.Settings.MultipleInstances))" }
    else { Write-Host "⚠ soeur introuvable : $soeur" }
    $xml = [xml](Export-ScheduledTask -TaskName $soeur)
    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace("t", "http://schemas.microsoft.com/windows/2004/02/mit/task")
    $ancien = $xml.SelectSingleNode("//t:Triggers", $ns)
    $neuf = [xml]("<x xmlns='http://schemas.microsoft.com/windows/2004/02/mit/task'>" + (New-DeclencheurMensuel) + "</x>")
    [void]$ancien.ParentNode.ReplaceChild($xml.ImportNode($neuf.DocumentElement.FirstChild, $true), $ancien)
    Write-Host "Le XML transforme se relit : $([bool]$xml.SelectSingleNode('//t:CalendarTrigger/t:ScheduleByMonthDayOfWeek', $ns))"
    exit 0
}

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

# L'ANCIEN NOM (« GTI Recrutement Mensuel », 24/11 au matin) est retire : deux taches lanceraient le
# meme run, et la surveillance ne regarde plus que le nouveau nom.
if (Get-ScheduledTask -TaskName $ancienNom -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $ancienNom -Confirm:$false
    Write-Host "L'ancienne tache « $ancienNom » est RETIREE."
}

# 1. Enregistree comme la soeur (declencheur quotidien provisoire, ACTIVE a la fin seulement)
$action    = New-ScheduledTaskAction -Execute "powershell.exe" `
             -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger   = New-ScheduledTaskTrigger -Daily -At $heure
$principal = New-ScheduledTaskPrincipal -UserId $ref.Principal.UserId -LogonType S4U -RunLevel Limited
$settings  = New-ScheduledTaskSettingsSet -Compatibility Win7 `
             -MultipleInstances IgnoreNew `
             -ExecutionTimeLimit (New-TimeSpan -Hours 8) `
             -DontStopOnIdleEnd
$settings.UseUnifiedSchedulingEngine = $true
$settings.StartWhenAvailable = $false
Register-ScheduledTask -TaskName $nom -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

# 2. Le declencheur remplace par le calendrier mensuel, dans le XML
$xml = [xml](Export-ScheduledTask -TaskName $nom)
$ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
$ns.AddNamespace("t", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$ancien = $xml.SelectSingleNode("//t:Triggers", $ns)
$neuf = [xml]("<x xmlns='http://schemas.microsoft.com/windows/2004/02/mit/task'>" + (New-DeclencheurMensuel) + "</x>")
[void]$ancien.ParentNode.ReplaceChild($xml.ImportNode($neuf.DocumentElement.FirstChild, $true), $ancien)
# (sans -User : le principal S4U voyage dans le XML exporte ; le repasser risquerait de changer son type)
Register-ScheduledTask -TaskName $nom -Xml $xml.OuterXml -Force | Out-Null

Write-Host "`nEnregistree. On VERIFIE maintenant, reglage par reglage, contre « $soeur ».`n"

# ═══════════════════════════════════════════════════════════════════════════════
# LA VERIFICATION -- UNE LIGNE PAR REGLAGE, NOMMEE (« un controle qui agrege perd ce qui sert a agir »)
# ═══════════════════════════════════════════════════════════════════════════════
$t = Get-ScheduledTask -TaskName $nom
$x = [xml](Export-ScheduledTask -TaskName $nom)
$nx = New-Object System.Xml.XmlNamespaceManager($x.NameTable)
$nx.AddNamespace("t", "http://schemas.microsoft.com/windows/2004/02/mit/task")
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

Comparer "UserId"             $t.Principal.UserId                      $ref.Principal.UserId
Comparer "LogonType"          $t.Principal.LogonType                   $ref.Principal.LogonType
Comparer "RunLevel"           $t.Principal.RunLevel                    $ref.Principal.RunLevel
Comparer "Compatibility"      $t.Settings.Compatibility                $ref.Settings.Compatibility
Comparer "UseUnifiedEngine"   $t.Settings.UseUnifiedSchedulingEngine   $ref.Settings.UseUnifiedSchedulingEngine
Comparer "MultipleInstances"  $t.Settings.MultipleInstances            $ref.Settings.MultipleInstances
Comparer "StartWhenAvailable" $t.Settings.StartWhenAvailable           $ref.Settings.StartWhenAvailable
Comparer "etat"               $t.State                                 "Ready"

# ⚠ VOLONTAIREMENT DIFFERENTS DE LA SOEUR : verifies contre la valeur VOULUE.
Comparer "limite d'execution" $t.Settings.ExecutionTimeLimit           $limite
Comparer "declencheur"        ([bool]$x.SelectSingleNode("//t:CalendarTrigger/t:ScheduleByMonthDayOfWeek", $nx)) $true
Comparer "semaine du mois"    ($x.SelectSingleNode("//t:ScheduleByMonthDayOfWeek/t:Weeks/t:Week", $nx).InnerText) "1"
Comparer "jour"               ($x.SelectSingleNode("//t:ScheduleByMonthDayOfWeek/t:DaysOfWeek", $nx).FirstChild.LocalName) "Sunday"
Comparer "mois (tous les 2)"  (($x.SelectSingleNode("//t:ScheduleByMonthDayOfWeek/t:Months", $nx).ChildNodes | ForEach-Object { $_.LocalName }) -join ",") ($MOIS -join ",")
Comparer "heure de depart"    (([datetime]$x.SelectSingleNode("//t:CalendarTrigger/t:StartBoundary", $nx).InnerText).ToString("HH:mm")) $heure
Comparer "un seul declencheur" ($x.SelectNodes("//t:Triggers/*", $nx).Count) 1

# ET LE SCRIPT APPELE : une tache qui pointe le mauvais fichier est verte et inutile.
Comparer "script appele" ($t.Actions[0].Arguments -like "*\scheduled\run_recrutement.ps1*") $true
# ET L'ANCIEN NOM EST BIEN PARTI : deux taches lanceraient le meme run.
Comparer "ancienne tache retiree" ([bool](Get-ScheduledTask -TaskName $ancienNom -ErrorAction SilentlyContinue)) $false

$prochaine = (Get-ScheduledTaskInfo -TaskName $nom).NextRunTime
Write-Host ""
Write-Host "Prochain passage : $prochaine"
if ($rouges.Count -gt 0) {
    Write-Host "⛔ $($rouges.Count) reglage(s) ROUGE(S) : $($rouges -join ', ')"
    Write-Host "   NE PAS laisser la tache ainsi -- corriger avant le premier dimanche."
    exit 1
}
Write-Host "✅ TOUT VERT -- reglages identiques a « $soeur » (sauf le declencheur et la limite, differents EXPRES)."
Write-Host ""
Write-Host "Pour la desactiver :   Disable-ScheduledTask -TaskName `"$nom`""
Write-Host "Essai a blanc du run : .\scheduled\run_recrutement.ps1 -DryRun"
exit 0

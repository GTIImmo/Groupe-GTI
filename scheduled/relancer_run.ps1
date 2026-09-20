# =============================================================================
#  RELANCER UN RUN PERDU — la seule facon sure                      20/09/2026
# =============================================================================
#  POURQUOI CE SCRIPT EXISTE. Le 17/09, une reprise ecrite a la main a oublie
#  UNE option -- `--include-archived-searches` -- et 7 182 recherches archivees
#  ont ete retirees de Supabase. Le 19/09, le run de 5 h est mort a 05:01 sur un
#  blocage d'IP et il a fallu tout rejouer. A chaque fois, la reprise vivait dans
#  un fichier temporaire qui disparaissait ensuite.
#
#  LA REGLE, APPRISE DEUX FOIS : REJOUER UN RUN, C'EST REJOUER SES OPTIONS.
#  Et la seule facon de ne pas en oublier une n'est pas de les recopier : c'est
#  de NE PAS LES ECRIRE. On demarre la TACHE PLANIFIEE elle-meme, qui porte deja
#  la bonne ligne de commande, le bon compte, le bon environnement et son propre
#  journal date.
#
#  CE QU'IL FAIT
#     .\scheduled\relancer_run.ps1 quotidien     -> GTI Quotidien      (05:00)
#     .\scheduled\relancer_run.ps1 descente      -> GTI Descente       (07:30)
#     .\scheduled\relancer_run.ps1 recherches    -> GTI Recherches Actives (03:00)
#     .\scheduled\relancer_run.ps1 sauvegarde    -> GTI Sauvegarde     (08:15)
#  Sans argument, il AFFICHE l'etat des quatre taches et ne lance rien.
#
#  CE QU'IL VERIFIE AVANT DE LANCER
#     1. Hektor repond (une ouverture de connexion, pas une authentification) --
#        relancer un run pendant un blocage d'IP l'aggrave.
#     2. Aucune des quatre taches ne tourne deja : deux runs en parallele se
#        disputent la base locale (« database is locked », 22/08).
#
#  CE QU'IL NE FAIT PAS : reprendre un run AU MILIEU. Une reprise partielle se
#  decide en lisant le journal, etape par etape, et elle se discute avant.
# =============================================================================
[CmdletBinding()]
param(
    [ValidateSet("quotidien", "descente", "recherches", "sauvegarde")]
    [string]$Run,
    [switch]$Force   # passer outre le controle « Hektor repond »
)

$ErrorActionPreference = "Stop"

$taches = [ordered]@{
    quotidien  = "GTI Quotidien"
    descente   = "GTI Descente"
    recherches = "GTI Recherches Actives"
    sauvegarde = "GTI Sauvegarde"
}

function Afficher-Etat {
    foreach ($cle in $taches.Keys) {
        $nom = $taches[$cle]
        try {
            $t = Get-ScheduledTask -TaskName $nom -ErrorAction Stop
            $i = $t | Get-ScheduledTaskInfo
            $verdict = if ($i.LastTaskResult -eq 0) { "ok" } else { "ECHEC ($($i.LastTaskResult))" }
            "{0,-12} {1,-26} {2,-9} derniere {3}  {4}" -f $cle, $nom, $t.State, $i.LastRunTime, $verdict
        } catch {
            "{0,-12} {1,-26} INTROUVABLE" -f $cle, $nom
        }
    }
}

function Test-HektorRepond {
    # Une seule ouverture de connexion, aucune authentification : la meme mesure
    # que la sonde du moniteur (check_gti_health.check_hektor_joignable).
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $ok = $c.ConnectAsync("groupe-gti-immobilier.la-boite-immo.com", 443).Wait(10000)
        $c.Close()
        return $ok
    } catch { return $false }
}

if (-not $Run) {
    Write-Output "=== ETAT DES TACHES ==="
    Afficher-Etat
    Write-Output ""
    Write-Output "Pour relancer :  .\scheduled\relancer_run.ps1 quotidien"
    exit 0
}

$enCours = @()
foreach ($cle in $taches.Keys) {
    try {
        if ((Get-ScheduledTask -TaskName $taches[$cle] -ErrorAction Stop).State -eq "Running") { $enCours += $taches[$cle] }
    } catch { }
}
if ($enCours.Count -gt 0) {
    Write-Output "REFUS : une tache tourne deja ($($enCours -join ', ')). Deux runs en parallele se disputent la base locale."
    exit 1
}

if (-not $Force -and -not (Test-HektorRepond)) {
    Write-Output "REFUS : Hektor ne repond pas depuis ce serveur. Relancer maintenant aggraverait un eventuel blocage d'IP."
    Write-Output "Verifier depuis une AUTRE connexion, puis relancer -- ou forcer avec -Force si l'on sait ce qu'on fait."
    exit 1
}

$nom = $taches[$Run]
Write-Output "Demarrage de « $nom » a $(Get-Date -Format 'HH:mm:ss')..."
Start-ScheduledTask -TaskName $nom
Start-Sleep -Seconds 5
$etat = (Get-ScheduledTask -TaskName $nom).State
Write-Output "Etat : $etat"
Write-Output "Journal : C:\Hektor\Projet\logs\scheduled\ (le fichier le plus recent)"
Write-Output "⚠ Ne pas lancer une seconde tache tant que celle-ci tourne."

# Tache planifiee « GTI Recrutement » : LE RUN DU RECRUTEMENT, TOUS LES DEUX MOIS   20/11 -> 24/11/2026
#
# Note : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §13 (architecture) et §14
#   (liste des taches). Decision de Frederic du 20/11 : « une collecte mensuelle est suffisante, et
#   une architecture similaire au reste de l'app : tache planifiee Windows, run, mise a jour,
#   monitoring ». Puis le 24/11 : « peut-on le passer a tous les 2 mois » -> le 1er dimanche de
#   decembre, fevrier, avril, juin, aout, octobre a 10:00. Ce script s'appelait
#   run_recrutement_mensuel.ps1 (renomme le 24/11 : plus de frequence dans le nom).
#
# CE QU'IL FAIT, EN 8 ETAPES (chacune a son battement « recrutement.<etape> ») :
#   descente     Supabase -> local : liste « ne plus contacter », effacements, corrections (R4)
#                ⛔ si elle est allumee et echoue, LE RUN S'ARRETE : on ne collecte jamais sans
#                savoir qui ne doit plus revenir
#   collecte     ouvre la collecte du mois, puis lit chaque source (une a la fois). Une source en
#                echec n'arrete pas les autres. Un lecteur coupe a 9 min (code 3) est relance : il
#                reprend ou il en etait. Puis `siren` : placement par le registre + minimisation
#   mise_a_jour  compare a la collecte d'avant : nouveaux, absents, partis, revenus, changes de
#                reseau ; une source MALADE (< 70 %, temoins perdus) ne fait partir personne
#   controle     la regle des coordonnees, l'opposition, les temoins -- ROUGE = rien ne monte
#   export       le CSV du mois (sortie\candidats_region_<date>.csv)
#   montee       local -> Supabase, schema « recrutement » (R4) -- derriere l'interrupteur
#   sauvegarde   copie datee et relue dans C:\Hektor\Backups\recrutement\ (12 gardees)
#   compte_rendu l'etat de chaque source, en COMPTES (jamais un nom)
#
# CE QU'IL NE TOUCHE JAMAIS : Hektor, le worker, le run de nuit, phase2.sqlite, les tables de l'app.
#   Il ne lit que des sites publics (robots.txt respecte, une requete a la fois, arret net sur un
#   refus) et l'API publique du registre.
#
# LES INTERRUPTEURS vivent dans un fichier a lui, PAS dans .env (qui reste intact) :
#   C:\Hektor\recrutement_donnees\interrupteurs.env
#     RECRUTEMENT_DESCENTE=0|1     RECRUTEMENT_MONTEE=0|1     RECRUTEMENT_BATTEMENTS=0|1
#   Tout a 0 tant que le schema « recrutement » n'est pas pose (R3).
#
# LE JOURNAL DE LA TACHE ne porte que des COMPTES et des codes. Le detail (adresses de pages, donc
#   parfois des noms) va dans recrutement_donnees\run_detail_<date>.txt, a cote des donnees, que la
#   purge RGPD atteint.
#
# LES CODES : 0 = tout vert ; 1 = quelque chose a voir (source en echec ou malade, controle rouge,
#   etape tombee). Convention du projet : un 1 se VOIT au Planificateur et a l'ecran Sante.
#
#   .\scheduled\run_recrutement.ps1                                  <- le run complet (comme la tache)
#   .\scheduled\run_recrutement.ps1         -DryRun                  <- collecte et controle, sans montee,
#                                                                       sans sauvegarde, sans battement
#   .\scheduled\run_recrutement.ps1         -StartAtLabel controle   <- reprendre a une etape
#   .\scheduled\run_recrutement.ps1         -Source safti            <- relire UN site (apres reparation
#                                                                       de son lecteur) : ni collecte
#                                                                       ouverte, ni mise a jour

param(
    [switch]$DryRun,
    [string]$StartAtLabel = "",
    [string]$Source = "",
    [int]$MaxRelances = 12
)

$ErrorActionPreference = "Continue"
# la sortie des scripts Python est en UTF-8 : sans cette ligne, PowerShell la lit dans l'ancien encodage de
# la console et « » devient « ┬½ » dans le journal (vu le 24/11)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$root = "C:\Hektor\Projet"
$donnees = if ($env:RECRUTEMENT_DONNEES) { $env:RECRUTEMENT_DONNEES } else { "C:\Hektor\recrutement_donnees" }
$py = Join-Path $root ".venv\Scripts\python.exe"
# La descente et la montee parlent a la base par le ROBOT (psycopg2) : le Python SYSTEME l'a, le .venv non
# (verifie le 24/11). Elles ne lisent jamais le .env du projet, seulement recrutement_donnees\robot.env.
$pyBase = if ($env:RECRUTEMENT_PYTHON_BASE) { $env:RECRUTEMENT_PYTHON_BASE } else { "C:\Python314\python.exe" }
# ⚠⚠ 24/11, TROUVE PAR LES 2 PREMIERS LANCEMENTS DE LA TACHE : le Python systeme N'A PAS psycopg2 ni requests.
#   Ils avaient ete installes « pour l'utilisateur » DEPUIS L'APPLICATION CLAUDE, qui est un paquet Windows
#   (MSIX) : Windows a range ces fichiers dans le dossier PRIVE de l'application
#   (AppData\Local\Packages\Claude_...\LocalCache\Roaming\Python). Un terminal Claude les voit ; la tache, un
#   service ou un PowerShell ordinaire, NON. (La 1re correction, PYTHONUSERBASE, ne pouvait donc rien.)
#   ➡ Le robot a SON dossier de paquets, a un endroit que tout le serveur voit, et le Python systeme est lance
#   avec -s (sans dossier personnel) : un essai depuis Claude se comporte alors EXACTEMENT comme la tache.
$paquetsRobot = if ($env:RECRUTEMENT_PAQUETS_PYTHON) { $env:RECRUTEMENT_PAQUETS_PYTHON } else { Join-Path $donnees "python_paquets" }
$installPaquets = "C:\Python314\python.exe -m pip install --target $paquetsRobot psycopg2-binary==2.9.12 requests==2.34.2 urllib3==2.7.0 idna==3.18 charset_normalizer==3.4.7 certifi==2026.6.17"
# Le Python systeme, avec SEULEMENT le dossier du robot en plus : PYTHONPATH est pose pour cet appel et rendu
# apres, pour ne jamais deborder sur le .venv (la collecte garde ses propres bibliotheques).
#   (fonction SIMPLE, sans param() : « -X » et « -c » passent tels quels dans $args au lieu d'etre pris pour
#   des parametres PowerShell)
function Invoke-PythonRobot {
    $ancien = $env:PYTHONPATH
    $env:PYTHONPATH = $paquetsRobot
    try { & $pyBase -s @args 2>&1 }
    finally { if ($null -eq $ancien) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue } else { $env:PYTHONPATH = $ancien } }
}
$collecteur = Join-Path $root "recrutement\collecte_annuaires.py"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "recrutement_$stamp.log"
$detail = Join-Path $donnees "run_detail_$stamp.txt"
Start-Transcript -Path $log -Append | Out-Null

$ETAPES = @("descente", "collecte", "mise_a_jour", "controle", "export", "montee", "sauvegarde", "compte_rendu")

# Les sources, dans l'ordre : le registre AVANT Maxihome (qui s'y place), `siren` en dernier.
$SOURCES = @(
    @("registre"),
    @("iad", "liste"), @("iad", "fiches"),
    @("safti", "liste"), @("safti", "fiches"),
    @("kw", "liste"), @("kw", "fiches"),
    @("orpi"), @("laforet"), @("c21"), @("42avenue"), @("manufacture"),
    @("capifrance"), @("optimhome"), @("bsk"), @("megagence"), @("expertimo"),
    @("drhouse"), @("3g"), @("lfimmo"), @("sextant"), @("cotepart"), @("exp"),
    @("groupement"), @("immodiffusion"), @("lucarne"), @("liberkeys"), @("maxihome")
)

function Read-Interrupteurs {
    $valeurs = @{ RECRUTEMENT_DESCENTE = "0"; RECRUTEMENT_MONTEE = "0"; RECRUTEMENT_BATTEMENTS = "0" }
    $fichier = Join-Path $donnees "interrupteurs.env"
    if (Test-Path -LiteralPath $fichier) {
        foreach ($ligne in Get-Content -LiteralPath $fichier) {
            if ($ligne -match '^\s*(RECRUTEMENT_[A-Z_]+)\s*=\s*([01])\s*$') { $valeurs[$Matches[1]] = $Matches[2] }
        }
    }
    return $valeurs
}

function Send-Battement {
    param([string]$Etape, [string]$Statut, [string]$Erreur = "")
    if (-not $script:battements) { return }
    $arguments = @((Join-Path $root "monitoring\heartbeat.py"), "--worker", "recrutement.$Etape", "--status", $Statut)
    if ($Erreur) { $arguments += @("--error", $Erreur) }
    & $py @arguments *>> $detail
}

function Invoke-Collecteur {
    param([string[]]$Arguments)
    $env:PYTHONIOENCODING = "utf-8"
    for ($i = 1; $i -le $MaxRelances; $i++) {
        & $py -X utf8 -u $collecteur @Arguments *>> $detail
        $code = $LASTEXITCODE
        if ($code -ne 3) { return $code }
        # ⚠ Write-Host, PAS Write-Output : dans une fonction, Write-Output s'ajouterait a la valeur rendue
        #   et `$code = Invoke-Collecteur ...` recevrait un tableau au lieu d'un nombre.
        Write-Host "    ($($Arguments -join ' ') : coupe a 9 min, relance $i/$MaxRelances)"
    }
    return 3
}

function Test-Etape {
    param([string]$Etape)
    if (-not $StartAtLabel) { return $true }
    return ($ETAPES.IndexOf($Etape) -ge $ETAPES.IndexOf($StartAtLabel))
}

$runFailed = $false
$verrou = Join-Path $donnees "run.lock"
try {
    Write-Output "=== Run du recrutement demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⛔ UN SEUL RUN A LA FOIS (vecu le 20/11 : deux lectures SAFTI en meme temps = double charge sur leur site)
    if (Test-Path -LiteralPath $verrou) {
        $autre = [int](Get-Content -LiteralPath $verrou -TotalCount 1)
        if (Get-Process -Id $autre -ErrorAction SilentlyContinue) {
            throw "un run tourne deja (processus $autre) : on ne lance pas le second"
        }
        Write-Output "    verrou orphelin (processus $autre absent) : retire"
    }
    Set-Content -LiteralPath $verrou -Value $PID -Encoding ascii

    if ($StartAtLabel -and ($ETAPES -notcontains $StartAtLabel)) {
        throw "etape inconnue pour -StartAtLabel : « $StartAtLabel » (connues : $($ETAPES -join ', '))"
    }
    if ($StartAtLabel) { Write-Output "=== REPRISE a partir de « $StartAtLabel » ===" }
    if ($Source -and -not ($SOURCES | Where-Object { $_[0] -eq $Source })) {
        throw "source inconnue pour -Source : « $Source »"
    }

    $inter = Read-Interrupteurs
    $script:battements = ($inter.RECRUTEMENT_BATTEMENTS -eq "1") -and -not $DryRun
    $descente = ($inter.RECRUTEMENT_DESCENTE -eq "1")
    $montee = ($inter.RECRUTEMENT_MONTEE -eq "1") -and -not $DryRun
    Write-Output "    interrupteurs : descente=$($inter.RECRUTEMENT_DESCENTE) montee=$($inter.RECRUTEMENT_MONTEE) battements=$($inter.RECRUTEMENT_BATTEMENTS)$(if ($DryRun) { ' (DryRun : ni montee, ni sauvegarde, ni battement)' })"

    # ── LE CONTROLE DE DEPART : si la descente ou la montee doivent tourner, le Python systeme et ses deux
    #    bibliotheques doivent repondre MAINTENANT -- pas apres des heures de collecte.
    if ($descente -or $montee) {
        if (-not (Test-Path -LiteralPath $pyBase)) { throw "le Python systeme est absent : $pyBase" }
        if (-not (Test-Path -LiteralPath $paquetsRobot)) {
            throw "le dossier des paquets du robot est absent ($paquetsRobot). L'installer UNE fois : $installPaquets"
        }
        $verif = Invoke-PythonRobot -c "import psycopg2, requests; print(psycopg2.__file__)"
        if ($LASTEXITCODE -ne 0) {
            throw "le Python systeme ne trouve pas psycopg2 / requests dans $paquetsRobot : $($verif | Select-Object -Last 1). Reinstaller : $installPaquets"
        }
        Write-Output "    Python systeme : psycopg2 et requests trouves ($($verif | Select-Object -Last 1))"
    }

    # ── ① DESCENTE ────────────────────────────────────────────────────────────────────────────
    if (Test-Etape "descente") {
        if (-not $descente) {
            Write-Output "[descente] eteinte (interrupteur) : la liste « ne plus contacter » locale fait foi"
        } else {
            Send-Battement "descente" "running"
            $script = Join-Path $root "recrutement\descendre.py"
            if (-not (Test-Path -LiteralPath $script)) { throw "descente allumee mais recrutement\descendre.py absent" }
            if (-not (Test-Path -LiteralPath $pyBase)) { throw "descente allumee mais le Python systeme est absent : $pyBase" }
            # elle n'ecrit que des COMPTES : sa sortie va au journal de la tache
            Invoke-PythonRobot -X utf8 $script | ForEach-Object { Write-Output "[descente] $_" }
            # ⚠ le code est GARDE tout de suite : le battement qui suit lance un autre programme et l'ecraserait
            #   (vu le 24/11 : « la descente a echoue (code 0) »)
            $codeDescente = $LASTEXITCODE
            if ($codeDescente -ne 0) {
                Send-Battement "descente" "error" "code $codeDescente"
                throw "la descente a echoue (code $codeDescente) : ON NE COLLECTE PAS sans la liste « ne plus contacter »"
            }
            Send-Battement "descente" "success"
            Write-Output "[descente] faite"
        }
    }

    # ── ② COLLECTE ────────────────────────────────────────────────────────────────────────────
    if (Test-Etape "collecte") {
        Send-Battement "collecte" "running"
        if (-not $Source) {
            $c = Invoke-Collecteur @("collecte", "ouvrir")
            if ($c -ne 0) { Send-Battement "collecte" "error" "ouverture"; throw "la collecte n'a pas pu etre ouverte (code $c)" }
        }
        $echecs = @()
        foreach ($s in $SOURCES) {
            if ($Source -and $s[0] -ne $Source) { continue }
            $debut = Get-Date
            $code = Invoke-Collecteur $s
            $duree = [int]((Get-Date) - $debut).TotalSeconds
            Write-Output ("[collecte] {0,-18} code {1}  ({2} s)" -f ($s -join " "), $code, $duree)
            if ($code -ne 0) { $echecs += ($s -join " ") }
        }
        $code = Invoke-Collecteur @("siren")
        Write-Output "[collecte] siren (placement + minimisation) code $code"
        if ($code -ne 0) { $echecs += "siren" }
        if ($echecs.Count -gt 0) {
            $runFailed = $true
            Send-Battement "collecte" "error" ("en echec : " + ($echecs -join ", "))
            Write-Output "[collecte] ⚠ en echec : $($echecs -join ', ') (les autres sources sont lues)"
        } else {
            Send-Battement "collecte" "success"
        }
    }

    # ── ③ MISE A JOUR ─────────────────────────────────────────────────────────────────────────
    if (Test-Etape "mise_a_jour") {
        if ($Source) {
            Write-Output "[mise_a_jour] sautee : relecture d'une seule source (-Source). Pour fermer une collecte restee"
            Write-Output "              ouverte : relancer avec -StartAtLabel mise_a_jour"
        } else {
            Send-Battement "mise_a_jour" "running"
            $code = Invoke-Collecteur @("maj")
            if ($code -eq 0) { Send-Battement "mise_a_jour" "success" }
            else { $runFailed = $true; Send-Battement "mise_a_jour" "error" "source malade ou collecte absente (code $code)" }
            Write-Output "[mise_a_jour] code $code$(if ($code -ne 0) { ' -- une source MALADE ou pas de collecte ouverte : voir le compte rendu' })"
        }
    }

    # ── ④ CONTROLE ────────────────────────────────────────────────────────────────────────────
    $controleRouge = $false
    if (Test-Etape "controle") {
        Send-Battement "controle" "running"
        $code = Invoke-Collecteur @("controle")
        $controleRouge = ($code -ne 0)
        if ($controleRouge) { $runFailed = $true; Send-Battement "controle" "error" "controle ROUGE" }
        else { Send-Battement "controle" "success" }
        Write-Output "[controle] $(if ($controleRouge) { 'ROUGE -- rien ne montera' } else { 'VERT' })"
    }

    # ── ⑤ EXPORT ──────────────────────────────────────────────────────────────────────────────
    if (Test-Etape "export") {
        $code = Invoke-Collecteur @("csv")
        if ($code -ne 0) { $runFailed = $true }
        Write-Output "[export] CSV code $code"
    }

    # ── ⑥ MONTEE ──────────────────────────────────────────────────────────────────────────────
    if (Test-Etape "montee") {
        if (-not $montee) {
            Write-Output "[montee] eteinte (interrupteur ou DryRun) : rien n'est envoye"
        } elseif ($controleRouge) {
            Write-Output "[montee] ⛔ refusee : le controle est ROUGE"
        } else {
            Send-Battement "montee" "running"
            $script = Join-Path $root "recrutement\pousser.py"
            if (-not (Test-Path -LiteralPath $script)) { throw "montee allumee mais recrutement\pousser.py absent" }
            if (-not (Test-Path -LiteralPath $pyBase)) { throw "montee allumee mais le Python systeme est absent : $pyBase" }
            # elle n'ecrit que des COMPTES : sa sortie va au journal de la tache
            Invoke-PythonRobot -X utf8 $script | ForEach-Object { Write-Output "[montee] $_" }
            $codeMontee = $LASTEXITCODE   # garde avant le battement (meme raison que la descente)
            if ($codeMontee -ne 0) { $runFailed = $true; Send-Battement "montee" "error" "code $codeMontee" }
            else { Send-Battement "montee" "success" }
            Write-Output "[montee] code $codeMontee"
        }
    }

    # ── ⑦ SAUVEGARDE ──────────────────────────────────────────────────────────────────────────
    if (Test-Etape "sauvegarde") {
        # ⚠ la sortie d'un programme externe n'entre PAS dans la transcription de PowerShell 5.1 (vu le
        #   20/11 : le compte rendu manquait au journal) -> on la fait passer par Write-Output.
        if ($DryRun) {
            & $py -X utf8 (Join-Path $root "recrutement\sauvegarder.py") --essai 2>&1 | ForEach-Object { Write-Output "[sauvegarde] $_" }
        } else {
            Send-Battement "sauvegarde" "running"
            & $py -X utf8 (Join-Path $root "recrutement\sauvegarder.py") 2>&1 | ForEach-Object { Write-Output "[sauvegarde] $_" }
            if ($LASTEXITCODE -ne 0) { $runFailed = $true; Send-Battement "sauvegarde" "error" "code $LASTEXITCODE" }
            else { Send-Battement "sauvegarde" "success" }
        }
    }

    # ── ⑧ COMPTE RENDU (des comptes, jamais un nom) ───────────────────────────────────────────
    if (Test-Etape "compte_rendu") {
        $cr = @'
import sqlite3, os
base = os.path.join(os.environ.get("RECRUTEMENT_DONNEES", r"C:\Hektor\recrutement_donnees"), "recrutement.sqlite")
c = sqlite3.connect(base)
n = c.execute("select max(numero) from collecte").fetchone()[0]
if n is None:
    print("  aucune collecte")
else:
    r = c.execute("select debut, fin, etat, note from collecte where numero=?", (n,)).fetchone()
    print(f"  collecte n {n} : {r[2]} ({r[0]} -> {r[1]})")
    for s in c.execute("select reseau, vus, precedent, sante, raison from source_etat where collecte=? order by sante desc, reseau", (n,)):
        print(f"    {s[0]:14} {s[3]:8} {s[4]}")
    for e in c.execute("select etat_suivi, count(*) from fiche group by 1 order by 2 desc"):
        print(f"    etat {e[0]} : {e[1]}")
'@
        Write-Output "[compte_rendu]"
        $cr | & $py -X utf8 - 2>&1 | ForEach-Object { Write-Output "$_" }
        Send-Battement "compte_rendu" "success"
    }
} catch {
    Write-Output "=== ERREUR run recrutement : $_ ==="
    $runFailed = $true
} finally {
    if ((Test-Path -LiteralPath $verrou) -and ((Get-Content -LiteralPath $verrou -TotalCount 1) -eq "$PID")) {
        Remove-Item -LiteralPath $verrou -Force
    }
    Write-Output "=== Fin $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- $(if ($runFailed) { 'QUELQUE CHOSE A VOIR (sortie 1)' } else { 'tout vert (sortie 0)' }) ==="
    Stop-Transcript | Out-Null
    # Un run par mois : on garde 13 mois de journaux.
    Get-ChildItem $logDir -Filter "recrutement_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-400) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem $donnees -Filter "run_detail_*.txt" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-400) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

if ($runFailed) { exit 1 }
exit 0

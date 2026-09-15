# RATTRAPAGE COMPROMIS PAR LA CONSOLE -- ce que l'API ne rend jamais
# ===========================================================================
#
# CE QU'IL VA CHERCHER, compromis par compromis, dans le formulaire de
# l'assistant de Hektor :
#     notairesAcquereur[] et notairesMandant[]   0 sur 10 586 par l'API
#     acquereurs[] et mandants[]                   avec leur NOM et leur telephone
#     montantHonoraireEntree et tauxHonoraireEntree   le TAUX VENDEUR
#
# /!\ IL N'ECRIT RIEN CHEZ HEKTOR, et c'est une construction, pas une intention :
#   il n'envoie que l'OUVERTURE de l'assistant. L'enregistrement est la requete
#   qui porte `actionContainer[] = save + treat`, et ces deux mots n'existent pas
#   dans son code. La tache 0.3 l'a mesure en contre-temoin : " ouvrir/fermer
#   sans enregistrer -> AUCUN mouvement " de la date du bien.
#
# --- LA CADENCE, ET ELLE N'EST PAS NEGOCIABLE ---
# Celle de notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md, section
# rattrapage -- la seule methode console qui n'ait JAMAIS rien declenche
# (56 926 lectures) :
#     1 requete par compromis, 0,5 s entre deux
#     lots de 100 avec 60 s, vagues de 2 000 avec 300 s
# Le rattrapage des DOCUMENTS, lui, a fait bannir notre IP 2 h 28 le 19/08 en
# tirant 2 a 3 requetes/seconde pendant des heures. On ne s'en approche pas.
#
# --- LES DEUX CEINTURES ---
#   -StopAt 02:00   il s'arrete entre deux lots avant l'heure dite. Le run
#                   quotidien de 05:00 fait LUI AUSSI de l'extraction console :
#                   deux flux en meme temps, c'est le doublement de debit qu'on
#                   vient d'ecarter. Une estimation peut se tromper ; cette
#                   ceinture rend l'estimation sans importance.
#   -Courtoisie     il s'efface tant qu'un travail worker tourne. Tu peux donc
#                   utiliser l'app pendant qu'il tourne : chaque geste declenche
#                   un worker qui parle a Hektor lui aussi, et on lui laisse la
#                   place au lieu de tirer en meme temps.
#
# --- REPRENABLE SANS RIEN NOTER ---
# Chaque compromis deja lu est saute au lancement suivant. Un arret, une coupure
# de courant, un 403 : on relance la meme commande et il repart ou il en etait.
#
# DUREE : ~4 h 25 pour les 9 215 compromis non annules (les annules sont ecartes,
# Hektor REFUSE de les ouvrir : " un compromis cloture ne peut pas etre modifie ").
# Mesure du palier du 10/09 : 1 151 lus en 33 min, zero erreur.
#
#     .\scheduled\run_rattrapage_compromis_console.ps1
#     .\scheduled\run_rattrapage_compromis_console.ps1 -Depuis 2024-01-01
# ===========================================================================
param(
    # ═══ LE GENRE, AJOUTE LE 14/09 ═══
    #
    # /!\ ET IL AURAIT DU L'ETRE EN MEME TEMPS QUE L'AUTRE LANCEUR. Le 14/09 j'ai
    #   appris les ventes au lecteur, au pilote et au lanceur d'ENTRETIEN, sans
    #   jamais demander qui d'autre appelait ce pilote. Ils sont trois : les deux
    #   lanceurs et l'etape du run quotidien. Reparer ce qu'on a sous les yeux
    #   n'est pas reparer.
    #
    # /!\ LA CADENCE, ELLE, N'EST PAS ICI. Une vente coute deux requetes ; le
    #   PILOTE ramene le lot a 50 pieces pour que la pause tombe toujours toutes
    #   les 100 requetes, et il l'annonce. Aucun lanceur n'a a le savoir.
    [ValidateSet("compromis", "vente")]
    [string]$Genre = "compromis",
    [string]$StopAt = "02:00",
    [string]$Depuis = "",
    [int]$Limit = 0,
    # /!\ CE LANCEUR N'AVAIT PAS DE SIMULATION, ET CA M'A PIEGE LE 14/09.
    #   J'ai voulu « eprouver » la commande et j'ai lance un VRAI rattrapage --
    #   200 ventes lues avant que je l'arrete. Aucun degat : la cadence etait la
    #   bonne et la donnee est celle qu'on voulait. Mais un lanceur qui ne sait
    #   QUE partir pour de vrai est un piege, et le pilote, lui, sait simuler
    #   depuis toujours. Il manquait juste le fil entre les deux.
    # /!\ « OUVERT » SE JUGE SUR LE DOSSIER, PAS SUR LE BIEN -- arbitrage du
    #   14/09. Un bien vendu en 2019, remis sur le marche en 2026 et de nouveau
    #   sous compromis, a bien un dossier OUVERT : juger sur le bien le raterait.
    #   L'ecart est de 18 dossiers sur 1 711, et ce sont ceux-la.
    # /!\ ET IL FAUT -Force AVEC. Les 9 218 compromis sont deja lus (page 1) :
    #   sans -Force, la garde « deja lu » les sauterait tous et il n'y aurait rien
    #   a faire. C'est leur PAGE 2 qu'on vient chercher.
    [switch]$SansVente,
    # ═══ LES PIECES DONT LA PAGE DES COMMISSIONS S'EST VIDEE ═══   15/09/2026
    #
    # /!\ ET IL FAUT -Force AVEC, pour la meme raison que -SansVente : ces pieces
    #   sont DEJA LUES (page 1), la garde « deja lu » les sauterait toutes. C'est
    #   leur PAGE 2 qu'on vient rechercher.
    #
    # /!\ QUI D'AUTRE APPELLE LE PILOTE ? La question du 14/09, et cette fois je
    #   la pose AVANT. Ils sont trois : ce lanceur, run_entretien_*.ps1, et les
    #   deux etapes du run quotidien. Je n'ajoute le drapeau qu'ICI, et c'est
    #   DELIBERE : dans le pilote les filtres se CUMULENT (AND). Le mettre a
    #   l'entretien donnerait « ce qui a bouge ET dont la page est vide » -- une
    #   intersection presque toujours vide -- la ou il faudrait un OU.
    #   ➡ Rendre l'entretien auto-reparable demande un OU dans la selection.
    #     A faire, mais pas en meme temps qu'un rattrapage.
    [switch]$SansCommission,
    [switch]$Simulation,
    [switch]$Force,
    [switch]$SansCourtoisie
)

# Continue : un avertissement ne doit pas interrompre un run de plusieurs heures.
# Les vrais echecs sont rendus par le CODE DE SORTIE du script python.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

$script = Join-Path $root "phase2\sync\sync_hektor_compromis_console.py"
# Le journal porte le genre : pour le compromis le nom ne change pas d'un
# caractere, et les journaux de septembre restent lisibles a cote.
$journal = Join-Path $root ("logs\scheduled\rattrapage_${Genre}_" +
    (Get-Date -Format "yyyy-MM-dd_HH-mm-ss") + ".log")
New-Item -ItemType Directory -Force -Path (Split-Path $journal) | Out-Null

$argsPy = @($script, "--genre", $Genre, "--limit", "$Limit", "--refresh-session-on-expired")
if ($StopAt) { $argsPy += @("--stop-at", $StopAt) }
if ($Depuis) { $argsPy += @("--depuis", $Depuis) }
if ($SansVente) { $argsPy += "--sans-vente" }
if ($SansCommission) { $argsPy += "--sans-commission" }
if ($Simulation) { $argsPy += "--dry-run" }
if ($Force) { $argsPy += "--force" }
if (-not $SansCourtoisie) { $argsPy += "--courtoisie" }

Write-Output "=== RATTRAPAGE $($Genre.ToUpper()) CONSOLE -- depart $(Get-Date -Format 'HH:mm:ss') ==="
Write-Output "    arret programme : $StopAt   journal : $journal"
if ($Simulation) { Write-Output "    SIMULATION -- aucune lecture chez Hektor" }

# /!\ PAS DE `2>&1` ICI. PowerShell 5.1 enveloppe chaque ligne d'erreur d'un
# executable natif dans un ErrorRecord ; avec ErrorActionPreference = Stop, la
# PREMIERE ligne ecrite sur la sortie d'erreur TUE le run. Mesure du 10/09 :
# le rattrapage s'est arrete net a la premiere vague, apres 2 000 compromis,
# sur une simple ligne de progression. Le script python n'ecrit plus que sur
# la sortie standard, et on ne redirige plus rien.
& $py $argsPy | Tee-Object -FilePath $journal
$code = $LASTEXITCODE

# /!\ UN 403 N'EST PAS UN INCIDENT A REESSAYER, C'EST LE DEBUT D'UN BANNISSEMENT.
# Le script rend 3 dans ce cas et s'arrete de lui-meme. On le DIT, fort, et on ne
# relance pas : verifier depuis une AUTRE IP avant de conclure a une panne Hektor.
if ($code -eq 3) {
    Write-Output "=== ARRET SUR 403 -- NE PAS RELANCER. Verifier depuis une AUTRE IP. ==="
} elseif ($code -ne 0) {
    Write-Output "=== ARRET, code $code -- voir le journal ==="
} else {
    Write-Output "=== TERMINE $(Get-Date -Format 'HH:mm:ss') ==="
}
exit $code

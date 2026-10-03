# Tache planifiee : LA DESCENTE (07:30) -- Supabase vers le serveur (blocs B.1, B.2, B.4).
#
# POURQUOI 07:30, et pas ailleurs.
#   03:00  recherches actives
#   05:30  run quotidien -> ~06:32   il POUSSE la journee vers Supabase
#   07:00  sauvegarde                 instantane de phase2.sqlite
#   07:30  ICI                        ~20 min, fin vers 07:50
# La descente doit lire Supabase APRES que le run de nuit y ait pousse la journee, et
# APRES la sauvegarde -- sinon elle ecrirait dans phase2.sqlite pendant qu'on en fait un
# instantane.
#
# TROIS ETAPES, dans cet ordre :
#   1. pull_from_supabase.py    refait les 120 copies locales (dont les 10 doublures __sb)
#   2. comparer_doublures.py    compte les ecarts et ecrit la photo du jour dans le journal
#   3. magasin_annonce_app.py   note, champ par champ, ce que l'app detient sur les annonces
# La seconde n'a de sens qu'apres la premiere : elle mesure ce que la descente vient de
# poser. Si la descente echoue, on releve quand meme -- la photo dira alors qu'elle date.
#
# LE VERROU COUVRE LES DEUX ETAPES (corrige le 22/08). Chacune le prend a son tour :
# l'etape 1 le pose puis le relache, l'etape 2 le reprend. Un tiers qui le regarde -- le
# rattrapage acquereurs, par exemple -- voit donc toute la duree du traitement, et pas
# seulement la descente. C'etait le defaut releve par l'autre session : le releve des
# doublures, qui pose une vingtaine d'index dont un sur 355 668 lignes, tournait hors
# verrou et a fait echouer le rattrapage du 22/08 sur « database is locked ».
#
# ⚠ LA DESCENTE EST LA PLUS LOURDE DE TOUTES LES TACHES qui parlent a Supabase. C'est elle
# qui a sature l'instance jusqu'au redemarrage dans la nuit du 21 au 22/08 -- deux passes
# lancees en une heure, ~2 800 requetes sans frein. Elle porte desormais trois freins
# (pauses, tables legeres d'abord, verrou contre le chevauchement) ; ne pas les retirer, et
# regarder ses premiers matins avant de considerer que c'est acquis.
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "descente_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

# ═══════════════════════════════════════════════════════════════════════════════
# ⚠⚠ LA DESCENTE NE DEMARRE PAS SI LE RUN QUOTIDIEN TOURNE ENCORE   03/10/2026
# ═══════════════════════════════════════════════════════════════════════════════
# VECU LE 03/10 : le run a deborde jusqu'a 08:21 (une etape passee de 46 s a 79 min),
# la descente a demarre a 08:15, et trois etapes du run sont tombees l'une apres
# l'autre -- la troisieme a ARRETE le run. 17 etapes jamais demarrees, dont TOUTES
# les montees vers le cloud : l'app est restee sur les donnees de la veille.
#
# ⭐ UN VERROU EXISTE DEJA (VerrouUnique / pull_from_supabase.lock, 22/08) ET IL A
#   FONCTIONNE : l'etape « redescente des lectures console » appelle justement
#   pull_from_supabase.py, elle a trouve le verrou tenu et elle est sortie en code 2
#   -- « un chevauchement n'est pas un bogue », c'est ecrit dans le script.
#   MAIS il ne couvre que les 6 etapes du run qui le prennent, sur 54. Les deux
#   autres etapes tombees ne le prennent pas.
#
# ⛔ POURQUOI PAS SIMPLEMENT FAIRE PRENDRE CE VERROU A TOUT LE RUN : il n'est pas
#   reentrant. Le wrapper le tiendrait, et les 6 etapes qui le demandent ensuite
#   -- processus FILS, donc autres PID -- se bloqueraient elles-memes.
#   On garde donc le verrou pour ce qu'il fait bien, et on ajoute ICI la seule
#   chose qu'il ne sait pas faire : regarder si LE RUN ENTIER tourne.
#
# ON PATIENTE PLUTOT QUE DE RENONCER : sauter une descente laisse les doublures
# d'hier, et la garde de fraicheur de relation_ledger crie le lendemain. Le 03/10,
# 45 minutes auraient absorbe le debordement en entier (08:21, soit +40 min).
# Au-dela, c'est que quelque chose ne va pas : on renonce, et BRUYAMMENT (exit 1,
# pour que le Planificateur l'enregistre -- lecon du 19/08, un exit 0 menteur avait
# cache 18 jours de lots en echec).
function Test-QuotidienEnCours {
    # ① l'etat de la tache -- fait autorite pour le cas qui compte : les deux
    #    taches planifiees qui se croisent la nuit.
    try {
        if ((Get-ScheduledTask -TaskName "GTI Quotidien" -ErrorAction Stop).State -eq 'Running') { return $true }
    } catch { }
    # ② le journal -- ⚠ INDISPENSABLE : un lancement MANUEL (ou une reprise
    #    -StartAtLabel) n'allume PAS l'etat de la tache. Vecu le 03/10 a 09:50.
    #    Un journal ecrit il y a moins de 3 min ET sans ligne de fin = ca tourne.
    $dernier = Get-ChildItem $logDir -Filter "quotidien_*.log" -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($dernier -and ((Get-Date) - $dernier.LastWriteTime).TotalMinutes -lt 3) {
        if (-not (Select-String -Path $dernier.FullName -Pattern "Run quotidien termine|ERREUR run quotidien" -Quiet -ErrorAction SilentlyContinue)) {
            return $true
        }
    }
    return $false
}

$attenteMaxMinutes = 45
$debutAttente = Get-Date
while (Test-QuotidienEnCours) {
    $ecoule = [math]::Round(((Get-Date) - $debutAttente).TotalMinutes)
    if ($ecoule -ge $attenteMaxMinutes) {
        Write-Output "=== DESCENTE ANNULEE : le run quotidien tourne encore apres $attenteMaxMinutes min ==="
        Write-Output "    On ne descend PAS par-dessus lui -- c'est ce qui a casse le run le 03/10."
        Write-Output "    Les doublures resteront celles d'hier ; la garde de fraicheur le dira."
        Stop-Transcript | Out-Null
        exit 1
    }
    Write-Output "--- le run quotidien tourne encore, on patiente ($ecoule/$attenteMaxMinutes min) ---"
    Start-Sleep -Seconds 60
}

$runFailed = $false
try {
    Write-Output "=== Descente demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    Write-Output "--- 1/3 descente Supabase -> serveur ---"
    & $py (Join-Path $root "phase2\sync\pull_from_supabase.py")
    $codeDescente = $LASTEXITCODE
    Write-Output "--- descente terminee (exit $codeDescente) ---"
    if ($codeDescente -ne 0) { $runFailed = $true }

    # Le releve tourne MEME si la descente a echoue : mieux vaut une photo qui dit
    # « les doublures datent d'hier » qu'aucune photo du tout.
    Write-Output "--- 2/3 releve des doublures ---"
    & $py (Join-Path $root "phase2\checks\comparer_doublures.py")
    $codeReleve = $LASTEXITCODE
    Write-Output "--- releve termine (exit $codeReleve) ---"
    if ($codeReleve -ne 0) { $runFailed = $true }

    # C.6 25/08 -- le magasin de ce que l'app detient sur les annonces.
    # ICI, en troisieme, et pas dans le run de nuit : il compare app_dossier_current
    # (que la descente vient de rafraichir) a app_view_generale (que le run de 05:30
    # vient de refaire). Il lui faut LES DEUX cotes frais. Le lancer ailleurs
    # comparerait une photo du jour a une photo de la veille -- mesure le 25/08 :
    # 89 faux ecarts, contre 0 une fois les deux cotes a la meme heure.
    Write-Output "--- 3/3 magasin des champs app (annonces) ---"
    & $py (Join-Path $root "phase2\identite\magasin_annonce_app.py")
    $codeMagasin = $LASTEXITCODE
    Write-Output "--- magasin termine (exit $codeMagasin) ---"
    if ($codeMagasin -ne 0) { $runFailed = $true }

    Write-Output "=== Descente terminee $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
} catch {
    Write-Output "=== ERREUR descente : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "descente_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# PROPAGER L'ECHEC AU PLANIFICATEUR -- meme correctif que run_recherches_actives.ps1 le
# 19/08 : un exit 0 menteur avait cache 18 jours de lots en echec, et avec eux la perte de
# 1 104 recherches actives. Windows doit voir l'echec, sinon la sonde conclut « 0 anomalie ».
if ($runFailed) { exit 1 }

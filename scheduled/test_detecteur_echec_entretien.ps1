# EPREUVE -- LE DETECTEUR D'ECHEC DE « GTI ENTRETIEN DOCUMENTS » VOIT-IL UN ECHEC ?
#                                                       16/10/2026, chantier 6 (correctif)
#
# POURQUOI. La nuit du 15 au 16/10, la tache a dit « les 4 lignes sont passees » et est
# sortie 0 -- mais son journal ne portait AUCUN des 4 marqueurs, et surtout son detecteur
# d'echec etait MORT : `Invoke-Ligne` ecrivait sur le flux de sortie, donc sa valeur de
# retour etait un TABLEAU, et `-not` d'un tableau non vide vaut $false. Une ligne en echec
# n'aurait JAMAIS ete comptee -> tache verte -> moniteur muet (il lit LastTaskResult).
#
# ⚠ ET ELLE EXECUTE LE VRAI CODE, PAS UNE IMITATION. L'avertissement du 03/10
# (run_full_pipeline.ps1, l. 228-245) le dit noir sur blanc : l'epreuve de la veille
# « testait une imitation, pas le vrai code ». Donc ici on LIT le fichier de la tache, on
# EXTRAIT le texte exact de la fonction, et on l'execute telle quelle.
#
# ⚠ ELLE NE LANCE PAS LA TACHE : elle remplace node par un `cmd /c exit <code>`. Aucune
#   lecture chez Hektor, aucune ecriture, aucun travail mis en file.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\test_detecteur_echec_entretien.ps1
#
# Sortie 0 = tout vert. Sortie 1 = au moins un controle rouge.

$ErrorActionPreference = "Continue"
$fichier = Join-Path $PSScriptRoot "run_entretien_documents.ps1"
$verts = 0
$rouges = @()

function Controle {
    param([string]$Nom, [bool]$Attendu, [string]$Mesure)
    if ($Attendu) {
        Write-Host ("  OK   {0} -- {1}" -f $Nom, $Mesure)
        $script:verts += 1
    } else {
        Write-Host ("  ROUGE {0} -- {1}" -f $Nom, $Mesure)
        $script:rouges += $Nom
    }
}

if (-not (Test-Path -LiteralPath $fichier)) { Write-Host "STOP : $fichier introuvable"; exit 1 }
$source = Get-Content -LiteralPath $fichier -Raw

# ── ① ON EXTRAIT LE TEXTE EXACT DE LA FONCTION ───────────────────────────────────────
# On part de « function Invoke-Ligne {» et on suit les accolades : pas de regex fragile.
$debut = $source.IndexOf("function Invoke-Ligne")
if ($debut -lt 0) { Write-Host "STOP : fonction Invoke-Ligne introuvable dans la tache"; exit 1 }
$i = $source.IndexOf("{", $debut)
$profondeur = 0
$fin = -1
for ($k = $i; $k -lt $source.Length; $k++) {
    if ($source[$k] -eq "{") { $profondeur++ }
    elseif ($source[$k] -eq "}") { $profondeur--; if ($profondeur -eq 0) { $fin = $k; break } }
}
if ($fin -lt 0) { Write-Host "STOP : accolades non refermees"; exit 1 }
$texteVrai = $source.Substring($debut, $fin - $debut + 1)

Write-Host "`n=== LE CODE EPROUVE EST CELUI DU FICHIER ($($texteVrai.Length) caracteres) ==="

# ── ② ET ON FABRIQUE LA FORME D'AVANT, POUR LE TEMOIN INVERSE ────────────────────────
# (uniquement en retirant le remede : Write-Host -> Write-Output, et sans | Out-Host)
$texteAvant = $texteVrai.Replace("Write-Host", "Write-Output").Replace(" | Out-Host", "")

# ── ③ LA FAUSSE COMMANDE : elle ecrit, puis sort avec le code demande ────────────────
$cmd = Join-Path $env:SystemRoot "System32\cmd.exe"
$nodeExe = $cmd
$argsEchec  = @("/c", "echo bruit de sortie de node& exit 3")
$argsSucces = @("/c", "echo bruit de sortie de node& exit 0")

# ── ④ LE VRAI CODE : il doit rendre UN SEUL BOOLEEN ──────────────────────────────────
Invoke-Expression $texteVrai
$r = Invoke-Ligne -Titre "epreuve ECHEC" -Arguments $argsEchec
$n = @($r).Count
Controle "la fonction ne rend QU'UNE SEULE valeur (echec)" ($n -eq 1) "$n valeur(s) rendue(s)"
Controle "et c'est un booleen" ($r -is [bool]) "type rendu : $($r.GetType().Name)"
Controle "elle dit FAUX quand la ligne echoue" ($r -eq $false) "valeur rendue : $r"
$detecte = @(); if (-not (Invoke-Ligne -Titre "epreuve ECHEC (vrai appelant)" -Arguments $argsEchec)) { $detecte += "ligne" }
Controle "le vrai appelant COMPTE l'echec" ($detecte.Count -eq 1) "$($detecte.Count) echec(s) compte(s), attendu 1"

$r2 = Invoke-Ligne -Titre "epreuve SUCCES" -Arguments $argsSucces
Controle "elle dit VRAI quand la ligne reussit" ($r2 -eq $true -and @($r2).Count -eq 1) "valeur rendue : $r2 ($(@($r2).Count) valeur)"
$detecte2 = @(); if (-not (Invoke-Ligne -Titre "epreuve SUCCES (vrai appelant)" -Arguments $argsSucces)) { $detecte2 += "ligne" }
Controle "et le vrai appelant NE compte PAS un succes" ($detecte2.Count -eq 0) "$($detecte2.Count) echec(s) compte(s), attendu 0"

# ── ⑤ LE TEMOIN INVERSE : la forme d'avant doit RATER l'echec ────────────────────────
# Sans lui, ces controles passeraient aussi sur du code casse (lecon du projet).
Invoke-Expression ($texteAvant.Replace("Invoke-Ligne", "Invoke-LigneAvant"))
$ra = Invoke-LigneAvant -Titre "temoin AVANT" -Arguments $argsEchec
$na = @($ra).Count
Controle "TEMOIN INVERSE : l'ancienne forme rendait PLUSIEURS valeurs" ($na -gt 1) "$na valeurs rendues"
$detecteAvant = @(); if (-not (Invoke-LigneAvant -Titre "temoin AVANT" -Arguments $argsEchec)) { $detecteAvant += "ligne" }
Controle "TEMOIN INVERSE : l'ancienne forme NE voyait PAS l'echec" ($detecteAvant.Count -eq 0) "$($detecteAvant.Count) echec(s) compte(s) -- c'est le defaut du 15/10"

# ── ⑥ ET LE JOURNAL : les marqueurs arrivent-ils bien a la transcription ? ───────────
$journal = Join-Path $env:TEMP ("epreuve_entretien_" + (Get-Date -Format "HHmmss") + ".log")
Start-Transcript -Path $journal | Out-Null
Invoke-Ligne -Titre "3/4 marqueur de journal" -Arguments $argsSucces | Out-Null
Stop-Transcript | Out-Null
$texteJournal = Get-Content -LiteralPath $journal -Raw -ErrorAction SilentlyContinue
Controle "le marqueur « --- x/4 » arrive au journal" ($texteJournal -like "*--- 3/4 marqueur de journal*") "journal de $($texteJournal.Length) caracteres"
Controle "et la sortie de la commande aussi" ($texteJournal -like "*bruit de sortie de node*") "le detail de la ligne est trace"
Remove-Item -LiteralPath $journal -Force -ErrorAction SilentlyContinue

# ── ④ TOUTES LES TACHES PORTENT LA MEME FONCTION -- ajoute le 19/10, ELARGI le 19/10 ─
# Depuis le 19/10 PLUSIEURS taches portent Invoke-Ligne : l'entretien des DOCUMENTS
# (22:00), celui des PHOTOS (21:00), et le BALAYAGE DES PHOTOS MASQUEES (00:00).
# Cette epreuve n'en execute QU'UNE.
# ➡ Plutot que de la dedoubler, on EXIGE qu'elles soient IDENTIQUES A L'OCTET PRES :
#   si elles le sont, eprouver l'une c'est eprouver toutes les autres. Si un jour
#   l'une divergent, ce controle passe au rouge et dit qu'il faut dedoubler l'epreuve.
# ⚠ C'est la regle du balayage de famille : un defaut se cherche LA OU VIVENT TOUS LES
#   MEMBRES, pas seulement chez celui qu'on a sous les yeux.
#
# ⚠⚠ ELARGI LE 19/10, ET C'EST LE POINT : la 1re version NOMMAIT SA JUMELLE EN DUR
#   (run_entretien_photos.ps1). Une TROISIEME tache portant la meme fonction lui aurait
#   donc ECHAPPE EN SILENCE -- exactement le trou que ce controle est cense boucher.
#   On BALAIE donc le dossier : toute tache de scheduled\ qui porte Invoke-Ligne est
#   comparee, qu'elle existe aujourd'hui ou qu'on l'ecrive demain.
function Get-TexteInvokeLigne {
    param([string]$Chemin)
    $src = Get-Content -LiteralPath $Chemin -Raw
    $d = $src.IndexOf("function Invoke-Ligne")
    if ($d -lt 0) { return $null }
    $i = $src.IndexOf("{", $d); $p = 0; $f = -1
    for ($k = $i; $k -lt $src.Length; $k++) {
        if ($src[$k] -eq "{") { $p++ }
        elseif ($src[$k] -eq "}") { $p--; if ($p -eq 0) { $f = $k; break } }
    }
    if ($f -lt 0) { return "" }
    return $src.Substring($d, $f - $d + 1)
}

$porteuses = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter "*.ps1" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -ne $fichier -and $_.Name -notlike "test_*" } |
    Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -like "*function Invoke-Ligne*" })

Controle "au moins une autre tache porte Invoke-Ligne" ($porteuses.Count -ge 1) `
    "$($porteuses.Count) autre(s) tache(s) porteuse(s) trouvee(s) dans scheduled\"

foreach ($p in $porteuses) {
    $t = Get-TexteInvokeLigne -Chemin $p.FullName
    if ($null -eq $t) {
        Controle "$($p.Name) porte Invoke-Ligne" $false "fonction introuvable"
    } else {
        Controle "$($p.Name) porte la MEME fonction (a l'octet pres)" ($t -ceq $texteVrai) `
            "eprouvee $($texteVrai.Length) car. / $($p.Name) $($t.Length) car. -- si elles divergent, DEDOUBLER cette epreuve"
    }
}

Write-Host ""
if ($rouges.Count -gt 0) {
    Write-Host "⛔ $($rouges.Count) ROUGE(S) : $($rouges -join ' | ')"
    exit 1
}
Write-Host "✅ TOUT VERT -- $verts controles. Le detecteur d'echec voit un echec, et le journal porte les marqueurs."
exit 0

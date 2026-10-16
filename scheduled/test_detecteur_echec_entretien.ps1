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

Write-Host ""
if ($rouges.Count -gt 0) {
    Write-Host "⛔ $($rouges.Count) ROUGE(S) : $($rouges -join ' | ')"
    exit 1
}
Write-Host "✅ TOUT VERT -- $verts controles. Le detecteur d'echec voit un echec, et le journal porte les marqueurs."
exit 0

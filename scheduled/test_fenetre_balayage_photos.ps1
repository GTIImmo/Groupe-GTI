# LA FENETRE DE POSE DU BALAYAGE DES PHOTOS MASQUEES : essai hors ligne.        26/10/2026
#
# On eprouve LA VRAIE FONCTION (Test-HorsFenetreDePose, decoupee dans le script par l'arbre syntaxique de
# PowerShell, sans lancer le script), heure par heure, avec les reglages par defaut du script.
# Pourquoi : le 25/10 a 23:00 (heure d'hiver, tache decalee d'une heure), l'ancienne garde « refus si
# l'heure depasse 1 » a refuse le lot. Etude : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md §15.
#
#     powershell -NoProfile -File scheduled\test_fenetre_balayage_photos.ps1
#     sortie 0 = vert ; 1 = un controle en echec ; 2 = n'a pas pu mesurer

$script = Join-Path $PSScriptRoot "run_balayage_photos_masquees.ps1"
$erreurs = $null
$arbre = [System.Management.Automation.Language.Parser]::ParseFile($script, [ref]$null, [ref]$erreurs)
if ($erreurs.Count -gt 0) { Write-Output "ECHEC  le script ne s'analyse pas : $($erreurs[0].Message)"; exit 2 }
$fonction = $arbre.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-HorsFenetreDePose' }, $true) | Select-Object -First 1
if (-not $fonction) { Write-Output "ECHEC  la fonction Test-HorsFenetreDePose est introuvable"; exit 2 }
. ([scriptblock]::Create($fonction.Extent.Text))

# les reglages PAR DEFAUT du script, lus dans son bloc param (pas recopies a la main)
$defauts = @{}
foreach ($p in $arbre.ParamBlock.Parameters) {
    if ($p.DefaultValue) { $defauts[$p.Name.VariablePath.UserPath] = $p.DefaultValue.Extent.Text }
}
$limite = [int]$defauts['HeureLimite']
$soir = [int]$defauts['HeureDebutSoir']

$echecs = 0
function Controle([string]$nom, [bool]$vrai, [string]$detail) {
    if ($vrai) { Write-Output "  OK   $nom" } else { Write-Output "ECHEC  $nom -- $detail"; $script:echecs++ }
}

$refusees = @(0..23 | Where-Object { Test-HorsFenetreDePose -Heure $_ -Limite $limite -DebutSoir $soir })
$acceptees = @(0..23 | Where-Object { -not (Test-HorsFenetreDePose -Heure $_ -Limite $limite -DebutSoir $soir) })
Controle "(1) reglages par defaut lus dans le script : limite 1 h, debut du soir 20 h" ($limite -eq 1 -and $soir -eq 20) "limite=$limite soir=$soir"
Controle "(2) un depart a 23:00 (heure d'hiver, le cas du 25/10) est ACCEPTE" ($acceptees -contains 23) ($acceptees -join ',')
Controle "(3) un depart a 00:00 (l'heure d'origine) est ACCEPTE" ($acceptees -contains 0) ($acceptees -join ',')
Controle "(4) 01:00 est encore accepte (la limite elle-meme)" ($acceptees -contains 1) ($acceptees -join ',')
Controle "(5) un depart tardif (02:00 = les recherches, 04:00 = le run) est REFUSE" (($refusees -contains 2) -and ($refusees -contains 4)) ($refusees -join ',')
Controle "(6) exactement 2 h -> 19 h refusees, 20 h -> 1 h acceptees" (($refusees -join ',') -eq ((2..19) -join ',')) ($refusees -join ',')

# TEMOIN INVERSE : la garde d'avant (« refus si l'heure depasse la limite ») refusait 23:00
$ancienne = { param([int]$Heure, [int]$Limite) return ($Heure -gt $Limite) }
Controle "(7) TEMOIN INVERSE : l'ancienne garde refusait 23:00 (le defaut de la nuit du 25/10)" (& $ancienne 23 1) ""

# LE BRANCHEMENT : la garde du script appelle bien la fonction (et plus l'ancienne comparaison)
$texte = Get-Content -LiteralPath $script -Raw -Encoding UTF8
Controle "(8) la garde du script appelle Test-HorsFenetreDePose" ($texte -match 'IgnorerFenetre -and -not \$DryRun -and \(Test-HorsFenetreDePose') ""
Controle "(9) l'ancienne comparaison seule a disparu" (-not ($texte -match '-not \$DryRun -and \$heure -gt \$HeureLimite\)')) ""

if ($echecs -gt 0) { Write-Output ""; Write-Output "$echecs controle(s) en echec."; exit 1 }
Write-Output ""; Write-Output "Tous les controles sont verts."
exit 0

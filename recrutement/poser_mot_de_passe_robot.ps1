# Donne un mot de passe au ROBOT du recrutement (recrutement_robot)                      24/11/2026
# ═══════════════════════════════════════════════════════════════════════════════
# A LANCER PAR FREDERIC (une PowerShell ordinaire suffit). Claude ne voit jamais le mot de passe.
#
# CE QU'IL FAIT :
#   1. fabrique un mot de passe aleatoire (32 caracteres, generateur cryptographique) ;
#   2. l'ecrit dans C:\Hektor\recrutement_donnees\robot.env (hors du depot), avec l'adresse du pooler
#      lue dans C:\Hektor\Projet\.env -- c'est ce fichier que lit recrutement/robot.py ;
#   3. calcule son EMPREINTE SCRAM-SHA-256 (le format dans lequel Postgres range les mots de passe) et
#      copie dans le presse-papiers :  alter role recrutement_robot with login password 'SCRAM-SHA-256$...';
#      ⭐ LE MOT DE PASSE LUI-MEME NE QUITTE JAMAIS LE SERVEUR : ni l'editeur SQL, ni son historique, ni
#        Claude ne le voient -- seulement son empreinte, qui ne permet pas de se connecter ;
#   4. attend que vous ayez colle et lance la commande dans l'editeur SQL, puis vide le presse-papiers.
#
# Pour CHANGER le mot de passe plus tard : relancer ce script (il remplace robot.env).
# Pour COUPER le robot : dans l'editeur SQL,  alter role recrutement_robot nologin;
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Hektor\Projet\recrutement\poser_mot_de_passe_robot.ps1

param(
    # ESSAI DU CALCUL SEULEMENT : rend l'empreinte d'un mot de passe et d'un sel FIXES (en base64), sans
    # rien ecrire ni copier -- pour la comparer a celle de Python (verification du 24/11).
    [string]$EssaiMotDePasse = "",
    [string]$EssaiSelBase64 = ""
)

$ErrorActionPreference = "Stop"

# L'empreinte SCRAM-SHA-256 (RFC 5802 / 7677), au format de pg_authid.rolpassword :
#   SCRAM-SHA-256$<iterations>:<sel>$<StoredKey>:<ServerKey>
function New-EmpreinteScram {
    param([string]$MotDePasse, [byte[]]$Sel, [int]$Iterations = 4096)
    $pbkdf2 = New-Object Security.Cryptography.Rfc2898DeriveBytes -ArgumentList @(
        [Text.Encoding]::UTF8.GetBytes($MotDePasse), $Sel, $Iterations, [Security.Cryptography.HashAlgorithmName]::SHA256)
    $saltedPassword = $pbkdf2.GetBytes(32)
    $hmac = New-Object Security.Cryptography.HMACSHA256 -ArgumentList (, $saltedPassword)
    $clientKey = $hmac.ComputeHash([Text.Encoding]::ASCII.GetBytes("Client Key"))
    $serverKey = $hmac.ComputeHash([Text.Encoding]::ASCII.GetBytes("Server Key"))
    $storedKey = [Security.Cryptography.SHA256]::Create().ComputeHash($clientKey)
    return ('SCRAM-SHA-256${0}:{1}${2}:{3}' -f $Iterations, [Convert]::ToBase64String($Sel),
            [Convert]::ToBase64String($storedKey), [Convert]::ToBase64String($serverKey))
}

if ($EssaiMotDePasse) {
    Write-Output (New-EmpreinteScram -MotDePasse $EssaiMotDePasse -Sel ([Convert]::FromBase64String($EssaiSelBase64)))
    exit 0
}

$projet  = "dwaqxfrinihnychuoptk"
$envProj = "C:\Hektor\Projet\.env"
$cible   = "C:\Hektor\recrutement_donnees\robot.env"

# ── l'adresse du pooler (la meme que Console/sauvegarde_plan_supabase.js) ─────
$hote = $null
foreach ($ligne in Get-Content -LiteralPath $envProj -Encoding UTF8) {
    if ($ligne -match '^\s*SUPABASE_POOLER_HOST\s*=\s*"?([^"\s]+)"?\s*$') { $hote = $Matches[1] }
}
if (-not $hote) { throw "SUPABASE_POOLER_HOST introuvable dans $envProj" }

# ── 1. le mot de passe (lettres et chiffres seulement : aucune normalisation SASLprep a craindre) ──
$alea = [Security.Cryptography.RandomNumberGenerator]::Create()
$alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789".ToCharArray()
$octets = New-Object byte[] 32
$alea.GetBytes($octets)
$motDePasse = -join ($octets | ForEach-Object { $alphabet[$_ % $alphabet.Length] })

# ── 2. robot.env ─────────────────────────────────────────────────────────────
$contenu = @(
    "# Reglages du robot du recrutement (recrutement/robot.py). Ecrit par poser_mot_de_passe_robot.ps1 le $(Get-Date -Format 'dd/MM/yyyy HH:mm').",
    "# NE PAS COMMITER, NE PAS COPIER : il ouvre le schema recrutement (et rien d'autre).",
    "RECRUTEMENT_ROBOT_HOTE=$hote",
    "RECRUTEMENT_ROBOT_PORT=5432",
    "RECRUTEMENT_ROBOT_UTILISATEUR=recrutement_robot.$projet",
    "RECRUTEMENT_ROBOT_MOT_DE_PASSE=$motDePasse"
)
[IO.File]::WriteAllLines($cible, $contenu, (New-Object Text.UTF8Encoding($false)))

# ── 3. l'empreinte SCRAM-SHA-256 (le mot de passe lui-meme ne sort pas d'ici) ──
$sel = New-Object byte[] 16
$alea.GetBytes($sel)
$empreinte = New-EmpreinteScram -MotDePasse $motDePasse -Sel $sel
$motDePasse = $null

Set-Clipboard -Value "alter role recrutement_robot with login password '$empreinte';"

Write-Host ""
Write-Host "1. robot.env est ecrit : $cible"
Write-Host "2. La commande est dans le presse-papiers (elle ne contient que l'EMPREINTE du mot de passe)."
Write-Host "   Ouvrez l'editeur SQL : https://supabase.com/dashboard/project/$projet/sql/new"
Write-Host "   Collez (Ctrl+V), puis Run. Vous devez voir « Success. No rows returned »."
Write-Host ""
Read-Host "3. Appuyez sur Entree une fois la commande lancee (le presse-papiers sera vide)"
Set-Clipboard -Value " "
Write-Host "Presse-papiers vide. Dites a Claude que c'est fait : il essaiera la connexion du robot."

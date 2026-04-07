## Objet

Commande fiable pour forcer le refresh de tous les `AnnonceById` de la phase 1 sans modifier `sync_raw.py` et sans purger toute la base.

## Contexte

La commande :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode full --resources annonces
```

ne refait pas toujours tous les détails annonce.

En l'état actuel du script :
- le listing annonces est bien relu complètement
- mais les appels `AnnonceById` sont rejoués seulement pour :
  - les IDs détectés comme changés
  - et les IDs sans `last_detail_sync_at`

Donc si Hektor change un `statut_name` sans changer `date_maj`, le mode `update` peut rater ce changement.

## Solution sans modifier le code

Forcer `last_detail_sync_at = null` pour toutes les annonces, puis relancer :
- `sync_raw.py --mode full --resources annonces`
- `normalize_source.py`

Cela oblige la phase `annonce_detail` à repasser sur tout le stock actif.

## Commande complète recommandée

```powershell
@'
import sqlite3
conn = sqlite3.connect(r"C:\Users\frede\Desktop\Projet\data\hektor.sqlite")
conn.execute("update sync_annonce_state set last_detail_sync_at = null")
conn.commit()
print(conn.execute("select count(*) from sync_annonce_state where last_detail_sync_at is null").fetchone()[0])
'@ | .\.venv\Scripts\python.exe -; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; .\.venv\Scripts\python.exe sync_raw.py --mode full --resources annonces; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; .\.venv\Scripts\python.exe normalize_source.py
```

## Effet attendu

- tous les IDs présents dans `sync_annonce_state` sont marqués comme détail à recharger
- la sync annonces rejoue les `AnnonceById`
- `normalize_source.py` réécrit `hektor_annonce_detail`
- les changements de `statut_name` sont récupérés même si `date_maj` n'avait pas bougé

## Contrôle conseillé après run

Exemple pour l'annonce `52412` :

```sql
select
  a.hektor_annonce_id,
  a.date_maj,
  a.synced_at,
  d.statut_name,
  d.synced_at as detail_synced_at
from hektor_annonce a
left join hektor_annonce_detail d using(hektor_annonce_id)
where a.hektor_annonce_id = '52412';
```

## Limite

Cette méthode est un contournement propre.

Le vrai correctif durable serait de faire évoluer `sync_raw.py` pour que :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode full --resources annonces
```

rejoue réellement tous les `AnnonceById` sur le stock actif, même si `date_maj` n'a pas changé.

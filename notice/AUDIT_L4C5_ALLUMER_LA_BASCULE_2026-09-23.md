# Audit avant d'allumer la bascule (`L4-c ⑤`)

*23/09/2026. La case du tableau **objets × gestes** que je n'avais pas remplie :
« qu'arrive-t-il à ce que le run NE reconstruit PAS ? »*

> **CONCLUSION : la bascule n'est pas un remplissage de table. C'est un remplissage de
> table ET une traduction de 60 060 lignes, dans la même fenêtre.**

---

## 1. Ce qui bascule tout seul, et ce qui ne bascule pas

| | |
|---|---|
| **reconstruit chaque nuit depuis le miroir** *(donc bascule seul)* | `app_contact_current` · `app_contact_relation_current` · `app_contact_search_current` |
| **JAMAIS reconstruit** *(donc reste sur l'ancien numéro)* | **18 tables de l'app**, dont `app_rapprochement` |

```
table                             lignes   n° Hektor   doublure
app_rapprochement                 49 721    49 721     49 684     ⚠ 37 sans
app_search_count_high_water       10 220    10 220     10 180     ⚠ 40 sans
app_console_deleted_contact_log       12        12          0     ⚠ 12 sans
app_google_calendar_event_link        11         9          8     ⚠  1 sans
app_email_envoi                       82        24         24
app_proposition                       11        11         11
app_relance_rapprochement             10        10         10
app_bien_acquereur_statut              7         7          7
app_espace_visite_request              3         3          3
+ 6 tables vides
                                  ──────
                                  60 060 lignes portent un numero de contact
```

---

## 2. ⛔ CE QUE ÇA CASSERAIT — mesuré, pas supposé

**Onze RPC filtrent `app_rapprochement` par `hektor_contact_id`** :

```
app_count_rapprochements_for_contact     app_get_rapprochements_for_dossier
app_count_rapprochements_for_contacts    app_refresh_rapprochements_for_dossier
app_generate_rapprochement_alerts        app_refresh_rapprochements_for_search
app_get_dossier_timeline                 app_process_rapprochement_dirty
app_contact_activite                     app_upsert_one_rapprochement
app_bulk_recompute_chunk
```

Après la bascule, `app_contact_current` porte **notre** numéro et `app_rapprochement` garde
**celui de Hektor**. Ces onze fonctions ne joignent plus rien :

- **les rapprochements disparaissent de l'app** *(49 721 lignes devenues invisibles)* ;
- **les alertes de rapprochement cessent** ;
- **les fils d'activité des contacts se vident** ;
- et le moteur, en recalculant, **écrirait des lignes en double** sous le nouveau numéro.

⚠ **Rien de tout cela ne leverait une erreur.** Les fonctions rendraient simplement zéro
ligne. C'est, une fois de plus, la signature des défauts de ce projet.

---

## 3. Le remède, et il est mécanique

**Traduire `hektor_contact_id` dans ces 18 tables au moment de la bascule** —
`hektor_contact_id := app_contact_id` — puisque la doublure EST la nouvelle identité.

```
traduisibles (la doublure est la)     59 971 lignes
non traduisibles                          ~89 lignes
   37  app_rapprochement : 3 contacts RECENTS (605476/77/79) dont la doublure
       n'est pas encore propagee -> LA PROPAGATION LES RATTRAPE avant la bascule
   40  app_search_count_high_water : contacts ABSENTS de l'app -> poids mort deja
   12  app_console_deleted_contact_log : contacts SUPPRIMES -> c'est un JOURNAL,
       il doit garder le numero d'origine. NE PAS TRADUIRE.
    1  app_google_calendar_event_link
```

⚠ **`app_console_deleted_contact_log` ne doit PAS être traduite** : c'est la trace de ce qui
a été supprimé, elle doit garder le numéro tel qu'il était. Une trace qu'on réécrit ne
trace plus rien.

---

## 4. La forme réelle de la bascule

```
①  lancer app_contact_id_propager      -> rattrape les 37
②  SAUVEGARDE locale (VACUUM INTO) + note du compte de chaque table
③  remplir app_contact_identite_app    356 156 paires
④  traduire les 17 tables              hektor_contact_id := app_contact_id
    (PAS app_console_deleted_contact_log)
⑤  build_contacts_layer                la couche bascule
⑥  push_contacts_to_supabase           AVEC --include-archived-searches
⑦  les 9 liens d'agenda (JSON)
⑧  verifier : rapprochements visibles, sondes a zero, cibles a 100 %
```

⚠ **③ à ⑥ dans la MÊME fenêtre.** Entre ③ et ⑤ la base est incohérente ; entre ⑤ et ⑥
l'app et le serveur divergent.

⚠ **Écrire chaque commande en entier et la MONTRER avant de l'exécuter** *(règle posée le
22/09 après la suppression accidentelle de 7 201 recherches, causée par un drapeau oublié)*.

**RETOUR ARRIÈRE** : vider `app_contact_identite_app`, retraduire à l'envers
*(`app_contact_id` → l'ancien numéro, lisible dans `hektor_target_id`)*, rejouer build+push.
Plus la sauvegarde fichier.

---

## 5. Ce qui reste NON MESURÉ, et qui se dit

- Les **autres tables** que `app_rapprochement` : je n'ai pas compté combien de RPC et
  d'endroits du front filtrent `app_email_envoi`, `app_bien_acquereur_statut`,
  `app_espace_visite_request`, `app_google_calendar_event_link` par le numéro de Hektor.
  L'audit du 22/09 les classait « relie nos données » — donc ils cassent aussi — mais je
  n'ai pas fait le compte exact.
- **RDV / visites** comme objet propre : toujours pas balayé.
- L'effet de la bascule sur les **jobs déjà en file** au moment du basculement.

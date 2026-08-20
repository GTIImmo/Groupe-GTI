# Méthode de travail — comment on mène ce développement

Date : 2026-08-20. **Contrat de travail entre Frédéric et l'assistant.**
Établi après une journée où trois oublis ont été rattrapés par Frédéric, pas par l'assistant.

---

## LE PROTOCOLE — trois temps par tâche

### ① Je lis et je mesure

Avant toute proposition :

- la **checklist en tête du plan** (`PLAN_DEV_ACTUALISE_2026-08-20.md`) ;
- les **notes citées** par le chantier ;
- `ls notice/*.md` **et la racine**, par mot-clé (~158 notes) ;
- `git log --all --diff-filter=D -- 'notice/*'` — **12 notes supprimées le 19/08** portent encore
  de la doctrine active ;
- la **mémoire projet** de l'assistant.

Puis **mesurer en base** au lieu de déduire du code. Annoncer ce qui a été lu et mesuré.

### ② J'explique, Frédéric valide

**Avant d'écrire une seule ligne**, présenter :

| | |
|---|---|
| Ce que je vais faire | en français, sans jargon |
| Ce que ça touche | quelles tables, combien de lignes |
| Ce qui peut casser | et comment je m'en protège |
| Comment on vérifie | avant / après, avec des chiffres |
| **Ce que je ne sais pas** | les incertitudes, nommées |

### ③ J'exécute et je prouve

Essai à blanc → chiffres → accord → application → vérification chiffrée.

---

## RÈGLES DE SÛRETÉ — non négociables

1. **Une tâche à la fois.** Jamais deux objets en même temps : si quelque chose bouge, on sait quoi.
2. **Essai à blanc systématique.** Ce qui s'annule tout seul ne fait pas de dégât.
3. **Une transaction.** Tout ou rien, jamais d'état intermédiaire.
4. **Preuve sur un cas d'abord.** 10 annonces avant 12 162 ; 1 contact avant 57 000.
5. **Une trace de retour arrière** conservée (table de correspondance).
6. **Rien de destructif sans inventaire préalable** de ce qui pend dessous.

---

## CE QUE FRÉDÉRIC SEUL PEUT DONNER

- **Les décisions métier** — l'assistant mesure, il ne tranche pas.
- **Le « go » explicite.** Un « ok » n'est pas un feu vert ; « vas-y » en est un.
- **Les objections.** Le 20/08 elles ont rattrapé trois erreurs. C'est le contrôle le plus efficace :
  Frédéric connaît le métier et l'historique mieux que l'assistant.

---

## LES CINQ QUESTIONS DE CONTRÔLE

```
   « qu'as-tu relu avant de proposer ca ? »
   « tu l'as mesure ou tu le deduis ? »
   « qu'est-ce qui casse si tu te trompes ? »
   « qu'est-ce que tu n'as pas verifie ? »
   « c'est deja documente quelque part ? »
```

**Si l'assistant ne peut pas répondre aux cinq, il n'est pas prêt à coder.**

---

## HYGIÈNE DE SESSION

**Au début** : relire le plan et la mémoire, annoncer où on en est. *(30 secondes.)*
**À la fin** : commiter, mettre la mémoire à jour, pousser. Ce qui n'est pas écrit disparaît.

---

## LIMITES DE L'ASSISTANT — à garder en tête

| | |
|---|---|
| **Il oublie tout entre les sessions** | sauf ce qui est dans le projet ou dans sa mémoire |
| **Il peut se tromper avec assurance** | le 20/08, une détection `ILIKE` mal écrite lui a fait affirmer **deux fois** l'inverse de la vérité. Son assurance n'est pas un indicateur — **les chiffres le sont** |
| **Il ne voit pas Hektor** | ni l'écran, ni le quotidien des négociateurs, sans qu'on lui ouvre une session |
| **Il ne connaît pas le métier** | il peut dire « 6 propositions sur 11 détachées » ; pas si c'est grave |

---

## CE QUI A MARCHÉ LE 19-20/08 — à reproduire

- **Mesurer avant de conclure** : l'alignement des identifiants a été fait après 6 mesures de
  pré-vol, dont « 0 collision » — et il s'est passé sans incident sur 341 394 lignes.
- **L'essai à blanc** : la même transaction exécutée puis annulée, avec les comptes réels.
- **La preuve sur 10 cas** avant la masse.
- **Le run complet derrière**, pour prouver que le cycle tient.

## CE QUI A RATÉ — à ne pas reproduire

- **Proposer avant de lire** : trois mécanismes qualifiés d'erreur alors qu'ils étaient analysés,
  corrigés en partie et sciemment contournés. Les notes existaient.
- **Conclure d'une mauvaise mesure** : `%update app_contact_search_current%` ne matche pas
  `update public.app_contact_search_current`.
- **Oublier les cas voisins** : traiter « la recherche modifiée » sans traiter « la recherche
  supprimée ».
- **Proposer un nettoyage sans inventaire** : aurait détruit 6 propositions sur 11, app-only,
  non reconstructibles.

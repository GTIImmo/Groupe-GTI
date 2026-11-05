-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER PARTENAIRES · D-1 — LE MÉTIER CHOISI À LA CRÉATION ENTRE AU REGISTRE      05/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §22.
--
-- LE DÉFAUT (D-1, essai du 04/11) : un partenaire créé dans l'app avec un métier (Syndic…) le perd. Le worker l'envoie à
-- Hektor, qui l'ignore (« Non défini »), et RIEN ne l'écrit chez nous. Or le métier vit CHEZ NOUS SEULEMENT (décision D2
-- de Frédéric, 04/11) : c'est notre registre, app_partenaire_metier, qui doit le recevoir.
--
-- CE QUE FAIT CE PATCH — ADDITIF, derrière l'interrupteur 'partenaire_metier_a_la_creation' (posé « off ») :
--   un déclencheur sur app_console_job, SEULEMENT à l'insertion d'un travail create_hektor_contact d'un PARTENAIRE
--   (contact_kind = partenaire) dont la charge porte un métier (partner_job_id) et notre numéro (app_identite) : il écrit
--   la ligne du registre (source « ecran », auteur = celui qui crée), dans la MÊME transaction que la création.
--   Correspondance code Hektor → métier = celle de la nuit (registre_partenaires_reprise.py, METIER_HEKTOR) + 2 notaire et
--   6 autre ; 7 Collaborateur et 16 « À supprimer » n'écrivent RIEN ; un code inconnu n'écrit rien.
--   Un métier déjà actif pour ce contact n'est pas doublé (index unique app_partenaire_metier_actif_uidx).
--   ⚠ Il ne fait JAMAIS échouer une création : une erreur devient un WARNING.
--   ⚠ Aucune fonction existante n'est retouchée (app_create_contact_optimistic, empreinte 278d5570…, reste telle quelle).
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'partenaire_metier_a_la_creation';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'partenaire_metier_a_la_creation';
-- RETOUR ARRIÈRE : patch_partenaire_metier_creation_2026-11-05_INVERSE.sql (les lignes déjà écrites RESTENT : ce sont
--                  de vrais métiers choisis par un utilisateur).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
    IF to_regclass('public.app_partenaire_metier') IS NULL OR to_regclass('public.app_console_job') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : app_partenaire_metier ou app_console_job absente. Rien n''est ecrit.';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_partenaire_metier_a_la_creation_trg') THEN
        RAISE EXCEPTION '%', 'ARRET : le declencheur app_partenaire_metier_a_la_creation_trg existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regprocedure('public.app_partenaire_metier_a_la_creation_trg()') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction app_partenaire_metier_a_la_creation_trg existe deja. Rien n''est ecrit.';
    END IF;
    -- Les deux contrôles du registre doivent être ceux du 04/11 soir (notaire et transactions acceptés) :
    -- tous les métiers de la correspondance y sont, et la source « ecran » aussi.
    IF md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'public.app_partenaire_metier'::regclass
             AND conname = 'app_partenaire_metier_metier_check')) <> '0d785740173b478f5379c2f396e2f458'
       OR md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'public.app_partenaire_metier'::regclass
             AND conname = 'app_partenaire_metier_source_check')) <> 'e322ef89ef8f343fe0eae8079d500f9c' THEN
        RAISE EXCEPTION '%', 'ARRET : les controles de app_partenaire_metier ont change depuis le 05/11. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 0. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('partenaire_metier_a_la_creation', 'off',
        'Chantier partenaires D-1 05/11/2026 : on = le metier choisi a la creation d''un partenaire dans l''app entre au registre app_partenaire_metier (source ecran), dans la meme transaction (voir supabase/patch_partenaire_metier_creation_2026-11-05.sql). off = comportement d''avant (le metier n''arrive nulle part chez nous).',
        now())
on conflict (key) do nothing;

-- 1. LA FONCTION DU DÉCLENCHEUR
create function public.app_partenaire_metier_a_la_creation_trg()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $fonction$
declare
  v_on      boolean;
  v_code    text;
  v_contact text;
  v_metier  text;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'partenaire_metier_a_la_creation';
  if not coalesce(v_on, false) then return null; end if;
  begin
    if lower(trim(coalesce(new.payload_json->>'contact_kind', ''))) <> 'partenaire' then return null; end if;
    v_code := nullif(trim(coalesce(new.payload_json->>'partner_job_id', '')), '');
    v_contact := nullif(trim(coalesce(new.payload_json->>'app_identite', '')), '');
    if v_code is null or v_contact is null then return null; end if;
    -- La correspondance de la nuit (METIER_HEKTOR) + 2 notaire, 6 autre. 7 et 16 : rien.
    v_metier := case v_code
      when '1' then 'promoteur'      when '2' then 'notaire'        when '3' then 'agent_immobilier'
      when '4' then 'diagnostiqueur' when '5' then 'syndic'         when '6' then 'autre'
      when '8' then 'societe'        when '15' then 'apporteur'     when '17' then 'administration'
      when '18' then 'societe'       when '19' then 'banque'        when '20' then 'mandataire'
      when '21' then 'autre'         when '22' then 'agent_immobilier' when '23' then 'technicien'
      else null end;
    if v_metier is null then return null; end if;
    insert into public.app_partenaire_metier (contact_id, metier, source, confirme_le, confirme_par, ecrit_par)
    select v_contact, v_metier, 'ecran', now(), new.requested_by, new.requested_by
     where not exists (select 1 from public.app_partenaire_metier m
                        where m.contact_id = v_contact and m.metier = v_metier and m.retire_le is null);
  exception when others then
    raise warning 'partenaire_metier_a_la_creation : metier non ecrit pour le travail % (%)', new.id, sqlerrm;
  end;
  return null;
end
$fonction$;

revoke all on function public.app_partenaire_metier_a_la_creation_trg() from public, anon, authenticated;

-- 2. LE DÉCLENCHEUR : seulement à l'insertion d'un travail de création de contact
create trigger app_partenaire_metier_a_la_creation_trg
  after insert on public.app_console_job
  for each row
  when (new.job_type = 'create_hektor_contact')
  execute function public.app_partenaire_metier_a_la_creation_trg();

COMMIT;

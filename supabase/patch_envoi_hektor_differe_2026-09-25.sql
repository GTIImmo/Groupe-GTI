-- L'ENVOI VERS HEKTOR DEVIENT UN ETAT, PLUS UNE CONDITION D'EXISTENCE
--                                                                     25/09/2026
-- AUJOURD'HUI : ajouter un document ou une photo depuis l'app envoie A HEKTOR D'ABORD,
-- et la ligne n'existe qu'une fois qu'Hektor a confirme. Si Hektor ne repond pas, rien
-- n'existe nulle part. A la coupure, ajouter un document CESSERA de fonctionner.
--
-- Les contacts, les annonces et les recherches ne fonctionnent pas comme ca : l'app
-- ecrit chez elle, marque la ligne « a envoyer », et un worker la pousse quand il peut
-- (app_contact_pending, app_annonce_pending, app_search_pending). Documents et photos
-- sont les deux seules entites a ne pas avoir ce filet. Remarque de Frederic, 25/09.
--
-- CE PATCH POSE L'ETAT, RIEN D'AUTRE. Purement additif et DORMANT : tant que le front
-- ne cree pas de ligne lui-meme, aucune n'aura de statut et le comportement est inchange.
--
--   envoi_hektor_statut :  NULL       la ligne vient de Hektor, rien a envoyer
--                          a_envoyer  creee par l'app, pas encore chez Hektor
--                          envoye     confirmee chez Hektor
--                          echec      Hektor a refuse ou n'a pas repondu
--
-- ⚠ VERIFIE AVANT D'ECRIRE : une ligne SANS numero Hektor survit a la synchro de nuit.
--   Les deux nettoyages (upsertConsoleDocuments et upsertConsolePhotos) ne suppriment
--   que des lignes qui ONT un numero Hektor devenu obsolete. C'etait le risque principal
--   du chantier ; il est ecarte.
--
-- Reversible :
--   alter table public.app_console_document drop column envoi_hektor_statut, drop column envoi_hektor_erreur, drop column envoi_hektor_at;
--   alter table public.app_console_photo    drop column envoi_hektor_statut, drop column envoi_hektor_erreur, drop column envoi_hektor_at;

begin;

alter table public.app_console_document
    add column if not exists envoi_hektor_statut text,
    add column if not exists envoi_hektor_erreur text,
    add column if not exists envoi_hektor_at     timestamptz;

alter table public.app_console_photo
    add column if not exists envoi_hektor_statut text,
    add column if not exists envoi_hektor_erreur text,
    add column if not exists envoi_hektor_at     timestamptz;

comment on column public.app_console_document.envoi_hektor_statut is
    'NULL = vient de Hektor. a_envoyer / envoye / echec = nee dans l''app (25/09/2026). '
    'La ligne existe AVANT la confirmation de Hektor, comme pour les contacts.';
comment on column public.app_console_photo.envoi_hektor_statut is
    'NULL = vient de Hektor. a_envoyer / envoye / echec = nee dans l''app (25/09/2026).';

-- Index PARTIELS : ils ne portent que sur ce qui reste a faire, donc quelques lignes,
-- jamais les 44 516 documents ni les 444 431 photos a venir.
create index if not exists idx_app_console_document_envoi_a_faire
    on public.app_console_document (envoi_hektor_at)
 where envoi_hektor_statut in ('a_envoyer', 'echec');

create index if not exists idx_app_console_photo_envoi_a_faire
    on public.app_console_photo (envoi_hektor_at)
 where envoi_hektor_statut in ('a_envoyer', 'echec');

-- GARDE-FOU : aucune ligne existante ne doit avoir gagne un statut. Le patch est
-- dormant par construction -- si ce n'est pas le cas, c'est qu'il fait autre chose
-- que ce qui est annonce.
do $$
declare v_doc bigint; v_pho bigint;
begin
    select count(*) into v_doc from public.app_console_document where envoi_hektor_statut is not null;
    select count(*) into v_pho from public.app_console_photo    where envoi_hektor_statut is not null;
    raise notice 'documents avec statut = %, photos avec statut = % (attendu : 0 et 0)', v_doc, v_pho;
    if v_doc > 0 or v_pho > 0 then
        raise exception 'REFUS : le patch devrait etre dormant, % document(s) et % photo(s) portent deja un statut', v_doc, v_pho;
    end if;
end $$;

commit;

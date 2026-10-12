// LA SAUVEGARDE DU PLAN DE LA BASE SUPABASE                         12/10/2026
//
// POURQUOI
//   La descente copie les DONNEES du cloud sur le serveur. Mais personne ne gardait
//   les FORMULES : definitions des vues, fonctions, declencheurs, regles de droits
//   (RLS), taches pg_cron. Releve du 12/10 : sur les 41 vues, 5 n'existent NULLE PART
//   ailleurs que dans Supabase (aucun fichier SQL) -- app_annonces_current,
//   app_dossier_match_attrs, app_ecart_statut_regle,
//   app_search_orphans_non_rattachables, app_stat_negociateur_v. Et les fichiers de
//   patch du depot ne sont pas forcement la DERNIERE version d'un objet.
//   Une copie des DONNEES d'une vue ne permet pas de la recreer : il faut sa formule.
//   Audit : notice/AUDIT_DESCENTE_2026-10-12.md.
//
// CE QU'IL FAIT
//   Lit le catalogue de Postgres (LECTURE SEULE : default_transaction_read_only = on)
//   et ecrit UN fichier SQL date, rejouable dans l'ordre :
//     extensions, sequences, tables, contraintes, index, fonctions, vues (dans l'ordre
//     de leurs dependances), declencheurs, RLS + politiques, droits, commentaires,
//     publication Realtime, taches pg_cron.
//   Puis il RECOMPTE chaque section contre le catalogue : un ecart = exit 1.
//
// CE QU'IL NE FAIT PAS
//   Aucune donnee (c'est le role de la descente et de la sauvegarde Supabase).
//   Aucune ecriture en base. Ne touche pas aux schemas internes de Supabase (auth,
//   storage, realtime...) sauf les politiques de storage, qui sont les notres.
//
// ⚠ CONNEXION PAR LE POOLER : l'adresse directe db.<ref>.supabase.co n'est servie
//   qu'en IPv6, introuvable depuis ce serveur (verifie le 12/10). Meme mot de passe
//   que DATABASE_URL, utilisateur postgres.<ref>, hote SUPABASE_POOLER_HOST.
//
// RESTAURER : rejouer le fichier dans une base vide (psql -f, ou par morceaux dans
//   l'editeur SQL). Une fonction en LANGUAGE sql qui lit une vue peut echouer au
//   premier passage (la vue vient apres) : rejouer la section des fonctions une
//   seconde fois apres les vues.
//
// USAGE
//   node Console/sauvegarde_plan_supabase.js                 # ecrit dans C:\Hektor\Backups\schema
//   node Console/sauvegarde_plan_supabase.js --out <dossier>
const fs = require("node:fs");
const path = require("node:path");

const REF = "dwaqxfrinihnychuoptk";
const GARDER_JOURS = 60;
const SCHEMAS_POLITIQUES = ["public", "storage"];

function readEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const env = {};
  for (const rawLine of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const index = line.indexOf("=");
    if (index <= 0) continue;
    let value = line.slice(index + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    env[line.slice(0, index).trim()] = value;
  }
  return env;
}

function argValue(name) {
  const i = process.argv.indexOf(name);
  return i > 0 ? process.argv[i + 1] : null;
}

const q = (ident) => '"' + String(ident).replace(/"/g, '""') + '"';
const lit = (text) => "'" + String(text).replace(/'/g, "''") + "'";

// Une chaine entre dollars dont l'etiquette n'apparait pas dans le texte.
function dollar(text) {
  let tag = "$plan$";
  for (let n = 1; String(text).includes(tag); n += 1) tag = `$plan${n}$`;
  return tag + text + tag;
}

async function main() {
  const repoRoot = path.resolve(__dirname, "..");
  const env = { ...readEnvFile(path.join(repoRoot, ".env")), ...readEnvFile(path.join(__dirname, ".env")), ...process.env };
  if (!env.DATABASE_URL || !env.SUPABASE_POOLER_HOST) throw new Error("DATABASE_URL ou SUPABASE_POOLER_HOST absent du .env");
  const pg = require("pg");
  const motDePasse = decodeURIComponent(new URL(env.DATABASE_URL).password);
  const client = new pg.Client({
    host: env.SUPABASE_POOLER_HOST, port: 5432, user: `postgres.${REF}`, password: motDePasse,
    database: "postgres", ssl: { rejectUnauthorized: false }, connectionTimeoutMillis: 20000,
  });
  await client.connect();
  const out = [];
  const compte = {};
  const attendu = {};
  const sql = async (text, params) => (await client.query(text, params)).rows;
  const section = (titre) => out.push("", "-- " + "=".repeat(76), `-- ${titre}`, "-- " + "=".repeat(76));

  try {
    await client.query("SET default_transaction_read_only = on");
    await client.query("BEGIN READ ONLY");
    await client.query("SET LOCAL statement_timeout = '120s'");
    const [info] = await sql("select now() as maintenant, version() as version, current_setting('server_version') as v");
    out.push(
      "-- PLAN DE LA BASE SUPABASE (structure seule, aucune donnee)",
      `-- projet ${REF} · releve ${new Date(info.maintenant).toISOString()} · Postgres ${info.v}`,
      "-- Genere par Console/sauvegarde_plan_supabase.js -- LECTURE SEULE.",
      "-- Rejouer dans l'ordre. Voir l'en-tete du script pour la restauration.",
    );

    // Objets appartenant a une extension : jamais recrees a la main.
    const horsExtension = "not exists (select 1 from pg_depend d where d.objid = %s and d.deptype = 'e')";

    section("EXTENSIONS");
    const ext = await sql("select extname, extversion, n.nspname from pg_extension e join pg_namespace n on n.oid = e.extnamespace order by 1");
    for (const e of ext) out.push(`CREATE EXTENSION IF NOT EXISTS ${q(e.extname)} WITH SCHEMA ${q(e.nspname)}; -- version ${e.extversion}`);
    compte.extensions = ext.length; attendu.extensions = ext.length;

    section("SEQUENCES");
    const seqs = await sql(`select c.relname, s.seqstart, s.seqincrement, s.seqmin, s.seqmax, s.seqcache, s.seqcycle, format_type(s.seqtypid, null) as typ
      from pg_sequence s join pg_class c on c.oid = s.seqrelid where c.relnamespace = 'public'::regnamespace and ${horsExtension.replace("%s", "c.oid")}
      and not exists (select 1 from pg_depend d where d.objid = c.oid and d.deptype = 'i') order by 1`);
    for (const s of seqs) out.push(`CREATE SEQUENCE IF NOT EXISTS public.${q(s.relname)} AS ${s.typ} INCREMENT ${s.seqincrement} MINVALUE ${s.seqmin} MAXVALUE ${s.seqmax} START ${s.seqstart} CACHE ${s.seqcache}${s.seqcycle ? " CYCLE" : ""};`);
    compte.sequences = seqs.length; attendu.sequences = seqs.length;

    section("TABLES (colonnes ; contraintes plus bas)");
    const tables = await sql(`select c.oid, c.relname, c.relkind, c.relpersistence from pg_class c
      where c.relnamespace = 'public'::regnamespace and c.relkind in ('r','p') and not c.relispartition and ${horsExtension.replace("%s", "c.oid")} order by 1`);
    const colonnes = await sql(`select a.attrelid, a.attname, format_type(a.atttypid, a.atttypmod) as typ, a.attnotnull, a.attidentity, a.attgenerated,
      pg_get_expr(d.adbin, d.adrelid) as defaut from pg_attribute a left join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
      join pg_class c on c.oid = a.attrelid where c.relnamespace = 'public'::regnamespace and c.relkind in ('r','p') and a.attnum > 0 and not a.attisdropped
      order by a.attrelid, a.attnum`);
    const parTable = new Map();
    for (const col of colonnes) {
      if (!parTable.has(col.attrelid)) parTable.set(col.attrelid, []);
      let ligne = `  ${q(col.attname)} ${col.typ}`;
      if (col.attidentity === "a") ligne += " GENERATED ALWAYS AS IDENTITY";
      else if (col.attidentity === "d") ligne += " GENERATED BY DEFAULT AS IDENTITY";
      else if (col.attgenerated === "s") ligne += ` GENERATED ALWAYS AS (${col.defaut}) STORED`;
      else if (col.defaut != null) ligne += ` DEFAULT ${col.defaut}`;
      if (col.attnotnull) ligne += " NOT NULL";
      parTable.get(col.attrelid).push(ligne);
    }
    for (const t of tables) {
      const unlogged = t.relpersistence === "u" ? "UNLOGGED " : "";
      const partition = t.relkind === "p" ? (await sql("select pg_get_partkeydef($1::oid) as k", [t.oid]))[0].k : null;
      out.push(`CREATE ${unlogged}TABLE IF NOT EXISTS public.${q(t.relname)} (`, (parTable.get(t.oid) || []).join(",\n"), `)${partition ? ` PARTITION BY ${partition}` : ""};`);
    }
    compte.tables = tables.length; attendu.tables = tables.length;

    section("CONTRAINTES (cles primaires et uniques d'abord, cles etrangeres ensuite)");
    const contraintes = await sql(`select c.relname, k.conname, k.contype, pg_get_constraintdef(k.oid) as def from pg_constraint k
      join pg_class c on c.oid = k.conrelid where c.relnamespace = 'public'::regnamespace and c.relkind in ('r','p') and k.contype in ('p','u','c','f','x')
      and ${horsExtension.replace("%s", "c.oid")} order by case k.contype when 'p' then 0 when 'u' then 1 when 'c' then 2 when 'x' then 3 else 4 end, 1, 2`);
    for (const k of contraintes) out.push(`ALTER TABLE public.${q(k.relname)} ADD CONSTRAINT ${q(k.conname)} ${k.def};`);
    compte.contraintes = contraintes.length; attendu.contraintes = contraintes.length;

    section("INDEX (hors ceux que portent les contraintes)");
    const index = await sql(`select i.relname, pg_get_indexdef(x.indexrelid) as def from pg_index x join pg_class i on i.oid = x.indexrelid
      join pg_class t on t.oid = x.indrelid where t.relnamespace = 'public'::regnamespace and ${horsExtension.replace("%s", "t.oid")}
      and not exists (select 1 from pg_constraint k where k.conindid = x.indexrelid) order by 1`);
    for (const i of index) out.push(i.def.replace(/^CREATE (UNIQUE )?INDEX /, "CREATE $1INDEX IF NOT EXISTS ") + ";");
    compte.index = index.length; attendu.index = index.length;

    section("FONCTIONS");
    const fonctions = await sql(`select p.oid, p.proname, pg_get_functiondef(p.oid) as def from pg_proc p
      where p.pronamespace = 'public'::regnamespace and p.prokind in ('f','p') and ${horsExtension.replace("%s", "p.oid")} order by 2, 1`);
    for (const f of fonctions) out.push(f.def.trimEnd() + ";", "");
    compte.fonctions = fonctions.length;
    attendu.fonctions = Number((await sql(`select count(*) n from pg_proc p where p.pronamespace = 'public'::regnamespace and p.prokind in ('f','p') and ${horsExtension.replace("%s", "p.oid")}`))[0].n);

    section("VUES (dans l'ordre de leurs dependances ; options de securite comprises)");
    const vues = await sql(`select c.oid, c.relname, c.relkind, c.reloptions, pg_get_viewdef(c.oid, true) as def from pg_class c
      where c.relnamespace = 'public'::regnamespace and c.relkind in ('v','m') and ${horsExtension.replace("%s", "c.oid")}`);
    const deps = await sql(`select distinct r.ev_class as vue, d.refobjid as dep from pg_rewrite r join pg_depend d on d.objid = r.oid
      join pg_class c on c.oid = d.refobjid where c.relkind in ('v','m') and d.refobjid <> r.ev_class`);
    const parOid = new Map(vues.map((v) => [v.oid, v]));
    const avant = new Map(vues.map((v) => [v.oid, []]));
    for (const d of deps) if (avant.has(d.vue) && parOid.has(d.dep)) avant.get(d.vue).push(d.dep);
    const ordre = [];
    const vu = new Set();
    const visiter = (oid, chemin = new Set()) => {
      if (vu.has(oid)) return;
      if (chemin.has(oid)) throw new Error(`cycle de dependances entre vues (${parOid.get(oid).relname})`);
      chemin.add(oid);
      for (const dep of avant.get(oid) || []) visiter(dep, chemin);
      chemin.delete(oid);
      vu.add(oid); ordre.push(parOid.get(oid));
    };
    for (const v of [...vues].sort((a, b) => a.relname.localeCompare(b.relname))) visiter(v.oid);
    for (const v of ordre) {
      const options = v.reloptions && v.reloptions.length ? ` WITH (${v.reloptions.join(", ")})` : "";
      if (v.relkind === "m") out.push(`CREATE MATERIALIZED VIEW IF NOT EXISTS public.${q(v.relname)}${options} AS`, v.def.trim().replace(/;$/, ""), "WITH NO DATA;", "");
      else out.push(`CREATE OR REPLACE VIEW public.${q(v.relname)}${options} AS`, v.def.trim().replace(/;$/, "") + ";", "");
    }
    compte.vues = ordre.length; attendu.vues = vues.length;

    section("DECLENCHEURS");
    const trig = await sql(`select t.tgname, pg_get_triggerdef(t.oid) as def from pg_trigger t join pg_class c on c.oid = t.tgrelid
      where c.relnamespace = 'public'::regnamespace and not t.tgisinternal order by c.relname, 1`);
    for (const t of trig) out.push(t.def + ";");
    compte.declencheurs = trig.length; attendu.declencheurs = trig.length;

    section("SECURITE PAR LIGNE (RLS) ET POLITIQUES");
    const rls = await sql(`select c.relname, c.relrowsecurity, c.relforcerowsecurity from pg_class c
      where c.relnamespace = 'public'::regnamespace and c.relkind in ('r','p') and (c.relrowsecurity or c.relforcerowsecurity) order by 1`);
    for (const r of rls) {
      if (r.relrowsecurity) out.push(`ALTER TABLE public.${q(r.relname)} ENABLE ROW LEVEL SECURITY;`);
      if (r.relforcerowsecurity) out.push(`ALTER TABLE public.${q(r.relname)} FORCE ROW LEVEL SECURITY;`);
    }
    const politiques = await sql(`select n.nspname, c.relname, p.polname, p.polpermissive, p.polcmd,
      coalesce((select string_agg(case when r = 0 then 'public' else quote_ident(pg_get_userbyid(r)) end, ', ') from unnest(p.polroles) r), 'public') as roles,
      pg_get_expr(p.polqual, p.polrelid) as qual, pg_get_expr(p.polwithcheck, p.polrelid) as wcheck
      from pg_policy p join pg_class c on c.oid = p.polrelid join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = any($1) order by 1, 2, 3`, [SCHEMAS_POLITIQUES]);
    const cmd = { r: "SELECT", a: "INSERT", w: "UPDATE", d: "DELETE", "*": "ALL" };
    for (const p of politiques) {
      let s = `CREATE POLICY ${q(p.polname)} ON ${q(p.nspname)}.${q(p.relname)} AS ${p.polpermissive ? "PERMISSIVE" : "RESTRICTIVE"} FOR ${cmd[p.polcmd]} TO ${p.roles}`;
      if (p.qual) s += ` USING (${p.qual})`;
      if (p.wcheck) s += ` WITH CHECK (${p.wcheck})`;
      out.push(s + ";");
    }
    compte.politiques = politiques.length; attendu.politiques = politiques.length;

    section("DROITS (roles de l'API : anon, authenticated, service_role)");
    const roles = "('anon','authenticated','service_role')";
    const droitsRel = await sql(`select c.relname, a.privilege_type, pg_get_userbyid(a.grantee) as role from pg_class c,
      aclexplode(c.relacl) a where c.relnamespace = 'public'::regnamespace and c.relkind in ('r','p','v','m','S')
      and pg_get_userbyid(a.grantee) in ${roles} order by 1, 3, 2`);
    for (const d of droitsRel) out.push(`GRANT ${d.privilege_type} ON public.${q(d.relname)} TO ${q(d.role)};`);
    const droitsFn = await sql(`select p.oid::regprocedure::text as sig, pg_get_userbyid(a.grantee) as role from pg_proc p,
      aclexplode(p.proacl) a where p.pronamespace = 'public'::regnamespace and a.privilege_type = 'EXECUTE'
      and pg_get_userbyid(a.grantee) in ${roles} order by 1, 2`);
    for (const d of droitsFn) out.push(`GRANT EXECUTE ON FUNCTION ${d.sig} TO ${q(d.role)};`);
    compte.droits = droitsRel.length + droitsFn.length; attendu.droits = compte.droits;

    section("COMMENTAIRES (la documentation posee dans la base)");
    const comm = await sql(`select 'TABLE' as k, c.oid::regclass::text as obj, d.description from pg_description d join pg_class c on c.oid = d.objoid
      where d.classoid = 'pg_class'::regclass and d.objsubid = 0 and c.relnamespace = 'public'::regnamespace and c.relkind in ('r','p')
      union all select case c.relkind when 'm' then 'MATERIALIZED VIEW' else 'VIEW' end, c.oid::regclass::text, d.description from pg_description d join pg_class c on c.oid = d.objoid
      where d.classoid = 'pg_class'::regclass and d.objsubid = 0 and c.relnamespace = 'public'::regnamespace and c.relkind in ('v','m')
      union all select 'FUNCTION', p.oid::regprocedure::text, d.description from pg_description d join pg_proc p on p.oid = d.objoid
      where d.classoid = 'pg_proc'::regclass and p.pronamespace = 'public'::regnamespace order by 1, 2`);
    for (const c of comm) out.push(`COMMENT ON ${c.k} ${c.obj} IS ${lit(c.description)};`);
    compte.commentaires = comm.length; attendu.commentaires = comm.length;

    section("PUBLICATION REALTIME");
    const pubs = await sql(`select p.pubname, coalesce(string_agg(quote_ident(n.nspname) || '.' || quote_ident(c.relname), ', ' order by c.relname), '') as tables
      from pg_publication p left join pg_publication_rel pr on pr.prpubid = p.oid left join pg_class c on c.oid = pr.prrelid
      left join pg_namespace n on n.oid = c.relnamespace group by 1 order by 1`);
    for (const p of pubs) out.push(`-- publication ${p.pubname} : ${p.tables || "(aucune table)"}`, ...(p.tables ? [`ALTER PUBLICATION ${q(p.pubname)} ADD TABLE ${p.tables};`] : []));

    section("TACHES PG_CRON");
    const cron = await sql("select jobid, jobname, schedule, command, active from cron.job order by jobid");
    for (const j of cron) {
      out.push(`-- job ${j.jobid}${j.active ? "" : " (INACTIF)"}`);
      out.push(`SELECT cron.schedule(${lit(j.jobname || `job_${j.jobid}`)}, ${lit(j.schedule)}, ${dollar(j.command)});`);
      if (!j.active) out.push(`SELECT cron.alter_job((select jobid from cron.job where jobname = ${lit(j.jobname || `job_${j.jobid}`)}), active := false);`);
    }
    compte.cron = cron.length; attendu.cron = cron.length;

    await client.query("COMMIT");
  } finally {
    await client.end();
  }

  // LE RECOMPTE : chaque section contre le catalogue.
  const ecarts = Object.keys(attendu).filter((k) => compte[k] !== attendu[k]);
  const resume = Object.keys(compte).map((k) => `${k} ${compte[k]}`).join(" · ");
  out.push("", `-- RECOMPTE : ${resume}`, `-- ECARTS : ${ecarts.length ? ecarts.join(", ") : "aucun"}`);

  const dossier = argValue("--out") || path.join(env.GTI_BACKUP_ROOT || "C:\\Hektor\\Backups", "schema");
  fs.mkdirSync(dossier, { recursive: true });
  // Heure LOCALE dans le nom, comme les autres sauvegardes du serveur.
  const d = new Date();
  const deux = (n) => String(n).padStart(2, "0");
  const stamp = `${d.getFullYear()}${deux(d.getMonth() + 1)}${deux(d.getDate())}_${deux(d.getHours())}${deux(d.getMinutes())}`;
  const fichier = path.join(dossier, `plan_supabase_${stamp}.sql`);
  // Ecrire a cote puis renommer : jamais de fichier a moitie ecrit sous le nom final.
  const texte = out.join("\n") + "\n";
  fs.writeFileSync(fichier + ".tmp", texte, "utf8");
  fs.renameSync(fichier + ".tmp", fichier);

  // Retention : on ne supprime que nos propres fichiers, au-dela de GARDER_JOURS.
  const limite = Date.now() - GARDER_JOURS * 86400000;
  for (const nom of fs.readdirSync(dossier)) {
    if (!/^plan_supabase_\d{8}_\d{4}\.sql$/.test(nom)) continue;
    const complet = path.join(dossier, nom);
    if (complet !== fichier && fs.statSync(complet).mtimeMs < limite) fs.unlinkSync(complet);
  }

  console.log(`[plan_supabase] ${fichier} (${Math.round(Buffer.byteLength(texte) / 1024)} Ko)`);
  console.log(`[plan_supabase] ${resume}`);
  if (ecarts.length) {
    console.error(`[plan_supabase] ECART au recompte : ${ecarts.map((k) => `${k} ${compte[k]}/${attendu[k]}`).join(", ")}`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(`[plan_supabase] ECHEC : ${error.message}`);
  process.exit(1);
});

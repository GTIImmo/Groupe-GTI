const fs = require("node:fs");
const path = require("node:path");

function readEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const env = {};
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const index = line.indexOf("=");
    if (index <= 0) continue;
    const key = line.slice(0, index).trim();
    let value = line.slice(index + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    env[key] = value;
  }
  return env;
}

function maskDatabaseUrl(databaseUrl) {
  try {
    const parsed = new URL(databaseUrl);
    if (parsed.password) parsed.password = "***";
    return parsed.toString();
  } catch {
    return "DATABASE_URL presente, format non affichable";
  }
}

async function main() {
  let pg;
  try {
    pg = require("pg");
  } catch {
    throw new Error(
      "Module 'pg' manquant. Installe-le une fois avec: cd Console && npm.cmd install pg"
    );
  }

  const repoRoot = path.resolve(__dirname, "..");
  const env = {
    ...readEnvFile(path.join(repoRoot, ".env")),
    ...readEnvFile(path.join(__dirname, ".env")),
    ...process.env,
  };

  const databaseUrl = env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("DATABASE_URL introuvable dans .env ou dans les variables systeme.");
  }

  const sqlFile = process.argv[2]
    ? path.resolve(process.cwd(), process.argv[2])
    : path.join(repoRoot, "supabase", "patch_console_create_draft_annonce_2026-05-15.sql");

  if (!fs.existsSync(sqlFile)) {
    throw new Error(`Fichier SQL introuvable: ${sqlFile}`);
  }

  const sql = fs.readFileSync(sqlFile, "utf8");
  if (!sql.trim()) {
    throw new Error(`Fichier SQL vide: ${sqlFile}`);
  }

  console.log(`Base: ${maskDatabaseUrl(databaseUrl)}`);
  console.log(`SQL : ${sqlFile}`);

  // ═══ L'HOTE DIRECT NE REPOND PLUS QU'EN IPv6 ═══                  14/09/2026
  //
  // CONSTAT : `getaddrinfo ENOTFOUND db.<ref>.supabase.co`. Supabase a retire
  // l'IPv4 des connexions DIRECTES ; cette machine n'a pas de route IPv6, donc
  // le lanceur echouait avant meme d'ouvrir le fichier SQL. Ce n'est pas une
  // panne passagere, c'est le nouvel etat du reseau.
  //
  // LE CHEMIN QUI RESTE est le POOLER, qui garde une adresse IPv4 :
  //     aws-0-<region>.pooler.supabase.com   utilisateur postgres.<ref>
  // Region et reference sont DEDUITES de l'adresse directe, jamais devinees --
  // et si la deduction echoue, on ne bascule pas : on rend l'erreur d'origine.
  //
  // ⚠ ON N'AFFICHE JAMAIS L'ADRESSE COMPLETE. maskDatabaseUrl masque le mot de
  //   passe, et toute erreur est re-emise SANS son message brut : le 14/09, un
  //   script d'essai a fait afficher le mot de passe par Node lui-meme, en
  //   echouant sur une URL entre guillemets. Une erreur qui recopie son entree
  //   est une fuite.
  function versLePooler(url, hote) {
    try {
      const u = new URL(url);
      const m = u.hostname.match(/^db\.([a-z0-9]+)\.supabase\.co$/i);
      if (!m) return null;
      u.hostname = hote;
      // Format Supavisor : l'utilisateur porte la reference du projet.
      u.username = `postgres.${m[1]}`;
      return u.toString();
    } catch {
      return null;
    }
  }

  async function tenter(url) {
    const client = new pg.Client({
      connectionString: url,
      ssl: { rejectUnauthorized: false },
      statement_timeout: 120000,
      query_timeout: 120000,
      connectionTimeoutMillis: 20000,
    });
    await client.connect();
    try {
      await client.query(sql);
    } finally {
      await client.end();
    }
  }

  try {
    await tenter(databaseUrl);
    console.log("Migration appliquee avec succes.");
    return;
  } catch (erreur) {
    const reseau = ["ENOTFOUND", "EAI_AGAIN", "ENETUNREACH", "ETIMEDOUT"]
      .includes(erreur && erreur.code);
    if (!reseau) throw erreur;
    console.log(`Hote direct injoignable (${erreur.code}) -- l'IPv4 y a ete retiree.`);
  }

  // La region n'est pas devinable : on la prend dans .env si elle y est, sinon on
  // essaie celles ou Supabase heberge nos projets. Une region fausse echoue vite
  // et proprement (le nom ne resout pas), elle n'ecrit rien.
  // ⚠ NI LE PREFIXE NI LA REGION NE SE DEVINENT. `aws-0-` et `aws-1-` resolvent
  //   TOUS LES DEUX pour la meme region (mesure du 14/09) : seule la bonne paire
  //   connait notre projet, l'autre repond « tenant not found ». On les essaie
  //   donc, et `SUPABASE_POOLER_HOST` dans .env coupe court a l'essai.
  const regions = [env.SUPABASE_REGION, "eu-west-2", "eu-west-3", "eu-central-1"]
    .filter(Boolean);
  const hotes = env.SUPABASE_POOLER_HOST
    ? [env.SUPABASE_POOLER_HOST]
    : regions.flatMap((r) => [`aws-0-${r}.pooler.supabase.com`,
                              `aws-1-${r}.pooler.supabase.com`]);
  for (const hote of hotes) {
    const url = versLePooler(databaseUrl, hote);
    if (!url) break;
    try {
      await tenter(url);
      console.log(`Migration appliquee avec succes, via ${hote}.`);
      if (!env.SUPABASE_POOLER_HOST) {
        console.log(`Pour aller droit au but : SUPABASE_POOLER_HOST=${hote} dans .env.`);
      }
      return;
    } catch (erreur) {
      const code = (erreur && erreur.code) || "";
      const message = String((erreur && erreur.message) || "");
      // « tenant not found » = mauvais couple prefixe/region, pas une panne.
      if (/tenant|not found/i.test(message)
          || ["ENOTFOUND", "EAI_AGAIN", "ENETUNREACH", "ETIMEDOUT"].includes(code)) continue;
      // Une erreur SQL ou d'authentification n'est pas un probleme de region :
      // on s'arrete la plutot que de rejouer la migration sur d'autres hotes.
      throw erreur;
    }
  }
  throw new Error(
    "Aucun chemin vers la base depuis cette machine : l'hote direct est en IPv6 "
    + "seul, et aucun pooler essaye ne connait le projet. Deux issues : poser "
    + "SUPABASE_POOLER_HOST dans .env (la chaine exacte se lit dans le tableau de "
    + "bord Supabase, rubrique Connect), ou appliquer le patch par l'outil "
    + "Supabase -- c'est ce qui a servi le 14/09 et cela marche.");
}

main().catch((error) => {
  console.error(`Erreur: ${error.message}`);
  process.exit(1);
});

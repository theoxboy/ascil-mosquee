#!/usr/bin/env node
// Crée le compte superadmin (un seul) ou réinitialise son mot de passe.
// Le mot de passe est haché ICI, sur votre machine : il n'est jamais envoyé en clair à Cloudflare.
//
//   node scripts/create-superadmin.mjs --sql              affiche le SQL à coller dans la console D1
//   node scripts/create-superadmin.mjs --local            base locale (tests)
//   node scripts/create-superadmin.mjs --remote           base en ligne (wrangler connecté)
//   ajouter --reset : nouveau mot de passe pour un compte existant
//
// Le SQL affiché ne contient que l'empreinte du mot de passe, jamais le mot de passe.
// Pour un usage non interactif (tests) : ASCIL_SA_USER, ASCIL_SA_PASSWORD, ASCIL_SA_NAME, ASCIL_SA_EMAIL.
import { pbkdf2Sync, randomBytes } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import readline from 'node:readline';

const args = process.argv.slice(2);
const sqlOnly = args.includes('--sql');
const target = args.includes('--remote') ? '--remote' : args.includes('--local') ? '--local' : null;
const reset = args.includes('--reset');
if (!target && !sqlOnly) {
  console.error('Précisez --sql (SQL pour la console D1), --local (base de test) ou --remote (base en ligne).');
  process.exit(1);
}

function ask(question, hidden = false) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
    if (hidden) {
      rl._writeToOutput = (s) => { if (s.includes(question)) rl.output.write(s); else rl.output.write('*'.repeat(s.length ? 1 : 0)); };
    }
    rl.question(question, (a) => { rl.close(); if (hidden) process.stdout.write('\n'); resolve(a); });
  });
}

const username = (process.env.ASCIL_SA_USER || await ask('Identifiant (ex. admin.ascil) : ')).trim();
if (!/^[A-Za-z0-9._-]{3,64}$/.test(username)) {
  console.error('Identifiant invalide : 3 à 64 caractères, lettres, chiffres, point, tiret ou souligné.');
  process.exit(1);
}
const name = (process.env.ASCIL_SA_NAME ?? (reset ? '' : await ask('Nom affiché (facultatif) : '))).trim().slice(0, 80);
const email = (process.env.ASCIL_SA_EMAIL ?? (reset ? '' : await ask('Courriel (facultatif) : '))).trim().slice(0, 120);
if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { console.error('Courriel invalide.'); process.exit(1); }
let password = process.env.ASCIL_SA_PASSWORD;
if (!password) {
  password = await ask('Mot de passe (12 caractères minimum) : ', true);
  const again = await ask('Confirmez le mot de passe : ', true);
  if (password !== again) { console.error('Les deux mots de passe ne correspondent pas.'); process.exit(1); }
}
if (password.length < 12) { console.error('Mot de passe trop court : 12 caractères minimum.'); process.exit(1); }

const ITER = 100000; // identique à functions/_lib/auth.js
const salt = randomBytes(16);
const dk = pbkdf2Sync(password, salt, ITER, 32, 'sha256');
const hash = `pbkdf2_sha256$${ITER}$${salt.toString('base64')}$${dk.toString('base64')}`;
const q = (s) => `'${String(s).replace(/'/g, "''")}'`;
const now = new Date().toISOString();

const sql = reset
  ? `UPDATE admins SET password_hash = ${q(hash)}, password_changed_at = ${q(now)} WHERE username = ${q(username)} COLLATE NOCASE;
SELECT changes() AS updated;
DELETE FROM admin_sessions WHERE admin_id = (SELECT id FROM admins WHERE username = ${q(username)} COLLATE NOCASE);`
  : `INSERT INTO admins (username, email, password_hash, role, display_name, created_at, password_changed_at)
SELECT ${q(username)}, ${email ? q(email) : 'NULL'}, ${q(hash)}, 'superadmin', ${name ? q(name) : 'NULL'}, ${q(now)}, ${q(now)}
WHERE NOT EXISTS (SELECT 1 FROM admins WHERE role = 'superadmin');
SELECT id, username, email, role, created_at FROM admins WHERE role = 'superadmin';`;

if (sqlOnly) {
  console.log('\n-- Copiez tout ce qui suit dans la console D1 « ascil-mosquee » :\n');
  console.log(sql);
  process.exit(0);
}

const dir = mkdtempSync(join(tmpdir(), 'ascil-sa-'));
const file = join(dir, 'sa.sql');
writeFileSync(file, sql, { mode: 0o600 });
try {
  const root = join(dirname(fileURLToPath(import.meta.url)), '..');
  const out = execFileSync('npx', ['-y', 'wrangler@4', 'd1', 'execute', 'ascil-mosquee', target, '--file', file, '--json'],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] });
  const results = JSON.parse(out);
  const rows = results.at(-1)?.results ?? [];
  if (reset) {
    const upd = results.find((r) => r.results?.[0] && 'updated' in r.results[0])?.results[0].updated;
    console.log(upd ? 'Mot de passe changé. Toutes les sessions de ce compte sont fermées.' : `Aucun compte « ${username} » trouvé.`);
  } else if (rows.length && rows[0].username.toLowerCase() === username.toLowerCase()) {
    console.log(`Compte superadmin prêt : ${rows[0].username}`);
  } else {
    console.log(`Un superadmin existe déjà (${rows[0]?.username}). Rien n'a été créé. Utilisez --reset pour changer son mot de passe.`);
  }
} finally {
  rmSync(dir, { recursive: true, force: true });
}

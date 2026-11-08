// Formulaires créés dans le panneau (étape M5, tables custom_forms et form_entries).
// Toute définition passe par cleanForm() ; toute réponse de visiteur par cleanEntry(),
// qui ne garde que les champs connus du formulaire et vérifie chacun selon son type.

import { error } from './http.js';

export const FIELD_TYPES = {
  texte: 'Texte court',
  paragraphe: 'Texte long',
  courriel: 'Courriel',
  telephone: 'Téléphone',
  nombre: 'Nombre',
  date: 'Date',
  liste: 'Liste déroulante',
  choix: 'Choix unique',
  cases: 'Cases à cocher',
};
export const WITH_OPTIONS = ['liste', 'choix', 'cases'];
export const ENTRY_STATUSES = ['nouveau', 'lu', 'traite'];
export const MAX_FIELDS = 30;
export const MIN_FILL_MS = 3000;
export const NO_TABLE = 'Les tables des formulaires n’existent pas encore. Appliquez la migration 0011 dans la console D1, puis réessayez.';
export const noTable = (e) => /no such table/i.test(String(e && e.message));

const MAIL_RE = /^[^@\s<>"]+@[^@\s<>"]+\.[^@\s<>"]{2,}$/;
const PHONE_RE = /^[+()\d][\d\s().+-]{6,24}$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const ID_RE = /^[a-z0-9]{1,12}$/;

const oneLine = (v, max) => (typeof v === 'string' ? v.replace(/[\u0000-\u001f\u007f]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max) : '');
const multiLine = (v, max) => (typeof v === 'string'
  ? v.replace(/\r\n?/g, '\n').replace(/[\u0000-\u0009\u000b-\u001f\u007f]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim().slice(0, max)
  : '');

export const MAX_LEN = { texte: 300, paragraphe: 5000, courriel: 200, telephone: 30, nombre: 30, date: 10, liste: 80, choix: 80, cases: 80 };

export function cleanFields(input) {
  const out = [];
  const seen = new Set();
  for (const f of (Array.isArray(input) ? input : []).slice(0, MAX_FIELDS)) {
    if (!f || typeof f !== 'object' || !FIELD_TYPES[f.type]) continue;
    let id = typeof f.id === 'string' && ID_RE.test(f.id) ? f.id : '';
    if (!id || seen.has(id)) {
      let n = out.length + 1;
      while (seen.has('c' + n)) n += 1;
      id = 'c' + n;
    }
    seen.add(id);
    const field = { id, type: f.type, label: oneLine(f.label, 120), aide: oneLine(f.aide, 200), requis: f.requis === true };
    if (WITH_OPTIONS.includes(f.type)) {
      const opts = (Array.isArray(f.options) ? f.options : []).map((o) => oneLine(o, 80)).filter(Boolean);
      field.options = Array.from(new Set(opts)).slice(0, 30);
    }
    out.push(field);
  }
  return out;
}

export function cleanForm(body, { partial = false } = {}) {
  const v = {};
  if (!partial || body.title !== undefined) {
    const title = oneLine(body.title, 120);
    if (title.length < 2) return { error: 'Donnez un titre au formulaire (2 caractères minimum).' };
    v.title = title;
  }
  if (body.intro !== undefined) v.intro = multiLine(body.intro, 1000);
  if (body.fields !== undefined) {
    v.fields = cleanFields(body.fields);
    const bad = v.fields.find((f) => !f.label);
    if (bad) return { error: 'Chaque champ a besoin d’un libellé (la question posée au visiteur).' };
    const noOpt = v.fields.find((f) => WITH_OPTIONS.includes(f.type) && !f.options.length);
    if (noOpt) return { error: `Le champ « ${noOpt.label} » a besoin d’au moins un choix (un par ligne).` };
  }
  if (body.bouton !== undefined) v.bouton = oneLine(body.bouton, 40) || 'Envoyer';
  if (body.merci !== undefined) v.merci = multiLine(body.merci, 600);
  if (body.open !== undefined) v.open = body.open === false || body.open === 0 ? 0 : 1;
  return { values: v };
}

export function rowToForm(r) {
  let fields = [];
  try { fields = JSON.parse(r.fields || '[]'); } catch { fields = []; }
  return {
    id: r.id, title: r.title, intro: r.intro, fields, bouton: r.bouton || 'Envoyer', merci: r.merci,
    open: !!r.open, createdAt: r.created_at, updatedAt: r.updated_at,
    ...(r.total !== undefined ? { total: r.total || 0, nouveaux: r.nouveaux || 0 } : {}),
  };
}

export function rowToEntry(r) {
  let data = {};
  try { data = JSON.parse(r.data || '{}'); } catch { data = {}; }
  return { id: r.id, formId: r.form_id, data, page: r.page_slug, status: r.status, createdAt: r.created_at };
}

// Réponse d'un visiteur (FormData) -> { value } ou { code, message, field }.
// value = { idDuChamp: { l: libellé au moment de l'envoi, v: valeur } }
export function cleanEntry(form, fd) {
  const value = {};
  for (const f of form.fields) {
    const name = 'c_' + f.id;
    let v;
    if (f.type === 'cases') {
      const picked = fd.getAll(name).map((x) => oneLine(String(x), 80)).filter((x) => f.options.includes(x));
      v = Array.from(new Set(picked)).join(', ');
    } else {
      const raw = fd.get(name);
      const s = typeof raw === 'string' ? raw : '';
      v = f.type === 'paragraphe' ? multiLine(s, MAX_LEN.paragraphe) : oneLine(s, MAX_LEN[f.type] || 300);
      if (s.length > (MAX_LEN[f.type] || 300) + 10) return { code: 'invalid', message: `La réponse « ${f.label} » est trop longue.`, field: f.id };
    }
    if (!v) {
      if (f.requis) return { code: 'missing', message: `Remplissez le champ « ${f.label} ».`, field: f.id };
      continue;
    }
    if (f.type === 'courriel' && !MAIL_RE.test(v)) return { code: 'invalid', message: `Le courriel de « ${f.label} » n’est pas valide (exemple : nom@exemple.com).`, field: f.id };
    if (f.type === 'telephone' && !PHONE_RE.test(v)) return { code: 'invalid', message: `Le numéro de « ${f.label} » n’est pas valide (exemple : 418 555-1234).`, field: f.id };
    if (f.type === 'nombre' && !Number.isFinite(Number(v.replace(',', '.')))) return { code: 'invalid', message: `« ${f.label} » doit être un nombre.`, field: f.id };
    if (f.type === 'date' && (!DATE_RE.test(v) || isNaN(Date.parse(v)))) return { code: 'invalid', message: `« ${f.label} » doit être une date.`, field: f.id };
    if ((f.type === 'liste' || f.type === 'choix') && !f.options.includes(v)) return { code: 'invalid', message: `Choisissez une réponse proposée pour « ${f.label} ».`, field: f.id };
    value[f.id] = { l: f.label, v };
  }
  if (!Object.keys(value).length) return { code: 'missing', message: 'Le formulaire est vide. Remplissez au moins un champ.' };
  return { value };
}

// Messages affichés sur la page après un envoi (?r=<code>).
export const RESULT_MESSAGES = {
  missing: 'Il manque une réponse obligatoire. Remplissez les champs marqués d’un astérisque, puis envoyez à nouveau.',
  invalid: 'Une réponse n’est pas au bon format. Vérifiez les courriels, téléphones, nombres et dates, puis envoyez à nouveau.',
  too_fast: 'Envoi trop rapide. Relisez vos réponses, puis envoyez à nouveau.',
  too_many: 'Trop d’envois depuis cette connexion. Réessayez dans 15 minutes.',
  closed: 'Ce formulaire est fermé : il n’accepte plus de réponses.',
  server: 'Votre réponse n’a pas pu être enregistrée. Réessayez dans un instant.',
};

export const LIST_SQL = `SELECT f.*,
  (SELECT COUNT(*) FROM form_entries e WHERE e.form_id = f.id) AS total,
  (SELECT COUNT(*) FROM form_entries e WHERE e.form_id = f.id AND e.status = 'nouveau') AS nouveaux
  FROM custom_forms f`;

// Formulaire :id -> { row } ou { response } (erreur prête à renvoyer).
export async function findForm(env, raw) {
  const id = Number(raw);
  if (!Number.isInteger(id) || id < 1) return { response: error(404, 'not_found', 'Ce formulaire n’existe pas.') };
  try {
    const row = await env.DB.prepare(`${LIST_SQL} WHERE f.id = ?`).bind(id).first();
    if (!row) return { response: error(404, 'not_found', 'Ce formulaire n’existe pas, ou a déjà été supprimé.') };
    return { row };
  } catch (e) {
    if (noTable(e)) return { response: error(503, 'no_table', NO_TABLE) };
    throw e;
  }
}

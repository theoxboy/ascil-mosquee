// « Créer une page » : règles partagées par les routes /api/admin/pages (et, à l'étape 5c,
// par l'affichage public /p/<slug>). Tout ce qui entre en base passe par cleanPage().
import { error } from './http.js';
import { PAGE_FILES } from './settings.js';

export const ROLES = ['superadmin', 'editor'];
export const VISIBILITIES = ['draft', 'published', 'private'];
const LAYOUTS = ['site', 'blank'];
const WIDTHS = ['normal', 'large', 'full'];
const BUTTON_STYLES = ['or', 'vert', 'contour'];
const MAX_BLOCKS = 50;

// Lien : 2 à 60 caractères, minuscules sans accent, chiffres et tirets simples.
export const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
export function slugError(slug) {
  if (typeof slug !== 'string' || slug.length < 2 || slug.length > 60 || !SLUG_RE.test(slug)) {
    return 'Le lien doit faire 2 à 60 caractères : lettres minuscules sans accent, chiffres et tirets (ex. ramadan-2027).';
  }
  return null;
}

// « Inscriptions Ramadan 2027 » -> « inscriptions-ramadan-2027 »
export function slugify(text) {
  return String(text || '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
    .slice(0, 60).replace(/-+$/g, '') || 'page';
}

// Premier lien libre à partir de base (base, base-2, base-3…), sans compter la page exceptId.
export async function uniqueSlug(db, base, exceptId = 0) {
  for (let n = 1; n < 1000; n++) {
    const suffix = n === 1 ? '' : `-${n}`;
    const candidate = base.slice(0, 60 - suffix.length).replace(/-+$/g, '') + suffix;
    if (!(await slugTaken(db, candidate, exceptId))) return candidate;
  }
  throw new Error('Aucun lien libre trouvé');
}

// Un lien est pris s'il appartient à une autre page. Une ancienne adresse (redirection) d'une
// autre page ne bloque pas : la nouvelle page la récupère et la redirection est supprimée.
export async function slugTaken(db, slug, exceptId = 0) {
  const row = await db.prepare('SELECT id FROM custom_pages WHERE slug = ? AND id != ?').bind(slug, exceptId).first();
  return !!row;
}

const str = (v, max) => (typeof v === 'string' ? v.replace(/\r\n/g, '\n').trim().slice(0, max) : '');

function cleanLink(l) {
  if (!l || typeof l !== 'object') return { type: 'none' };
  if (l.type === 'page' && Object.prototype.hasOwnProperty.call(PAGE_FILES, l.page)) return { type: 'page', page: l.page };
  if (l.type === 'custom' && typeof l.slug === 'string' && SLUG_RE.test(l.slug) && l.slug.length <= 60) return { type: 'custom', slug: l.slug };
  if (l.type === 'url' && typeof l.url === 'string' && /^https?:\/\/\S{3,}$/i.test(l.url.trim()) && l.url.length <= 500) {
    return { type: 'url', url: l.url.trim() };
  }
  return { type: 'none' };
}

// Blocs acceptés à cette étape : texte, bouton, tableau. Les autres types sont ignorés.
export function cleanBlocks(input) {
  if (!Array.isArray(input)) return [];
  const out = [];
  for (const b of input.slice(0, MAX_BLOCKS)) {
    if (!b || typeof b !== 'object') continue;
    if (b.type === 'texte') {
      out.push({ type: 'texte', titre: str(b.titre, 200), texte: str(b.texte, 5000) });
    } else if (b.type === 'bouton') {
      out.push({ type: 'bouton', texte: str(b.texte, 80), lien: cleanLink(b.lien), style: BUTTON_STYLES.includes(b.style) ? b.style : 'or' });
    } else if (b.type === 'tableau') {
      const colonnes = (Array.isArray(b.colonnes) ? b.colonnes : []).slice(0, 8).map((c) => str(c, 80));
      const safeColonnes = colonnes.length ? colonnes : [''];
      const n = safeColonnes.length;
      const lignes = (Array.isArray(b.lignes) ? b.lignes : []).slice(0, 100)
        .map((r) => (Array.isArray(r) ? r : []).slice(0, n).map((c) => str(c, 200)))
        .map((r) => r.concat(Array(n - r.length).fill('')));
      const safeLignes = lignes.length ? lignes : [Array(n).fill('')];
      out.push({ type: 'tableau', colonnes: safeColonnes, lignes: safeLignes });
    }
  }
  return out;
}

// Données envoyées par l'éditeur -> { values } prêtes pour la base, ou { error }.
export function cleanPage(body, { partial = false } = {}) {
  const v = {};
  if (!partial || body.title !== undefined) {
    const title = str(body.title, 120);
    if (title.length < 2) return { error: 'Donnez un titre à la page (2 caractères minimum).' };
    v.title = title;
  }
  if (body.slug !== undefined) {
    const slug = typeof body.slug === 'string' ? body.slug.trim().toLowerCase() : '';
    const e = slugError(slug);
    if (e) return { error: e };
    v.slug = slug;
  }
  if (body.blocks !== undefined) v.blocks = cleanBlocks(body.blocks);
  if (body.visibility !== undefined) {
    if (!VISIBILITIES.includes(body.visibility)) return { error: 'Choisissez une visibilité : brouillon, publiée ou lien privé.' };
    v.visibility = body.visibility;
  }
  if (body.layout !== undefined) v.layout = LAYOUTS.includes(body.layout) ? body.layout : 'site';
  if (body.width !== undefined) v.width = WIDTHS.includes(body.width) ? body.width : 'normal';
  if (body.description !== undefined) v.description = str(body.description, 160);
  return { values: v };
}

export function rowToPage(r) {
  if (!r) return null;
  let blocks = [];
  try { blocks = JSON.parse(r.blocks || '[]'); } catch { blocks = []; }
  return {
    id: r.id, slug: r.slug, title: r.title, blocks, visibility: r.visibility, layout: r.layout, width: r.width,
    description: r.description, createdAt: r.created_at, updatedAt: r.updated_at,
    updatedBy: r.updated_by_name || null, url: `/p/${r.slug}`,
  };
}

export const SELECT_PAGE = `SELECT p.*, a.username AS updated_by_name
  FROM custom_pages p LEFT JOIN admins a ON a.id = p.updated_by`;

export async function loadPage(db, rawId) {
  const id = Number(rawId);
  if (!Number.isInteger(id) || id < 1) return { response: error(404, 'not_found', 'Cette page n’existe pas.') };
  const row = await db.prepare(`${SELECT_PAGE} WHERE p.id = ?`).bind(id).first();
  if (!row) return { response: error(404, 'not_found', 'Cette page n’existe pas, ou a déjà été supprimée.') };
  return { row };
}

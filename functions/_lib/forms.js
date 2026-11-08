// Boîte de réception des formulaires publics (table form_messages, migration 0009).
// Aucun courriel n'est envoyé : les demandes se lisent dans le panneau (Contact → Demandes reçues).

// Formulaires acceptés, et leur nom dans le panneau.
export const FORM_SOURCES = {
  contact: 'Contact',
  cours: 'Cours',
  mariages: 'Mariages',
  funerailles: 'Funérailles',
  aide: 'Aide alimentaire',
  femmes: 'Espace femmes',
};
export const FORM_STATUSES = ['nouveau', 'lu', 'traite'];

export const MIN_FILL_MS = 3000; // un humain met plus de 3 secondes à remplir un formulaire
export const LIMIT = 5; // envois par connexion…
export const WINDOW_MS = 15 * 60 * 1000; // …en 15 minutes

const oneLine = (v, max) => (typeof v === 'string' ? v.replace(/[\u0000-\u001f\u007f]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max) : '');
const multiLine = (v, max) => (typeof v === 'string'
  ? v.replace(/\r\n?/g, '\n').replace(/[\u0000-\u0009\u000b-\u001f\u007f]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim().slice(0, max)
  : '');

const MAIL_RE = /^[^@\s<>"]+@[^@\s<>"]+\.[^@\s<>"]{2,}$/;
const PHONE_RE = /^[+()\d][\d\s().+-]{6,24}$/;

// Vérifie et nettoie une demande. Renvoie { value } ou { code, message } (message pour la personne).
export function cleanFormMessage(body) {
  const source = typeof body.source === 'string' && FORM_SOURCES[body.source] ? body.source : '';
  if (!source) return { code: 'invalid_form', message: 'Ce formulaire n’est pas reconnu. Rechargez la page et réessayez.' };
  const nom = oneLine(body.nom, 100);
  const contact = oneLine(body.contact, 120);
  const sujet = oneLine(body.sujet, 120);
  const message = multiLine(body.message, 3000);
  if (nom.length < 2) return { code: 'missing_name', message: 'Indiquez votre nom (2 caractères minimum).' };
  if (!MAIL_RE.test(contact) && !PHONE_RE.test(contact)) {
    return { code: 'missing_contact', message: 'Indiquez un courriel valide (par exemple nom@exemple.com) ou un numéro de téléphone.' };
  }
  if (message.length < 2) return { code: 'missing_message', message: 'Écrivez votre message.' };

  // Champs propres au formulaire : au plus 12 couples libellé → valeur courts.
  let details = null;
  if (body.details && typeof body.details === 'object' && !Array.isArray(body.details)) {
    const out = {};
    for (const [k, v] of Object.entries(body.details).slice(0, 12)) {
      const key = oneLine(k, 60);
      const val = typeof v === 'boolean' ? (v ? 'Oui' : 'Non') : typeof v === 'number' && Number.isFinite(v) ? String(v) : multiLine(v, 500);
      if (key && val) out[key] = val;
    }
    if (Object.keys(out).length) details = out;
  }
  return { value: { source, nom, contact, sujet, message, details } };
}

export function parseDetails(text) {
  if (!text) return null;
  try {
    const d = JSON.parse(text);
    return d && typeof d === 'object' && !Array.isArray(d) ? d : null;
  } catch {
    return null;
  }
}

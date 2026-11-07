// Configuration et valeurs par défaut des réglages du site.

export const DEFAULT_SETTINGS = {
  home: {
    general: {
      email: 'associationrdl.ascil@gmail.com',
      facebook: 'https://www.facebook.com/',
      address: '174 rue Lafontaine',
      city: 'Rivière-du-Loup (Québec)',
      mapUrl: 'https://maps.google.com/?q=174+rue+Lafontaine+Riviere-du-Loup',
    },
    ordre: ['acces', 'campagne', 'annonces', 'bienvenue', 'invitation'],
    on: {
      chargement: true, bandeau: true, compte: true, mail: true, fb: true,
      don: true, langue: true, horaires: true, apropos: true, services: true,
      evenements: true, ressources: true, contact: true, hero: true, priere: true,
      hegirien: true, progression: true, puces: true, acces: true, campagne: true,
      barre: true, annonces: true, bienvenue: true, invitation: true, haut: true,
      pHor: true, pIti: true, pFb: true, pTcom: true, pCciq: true, pMail: true,
    },
    chargement: {
      duration: 'normale',
    },
    hero: {
      h1: 'Page : Horaires du mois',
      h2: 'Page : Faire un don',
    },
    priere: {
      fajr: '06:30',
      lever: '',
      dohr: '',
      jumua: '12:30',
      asr: '',
      maghreb: '',
      icha: '19:00',
    },
    acces: {
      cartes: [
        { id: 'vendredi', on: true, lien: 'Page : Horaires du mois' },
        { id: 'trouver', on: true, lien: 'Page : Contact' },
        { id: 'campagne', on: true, lien: 'Page : Faire un don' },
      ],
    },
    campagne: {
      objectif: 350000,
      recolte: 140000,
      btnInterac: 'Page : Faire un don',
      btnSuivre: 'Page : Campagne en direct',
    },
    annonces: {
      max: 3,
      btnTous: 'Page : Événements',
      items: [
        {
          id: 0,
          date: 'Oct. 2026',
          titre: 'Lancement de la campagne nouveau lieu',
          resume: 'Objectif 350 000 $ pour acquérir et transformer un bâtiment en mosquée.',
          lien: 'Page : Événements',
          on: true,
        },
        {
          id: 1,
          date: '27 mai 2026',
          titre: 'Aïd al-Adha 1447',
          resume: 'Prière célébrée à la salle louée du 15 rue Frontenac.',
          lien: 'Page : Événements',
          on: true,
        },
        {
          id: 2,
          date: '25 avr. 2026',
          titre: 'Journée de parrainage d’orphelins',
          resume: 'Avec l’organisme Soleil des Orphelins, au 174 rue Lafontaine.',
          lien: 'Page : Événements',
          on: true,
        },
      ],
    },
    bienvenue: {
      lien: 'Page : Contact',
    },
    invitation: {
      lien: 'Page : Contact',
    },
    pied: {
      tcom: 'https://www.tcomq.ca/',
      cciq: '',
    },
  },
  event_registration: {
    event_slug: 'iftar-2027',
    event_title: 'Iftar communautaire',
    date_str: 'Samedi 20 février 2027 · 17 h 15',
    location: '174 rue Lafontaine',
    description: 'Repas de rupture du jeûne ouvert à tous : familles, voisins, étudiants. Gratuit, dons bienvenus.',
    total_seats: 120,
    max_per_reg: 6,
    deadline: '2027-02-18',
    is_open: true,
    opt_vege: true,
    opt_code: true,
    opt_agenda: true,
  },
};

export function cleanHomeSettings(input) {
  if (!input || typeof input !== 'object') return DEFAULT_SETTINGS.home;
  const def = DEFAULT_SETTINGS.home;

  const out = {
    general: {
      email: typeof input.general?.email === 'string' ? input.general.email.trim() : def.general.email,
      facebook: typeof input.general?.facebook === 'string' ? input.general.facebook.trim() : def.general.facebook,
      address: typeof input.general?.address === 'string' ? input.general.address.trim() : def.general.address,
      city: typeof input.general?.city === 'string' ? input.general.city.trim() : def.general.city,
      mapUrl: typeof input.general?.mapUrl === 'string' ? input.general.mapUrl.trim() : def.general.mapUrl,
    },
    ordre: Array.isArray(input.ordre) ? input.ordre.filter((x) => def.ordre.includes(x)) : def.ordre,
    on: {},
    chargement: {
      duration: input.chargement?.duration === 'rapide' ? 'rapide' : 'normale',
    },
    hero: {
      h1: typeof input.hero?.h1 === 'string' ? input.hero.h1 : def.hero.h1,
      h2: typeof input.hero?.h2 === 'string' ? input.hero.h2 : def.hero.h2,
    },
    priere: {
      fajr: typeof input.priere?.fajr === 'string' ? input.priere.fajr.trim() : def.priere.fajr,
      lever: typeof input.priere?.lever === 'string' ? input.priere.lever.trim() : def.priere.lever,
      dohr: typeof input.priere?.dohr === 'string' ? input.priere.dohr.trim() : def.priere.dohr,
      jumua: typeof input.priere?.jumua === 'string' ? input.priere.jumua.trim() : def.priere.jumua,
      asr: typeof input.priere?.asr === 'string' ? input.priere.asr.trim() : def.priere.asr,
      maghreb: typeof input.priere?.maghreb === 'string' ? input.priere.maghreb.trim() : def.priere.maghreb,
      icha: typeof input.priere?.icha === 'string' ? input.priere.icha.trim() : def.priere.icha,
    },
    acces: {
      cartes: Array.isArray(input.acces?.cartes) ? input.acces.cartes : def.acces.cartes,
    },
    campagne: {
      objectif: typeof input.campagne?.objectif === 'number' ? Math.max(0, input.campagne.objectif) : (parseInt(input.campagne?.objectif, 10) || def.campagne.objectif),
      recolte: typeof input.campagne?.recolte === 'number' ? Math.max(0, input.campagne.recolte) : (parseInt(input.campagne?.recolte, 10) || 0),
      btnInterac: typeof input.campagne?.btnInterac === 'string' ? input.campagne.btnInterac : def.campagne.btnInterac,
      btnSuivre: typeof input.campagne?.btnSuivre === 'string' ? input.campagne.btnSuivre : def.campagne.btnSuivre,
    },
    annonces: {
      max: [1, 2, 3].includes(input.annonces?.max) ? input.annonces.max : def.annonces.max,
      btnTous: typeof input.annonces?.btnTous === 'string' ? input.annonces.btnTous : def.annonces.btnTous,
      items: Array.isArray(input.annonces?.items) ? input.annonces.items : def.annonces.items,
    },
    bienvenue: {
      lien: typeof input.bienvenue?.lien === 'string' ? input.bienvenue.lien : def.bienvenue.lien,
    },
    invitation: {
      lien: typeof input.invitation?.lien === 'string' ? input.invitation.lien : def.invitation.lien,
    },
    pied: {
      tcom: typeof input.pied?.tcom === 'string' ? input.pied.tcom.trim() : def.pied.tcom,
      cciq: typeof input.pied?.cciq === 'string' ? input.pied.cciq.trim() : def.pied.cciq,
    },
  };

  // On/Off switches
  for (const k of Object.keys(def.on)) {
    out.on[k] = input.on && typeof input.on[k] === 'boolean' ? input.on[k] : def.on[k];
  }

  // Ensure all sections are in ordre
  for (const o of def.ordre) {
    if (!out.ordre.includes(o)) out.ordre.push(o);
  }

  return out;
}

export function cleanEventRegistrationSettings(input) {
  const def = DEFAULT_SETTINGS.event_registration;
  if (!input || typeof input !== 'object') return { ...def };

  return {
    event_slug: typeof input.event_slug === 'string' && input.event_slug.trim() ? input.event_slug.trim().slice(0, 64) : def.event_slug,
    event_title: typeof input.event_title === 'string' && input.event_title.trim() ? input.event_title.trim().slice(0, 120) : def.event_title,
    date_str: typeof input.date_str === 'string' && input.date_str.trim() ? input.date_str.trim().slice(0, 120) : def.date_str,
    location: typeof input.location === 'string' && input.location.trim() ? input.location.trim().slice(0, 160) : def.location,
    description: typeof input.description === 'string' ? input.description.trim().slice(0, 500) : def.description,
    total_seats: typeof input.total_seats === 'number' ? Math.max(1, Math.min(10000, Math.floor(input.total_seats))) : (parseInt(input.total_seats, 10) || def.total_seats),
    max_per_reg: typeof input.max_per_reg === 'number' ? Math.max(1, Math.min(20, Math.floor(input.max_per_reg))) : (parseInt(input.max_per_reg, 10) || def.max_per_reg),
    deadline: typeof input.deadline === 'string' ? input.deadline.trim().slice(0, 20) : def.deadline,
    is_open: typeof input.is_open === 'boolean' ? input.is_open : def.is_open,
    opt_vege: typeof input.opt_vege === 'boolean' ? input.opt_vege : def.opt_vege,
    opt_code: typeof input.opt_code === 'boolean' ? input.opt_code : def.opt_code,
    opt_agenda: typeof input.opt_agenda === 'boolean' ? input.opt_agenda : def.opt_agenda,
  };
}

// « Site entier → Pages publiées » : réglage -> page du site public (versions PC, M- et T-).
// Accueil n'y figure pas : elle ne peut pas être masquée.
export const PAGE_FILES = {
  pg_horaires: 'Horaires', pg_apropos: 'APropos', pg_services: 'Services', pg_dons: 'Dons',
  pg_evenements: 'Evenements', pg_ressources: 'Ressources', pg_contact: 'Contact',
  pg_cours: 'N2-Cours', pg_mariages: 'N2-Mariages', pg_funerailles: 'N2-Funerailles',
  pg_aide: 'N2-AideAlimentaire', pg_femmes: 'N2-EspaceFemmes', pg_khutba: 'N2-Khutba',
  pg_rappel: 'N3-Rappel', pg_campagne: 'N3-Campagne', pg_calendrier: 'N3-Calendrier',
  pg_inscription: 'N3-Inscription', pg_dua: 'N3-Dua',
};

// Tant que rien n'est enregistré, tout reste publié : le site ne change pas tout seul.
DEFAULT_SETTINGS.pages = Object.fromEntries(Object.keys(PAGE_FILES).map((k) => [k, true]));

export function cleanPagesSettings(input) {
  const out = { ...DEFAULT_SETTINGS.pages };
  if (input && typeof input === 'object') {
    for (const k of Object.keys(out)) if (typeof input[k] === 'boolean') out[k] = input[k];
  }
  return out;
}

export async function readPagesSettings(db) {
  const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'pages'").first();
  let saved = null;
  try { saved = row ? JSON.parse(row.value) : null; } catch { saved = null; }
  return cleanPagesSettings(saved);
}

const PAGE_BY_FILE = Object.fromEntries(Object.entries(PAGE_FILES).map(([k, f]) => [f, k]));

// '/M-N2-Cours.dc.html' ou '/N2-Cours.dc' -> 'pg_cours' ; null pour toute autre adresse.
export function pageSettingForPath(path) {
  const m = /^\/(?:M-|T-)?([A-Za-z0-9-]+?)\.dc(?:\.html)?$/.exec(path);
  return m ? PAGE_BY_FILE[m[1]] || null : null;
}

// Date de mise à jour des réglages : toujours au format ISO, comme la migration 0003.
export const nowIso = () => new Date().toISOString();

// Réglages de l'événement ouvert aux inscriptions (une seule lecture, partagée par les routes).
export async function readEventRegistrationSettings(db) {
  try {
    const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'event_registration'").first();
    if (row && row.value) return cleanEventRegistrationSettings(JSON.parse(row.value));
  } catch (err) {
    console.warn('read event_registration error:', err && err.message);
  }
  return { ...DEFAULT_SETTINGS.event_registration };
}

// « Site entier → Saison et langues → Bannière d'alerte » : bande en haut de toutes les pages publiques.
// Désactivée tant que rien n'est enregistré.
DEFAULT_SETTINGS.alert = { on: false, message: '', link: { type: 'none' }, from: '', to: '', tone: 'attention' };
const ALERT_TONES = ['info', 'attention', 'urgent'];
const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

export function cleanAlertSettings(input) {
  const def = DEFAULT_SETTINGS.alert;
  const i = input && typeof input === 'object' ? input : {};
  const day = (v) => (typeof v === 'string' && ISO_DAY.test(v) ? v : '');
  const out = {
    on: typeof i.on === 'boolean' ? i.on : def.on,
    message: typeof i.message === 'string' ? i.message.replace(/\s+/g, ' ').trim().slice(0, 200) : '',
    link: { type: 'none' },
    from: day(i.from),
    to: day(i.to),
    tone: ALERT_TONES.includes(i.tone) ? i.tone : def.tone,
  };
  const l = i.link && typeof i.link === 'object' ? i.link : {};
  if (l.type === 'page' && Object.prototype.hasOwnProperty.call(PAGE_FILES, l.page)) {
    out.link = { type: 'page', page: l.page };
  } else if (l.type === 'url' && typeof l.url === 'string' && /^https?:\/\/[^\s]{3,}$/i.test(l.url.trim()) && l.url.length <= 500) {
    out.link = { type: 'url', url: l.url.trim() };
  }
  // Période à l'envers : on garde le début, on efface la fin plutôt que de ne jamais afficher.
  if (out.from && out.to && out.to < out.from) out.to = '';
  return out;
}

// Clés modifiables par la route générique /api/admin/settings/:key, et par qui.
// « event_registration » n'y figure pas : elle passe par /api/admin/events/settings
// (superadmin et responsable événements), qui la valide.
export const GENERIC_KEYS = {
  home: { roles: ['superadmin', 'editor'], clean: cleanHomeSettings },
  pages: { roles: ['superadmin', 'editor'], clean: cleanPagesSettings },
  alert: { roles: ['superadmin', 'editor'], clean: cleanAlertSettings },
};

// Réglages lisibles publiquement par /api/settings/:key.
export const PUBLIC_KEYS = ['home', 'pages', 'alert'];

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

// Lien d'un bouton de l'accueil : « Page : … » (page du site), « /p/<lien> » (page créée) ou https://….
// Toute autre valeur (ancienne page d'exemple, « Lien externe… » enregistré tel quel, javascript:…)
// revient à la valeur par défaut.
function homeLink(v, def) {
  if (typeof v !== 'string') return def;
  const t = v.trim();
  if (/^Page : [^<>"]{1,60}$/.test(t)) return t;
  if (/^\/p\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(t) && t.length <= 63) return t;
  if (/^https?:\/\/[^\s<>"]{3,}$/i.test(t) && t.length <= 500) return t;
  return def;
}

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
      h1: homeLink(input.hero?.h1, def.hero.h1),
      h2: homeLink(input.hero?.h2, def.hero.h2),
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
      cartes: Array.isArray(input.acces?.cartes)
        ? input.acces.cartes.slice(0, def.acces.cartes.length).map((c, i) => ({
          id: def.acces.cartes[i].id,
          on: typeof c?.on === 'boolean' ? c.on : true,
          lien: homeLink(c?.lien, def.acces.cartes[i].lien),
        }))
        : def.acces.cartes,
    },
    campagne: {
      objectif: typeof input.campagne?.objectif === 'number' ? Math.max(0, input.campagne.objectif) : (parseInt(input.campagne?.objectif, 10) || def.campagne.objectif),
      recolte: typeof input.campagne?.recolte === 'number' ? Math.max(0, input.campagne.recolte) : (parseInt(input.campagne?.recolte, 10) || 0),
      btnInterac: homeLink(input.campagne?.btnInterac, def.campagne.btnInterac),
      btnSuivre: homeLink(input.campagne?.btnSuivre, def.campagne.btnSuivre),
    },
    annonces: {
      max: [1, 2, 3].includes(input.annonces?.max) ? input.annonces.max : def.annonces.max,
      btnTous: homeLink(input.annonces?.btnTous, def.annonces.btnTous),
      items: Array.isArray(input.annonces?.items)
        ? input.annonces.items.slice(0, 10).map((it, i) => ({
          id: typeof it?.id === 'number' ? it.id : i,
          date: typeof it?.date === 'string' ? it.date.slice(0, 40) : '',
          titre: typeof it?.titre === 'string' ? it.titre.slice(0, 160) : '',
          resume: typeof it?.resume === 'string' ? it.resume.slice(0, 400) : '',
          lien: homeLink(it?.lien, 'Page : Événements'),
          on: typeof it?.on === 'boolean' ? it.on : true,
        }))
        : def.annonces.items,
    },
    bienvenue: {
      lien: homeLink(input.bienvenue?.lien, def.bienvenue.lien),
    },
    invitation: {
      lien: homeLink(input.invitation?.lien, def.invitation.lien),
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
  } else if (l.type === 'custom' && typeof l.slug === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(l.slug) && l.slug.length <= 60) {
    out.link = { type: 'custom', slug: l.slug };
  } else if (l.type === 'url' && typeof l.url === 'string' && /^https?:\/\/[^\s]{3,}$/i.test(l.url.trim()) && l.url.length <= 500) {
    out.link = { type: 'url', url: l.url.trim() };
  }
  // Période à l'envers : on garde le début, on efface la fin plutôt que de ne jamais afficher.
  if (out.from && out.to && out.to < out.from) out.to = '';
  // Une bannière sans message ne peut pas être affichée : cohérence garantie entre message vide et « Afficher ».
  if (!out.message) out.on = false;
  return out;
}

// « Site entier → Saison et langues → Mode du site ».
// auto = true : le mode n'est actif qu'entre les dates (bornes incluses) ; auto = false : le mode
// choisi s'applique tout de suite, jusqu'à ce qu'on le change. « normal » = rien de particulier.
DEFAULT_SETTINGS.season = { mode: 'normal', from: '', to: '', auto: true };
const SEASON_MODES = ['normal', 'ramadan', 'aid_fitr', 'aid_adha'];

export function cleanSeasonSettings(input) {
  const i = input && typeof input === 'object' ? input : {};
  const day = (v) => (typeof v === 'string' && ISO_DAY.test(v) ? v : '');
  const out = {
    mode: SEASON_MODES.includes(i.mode) ? i.mode : 'normal',
    from: day(i.from),
    to: day(i.to),
    auto: typeof i.auto === 'boolean' ? i.auto : true,
  };
  if (out.from && out.to && out.to < out.from) out.to = '';
  return out;
}

// « Site entier → Saison et langues → Langues » : langues proposées dans le sélecteur du site.
// Le français est toujours actif. Par défaut, les trois restent visibles (comme avant ce réglage).
DEFAULT_SETTINGS.languages = { fr: true, ar: true, en: true };

export function cleanLanguagesSettings(input) {
  const i = input && typeof input === 'object' ? input : {};
  return {
    fr: true,
    ar: typeof i.ar === 'boolean' ? i.ar : true,
    en: typeof i.en === 'boolean' ? i.en : true,
  };
}

// « Horaires » : réglages de la page publique Horaires (les heures elles-mêmes sont dans la table
// prayer_times, une ligne par jour). Les dates du Ramadan viennent de « Site entier → Mode du site »
// (clé season) ; l'heure de Jumu'a vient du tableau du mois. Valeurs par défaut = page actuelle.
DEFAULT_SETTINGS.horaires = {
  aujourdhui: { on: true, compte: true, hijri: true, lienRappel: true, lienKhutba: true },
  mois: { vendredis: true },
  vendredi: { on: true, avance: 15, conseil: true },
  ramadan: { on: true, suhoor: true, iftar: true, tarawih: false, tarawihHeure: '' },
  aid: {
    on: true, lieu: 'Salle louée — 15 rue Frontenac',
    itineraire: 'https://maps.google.com/?q=15+rue+Frontenac+Riviere-du-Loup',
    fitrDate: '', fitrHeure: '', adhaDate: '', adhaHeure: '',
  },
  qibla: { on: true, degres: '61,6', repere: '' },
};
const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;

export function cleanHorairesSettings(input) {
  const def = DEFAULT_SETTINGS.horaires;
  const i = input && typeof input === 'object' ? input : {};
  const bool = (sec, k) => (typeof i[sec]?.[k] === 'boolean' ? i[sec][k] : def[sec][k]);
  const text = (sec, k, max) => (typeof i[sec]?.[k] === 'string' ? i[sec][k].replace(/\s+/g, ' ').trim().slice(0, max) : def[sec][k]);
  const day = (sec, k) => (typeof i[sec]?.[k] === 'string' && ISO_DAY.test(i[sec][k]) ? i[sec][k] : '');
  const time = (sec, k) => (typeof i[sec]?.[k] === 'string' && HHMM.test(i[sec][k]) ? i[sec][k] : '');
  const avance = Number(i.vendredi?.avance);
  const deg = typeof i.qibla?.degres === 'string' ? i.qibla.degres.trim().replace('.', ',') : def.qibla.degres;
  const degNum = Number(deg.replace(',', '.'));
  const url = typeof i.aid?.itineraire === 'string' ? i.aid.itineraire.trim() : def.aid.itineraire;
  return {
    aujourdhui: { on: bool('aujourdhui', 'on'), compte: bool('aujourdhui', 'compte'), hijri: bool('aujourdhui', 'hijri'),
      lienRappel: bool('aujourdhui', 'lienRappel'), lienKhutba: bool('aujourdhui', 'lienKhutba') },
    mois: { vendredis: bool('mois', 'vendredis') },
    vendredi: { on: bool('vendredi', 'on'),
      avance: Number.isInteger(avance) && avance >= 0 && avance <= 120 ? avance : def.vendredi.avance,
      conseil: bool('vendredi', 'conseil') },
    ramadan: { on: bool('ramadan', 'on'), suhoor: bool('ramadan', 'suhoor'), iftar: bool('ramadan', 'iftar'),
      tarawih: bool('ramadan', 'tarawih'), tarawihHeure: time('ramadan', 'tarawihHeure') },
    aid: {
      on: bool('aid', 'on'), lieu: text('aid', 'lieu', 120),
      itineraire: /^https?:\/\/[^\s<>"]{3,}$/i.test(url) && url.length <= 500 ? url : (url ? def.aid.itineraire : ''),
      fitrDate: day('aid', 'fitrDate'), fitrHeure: time('aid', 'fitrHeure'),
      adhaDate: day('aid', 'adhaDate'), adhaHeure: time('aid', 'adhaHeure'),
    },
    qibla: { on: bool('qibla', 'on'), degres: Number.isFinite(degNum) && degNum >= 0 && degNum < 360 ? deg : def.qibla.degres,
      repere: text('qibla', 'repere', 160) },
  };
}

// Horaires → Langue de la khutba (clé khutba). Une ligne par vendredi (date AAAA-MM-JJ, un vendredi),
// triées par date ; le site montre les vendredis à venir, dans la limite de « nombre ».
export const KHUTBA_LANGUES = ['Français', 'Arabe', 'Anglais', 'Arabe et français'];
export const KHUTBA_TRADUCTIONS = ['Aucune', 'Arabe', 'Français', 'Anglais'];
export const KHUTBA_MODES = ['Résumé imprimé à l’entrée', 'Traduction orale', 'Écran'];
DEFAULT_SETTINGS.khutba = {
  vendredis: [
    { date: '2026-11-06', langue: 'Français', traduction: 'Aucune', imam: '', on: true },
    { date: '2026-11-13', langue: 'Arabe', traduction: 'Français', imam: '', on: true },
  ],
  nombre: 4,
  mode: 'Résumé imprimé à l’entrée',
};

export function cleanKhutbaSettings(input) {
  const def = DEFAULT_SETTINGS.khutba;
  const i = input && typeof input === 'object' ? input : {};
  const seen = new Set();
  const list = (Array.isArray(i.vendredis) ? i.vendredis : def.vendredis)
    .filter((v) => v && typeof v === 'object' && typeof v.date === 'string' && ISO_DAY.test(v.date)
      && new Date(`${v.date}T12:00:00Z`).getUTCDay() === 5)
    .filter((v) => (seen.has(v.date) ? false : (seen.add(v.date), true)))
    .slice(0, 60)
    .map((v) => ({
      date: v.date,
      langue: KHUTBA_LANGUES.includes(v.langue) ? v.langue : 'Arabe',
      traduction: KHUTBA_TRADUCTIONS.includes(v.traduction) ? v.traduction : 'Aucune',
      imam: typeof v.imam === 'string' ? v.imam.replace(/\s+/g, ' ').trim().slice(0, 80) : '',
      on: typeof v.on === 'boolean' ? v.on : true,
    }))
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const nombre = Number(i.nombre);
  return {
    vendredis: list,
    nombre: [2, 4, 6, 8].includes(nombre) ? nombre : def.nombre,
    mode: KHUTBA_MODES.includes(i.mode) ? i.mode : def.mode,
  };
}

// Horaires → Rappel de prière (clé rappel) : prières proposées aux visiteurs, délais, notification.
export const RAPPEL_DELAIS = [5, 10, 15, 30, 60];
DEFAULT_SETTINGS.rappel = {
  prieres: { fajr: true, dohr: false, jumua: true, asr: false, maghreb: false, icha: true },
  delais: [5, 10, 15, 30, 60],
  defaut: 15,
  titre: 'Prière dans {délai}',
  son: true,
  vibration: true,
};

export function cleanRappelSettings(input) {
  const def = DEFAULT_SETTINGS.rappel;
  const i = input && typeof input === 'object' ? input : {};
  const prieres = {};
  Object.keys(def.prieres).forEach((k) => {
    prieres[k] = typeof i.prieres?.[k] === 'boolean' ? i.prieres[k] : def.prieres[k];
  });
  let delais = Array.isArray(i.delais) ? RAPPEL_DELAIS.filter((d) => i.delais.map(Number).includes(d)) : def.delais.slice();
  if (!delais.length) delais = [15];
  const defaut = Number(i.defaut);
  const titre = typeof i.titre === 'string' ? i.titre.replace(/\s+/g, ' ').trim().slice(0, 80) : def.titre;
  return {
    prieres,
    delais,
    defaut: delais.includes(defaut) ? defaut : (delais.includes(def.defaut) ? def.defaut : delais[0]),
    titre: titre || def.titre,
    son: typeof i.son === 'boolean' ? i.son : def.son,
    vibration: typeof i.vibration === 'boolean' ? i.vibration : def.vibration,
  };
}

// À propos → L’association (clé apropos). Les blocs reprennent le contenu d’origine de la page publique.
// Une étape d’histoire sans date reste masquée ; l’équipe n’est publiée qu’avec l’accord écrit et un nom.
const PHOTO_RE = /^data:image\/(?:jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/;
export const PHOTO_MAX = 100000;
DEFAULT_SETTINGS.apropos = {
  presentation: {
    on: true,
    texte: 'L’ASCIL rassemble les musulmanes et les musulmans de Rivière-du-Loup et des environs. Elle tient un lieu de prière au 174 rue Lafontaine, organise la prière du vendredi, les prières de l’Aïd et des activités de solidarité, et accueille les nouveaux arrivants dans la région.',
  },
  valeurs: {
    on: true,
    items: [
      { titre: 'Prier ensemble', texte: 'Les cinq prières quotidiennes et la prière du vendredi (Jumu’a).', on: true },
      { titre: 'Se soutenir', texte: 'Accueil, solidarité et événements caritatifs, comme l’activité avec Soleil des Orphelins d’avril 2026.', on: true },
      { titre: 'S’ancrer ici', texte: 'Une communauté du Bas-Saint-Laurent, membre de la Table de concertation des organisations musulmanes du Québec (TCOM).', on: true },
    ],
  },
  histoire: {
    on: true,
    items: [
      { date: '', titre: 'Fondation de l’association', on: true },
      { date: '', titre: 'Installation au 174 rue Lafontaine', on: true },
      { date: '2026-10-01', titre: 'Lancement du projet de nouveau lieu', on: true },
    ],
  },
  projet: { on: true, btnSoutenir: 'Page : Faire un don', btnSuivre: 'Page : Campagne en direct' },
  equipe: {
    on: false,
    accord: false,
    items: [
      { nom: '', role: 'Président', photo: '', on: true },
      { nom: '', role: 'Imam', photo: '', on: true },
      { nom: '', role: 'Membre du conseil', photo: '', on: true },
    ],
  },
  chiffres: {
    on: true,
    items: [
      { valeur: '≈ 1 100', libelle: 'abonnés à la page Facebook de l’ASCIL', source: 'page Facebook de l’ASCIL', on: true },
      { valeur: '≈ 45', libelle: 'pays d’origine des personnes immigrantes de la région', source: 'données de la MRC de Rivière-du-Loup', on: true },
      { valeur: '2e', libelle: 'le Maghreb, région d’origine la mieux représentée après la France', source: 'données de la MRC de Rivière-du-Loup', on: true },
    ],
  },
};

const oneLine = (v, max) => (typeof v === 'string' ? v.replace(/\s+/g, ' ').trim().slice(0, max) : '');
const boolOr = (v, d) => (typeof v === 'boolean' ? v : d);
function listOf(v, def, max, fn) {
  return (Array.isArray(v) ? v : def).filter((x) => x && typeof x === 'object').slice(0, max).map(fn);
}

export function cleanAproposSettings(input) {
  const def = DEFAULT_SETTINGS.apropos;
  const i = input && typeof input === 'object' ? input : {};
  const part = (k) => (i[k] && typeof i[k] === 'object' ? i[k] : {});
  const pres = part('presentation'), val = part('valeurs'), hist = part('histoire');
  const proj = part('projet'), eq = part('equipe'), chif = part('chiffres');
  const texte = typeof pres.texte === 'string'
    ? pres.texte.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).join('\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, 1500)
    : def.presentation.texte;
  return {
    presentation: { on: boolOr(pres.on, def.presentation.on), texte },
    valeurs: {
      on: boolOr(val.on, def.valeurs.on),
      items: listOf(val.items, def.valeurs.items, 6, (x) => ({ titre: oneLine(x.titre, 80), texte: oneLine(x.texte, 300), on: boolOr(x.on, true) })),
    },
    histoire: {
      on: boolOr(hist.on, def.histoire.on),
      items: listOf(hist.items, def.histoire.items, 12, (x) => ({
        date: typeof x.date === 'string' && ISO_DAY.test(x.date) ? x.date : '',
        titre: oneLine(x.titre, 120),
        on: boolOr(x.on, true),
      })),
    },
    projet: {
      on: boolOr(proj.on, def.projet.on),
      btnSoutenir: homeLink(proj.btnSoutenir, def.projet.btnSoutenir),
      btnSuivre: homeLink(proj.btnSuivre, def.projet.btnSuivre),
    },
    equipe: {
      on: boolOr(eq.on, def.equipe.on),
      accord: boolOr(eq.accord, def.equipe.accord),
      items: listOf(eq.items, def.equipe.items, 8, (x) => ({
        nom: oneLine(x.nom, 80),
        role: oneLine(x.role, 80),
        photo: typeof x.photo === 'string' && x.photo.length <= PHOTO_MAX && PHOTO_RE.test(x.photo) ? x.photo : '',
        on: boolOr(x.on, true),
      })),
    },
    chiffres: {
      on: boolOr(chif.on, def.chiffres.on),
      items: listOf(chif.items, def.chiffres.items, 6, (x) => ({
        valeur: oneLine(x.valeur, 20), libelle: oneLine(x.libelle, 160), source: oneLine(x.source, 120), on: boolOr(x.on, true),
      })),
    },
  };
}

// À propos → Campagne en direct (clé campagne). L’objectif et le montant récolté restent dans
// home.campagne (communs à l’accueil) ; en mode automatique, récolté, donateurs, semaines et
// derniers dons sont calculés à partir de la table donations (functions/_lib/campagne.js).
export const CAMPAGNE_NOMS = ['prenom', 'initiales', 'anonyme'];
DEFAULT_SETTINGS.campagne = {
  donateurs: 0,
  auto: false,
  etapes: {
    on: true,
    items: [
      { seuil: 25, libelle: 'Promesse d’achat signée', on: true },
      { seuil: 50, libelle: 'Inspection et financement', on: true },
      { seuil: 75, libelle: 'Passage chez le notaire', on: true },
      { seuil: 100, libelle: 'Clés du nouveau lieu', on: true },
    ],
  },
  semaines: { on: true, nombre: 8, valeurs: [] },
  derniers: { on: true, nombre: 5, nom: 'prenom', montant: true },
};

// « 12 500 », « 12 500 $ » ou 12500 -> 12500 ; null si ce n'est pas un montant.
export function wholeAmount(v, max) {
  const n = typeof v === 'number' ? v : Number(String(v == null ? '' : v).replace(/[\s  $]/g, '').replace(',', '.'));
  if (!Number.isFinite(n) || n < 0) return null;
  return Math.min(Math.round(n), max);
}

export function cleanCampagneSettings(input) {
  const def = DEFAULT_SETTINGS.campagne;
  const i = input && typeof input === 'object' ? input : {};
  const et = i.etapes && typeof i.etapes === 'object' ? i.etapes : {};
  const se = i.semaines && typeof i.semaines === 'object' ? i.semaines : {};
  const de = i.derniers && typeof i.derniers === 'object' ? i.derniers : {};
  const nombre = Number(se.nombre), dn = Number(de.nombre);
  return {
    donateurs: wholeAmount(i.donateurs, 1000000) ?? def.donateurs,
    auto: boolOr(i.auto, def.auto),
    etapes: {
      on: boolOr(et.on, def.etapes.on),
      items: listOf(et.items, def.etapes.items, 8, (x) => ({
        seuil: Math.max(0, Math.min(100, wholeAmount(x.seuil, 100) ?? 0)), libelle: oneLine(x.libelle, 120), on: boolOr(x.on, true),
      })).sort((a, b) => a.seuil - b.seuil),
    },
    semaines: {
      on: boolOr(se.on, def.semaines.on),
      nombre: [4, 8, 12].includes(nombre) ? nombre : def.semaines.nombre,
      valeurs: (Array.isArray(se.valeurs) ? se.valeurs : def.semaines.valeurs).slice(0, 12).map((v) => wholeAmount(v, 100000000) ?? 0),
    },
    derniers: {
      on: boolOr(de.on, def.derniers.on),
      nombre: [3, 5, 10].includes(dn) ? dn : def.derniers.nombre,
      nom: CAMPAGNE_NOMS.includes(de.nom) ? de.nom : def.derniers.nom,
      montant: boolOr(de.montant, def.derniers.montant),
    },
  };
}

// Services → Tous les services (clé services). Cartes de la page Services, dans l'ordre.
// Trois cartes ont un rôle propre : prieres (heures de Fajr et d'Icha du tableau du mois),
// jumua (heure de Jumu'a, lignes khutba et espace femmes), aid (lieu repris de horaires.aid.lieu,
// Zakat al-Fitr). Les autres sont libres (kind 'libre') et peuvent être ajoutées ou supprimées.
export const SERVICE_KINDS = ['prieres', 'jumua', 'aid', 'libre'];
const SERVICE_BASE = { titre: '', texte: '', icone: 0, saison: false, lien: '', lienTexte: '', khutba: false, femmes: false, zakat: null, zakatAnnee: '', on: true };
DEFAULT_SETTINGS.services = {
  items: [
    { ...SERVICE_BASE, kind: 'prieres', titre: 'Les cinq prières quotidiennes', texte: 'Au 174 rue Lafontaine, tous les jours.', icone: 0,
      lien: 'Page : Horaires du mois', lienTexte: 'Tableau complet des horaires' },
    { ...SERVICE_BASE, kind: 'jumua', titre: 'La prière du vendredi (Jumu’a)', texte: 'Khutba suivie de la prière.', icone: 1, khutba: true, femmes: true },
    { ...SERVICE_BASE, kind: 'libre', titre: 'Ramadan : Iftar et Tarawih', icone: 2, saison: true,
      texte: 'Proposés pendant le mois de Ramadan, avec des dates publiées chaque année dès l’annonce officielle.' },
    { ...SERVICE_BASE, kind: 'aid', titre: 'Les prières de l’Aïd', icone: 3, saison: true, zakat: 15, zakatAnnee: '2025' },
    { ...SERVICE_BASE, kind: 'libre', titre: 'Solidarité et événements caritatifs', icone: 4, lien: 'Page : Événements', lienTexte: 'Voir les événements',
      texte: 'Exemple : la journée de parrainage d’orphelins avec l’organisme Soleil des Orphelins, le 25 avril 2026 au 174 rue Lafontaine.' },
  ],
  autres: { on: true, cours: true, mariages: true, funerailles: true, aide: true, femmes: true, khutba: true },
  equipements: { on: true, fauteuil: true, ablutions: true, parking: true, femmes: false },
  question: { on: true, lien: 'Page : Contact' },
};

export function cleanServicesSettings(input) {
  const def = DEFAULT_SETTINGS.services;
  const i = input && typeof input === 'object' ? input : {};
  const seen = new Set();
  const items = listOf(i.items, def.items, 12, (x) => {
    const kind = SERVICE_KINDS.includes(x.kind) ? x.kind : 'libre';
    const icone = Number(x.icone);
    const zak = x.zakat === null || x.zakat === '' || x.zakat === undefined ? null : wholeAmount(x.zakat, 10000);
    return {
      kind,
      titre: oneLine(x.titre, 80),
      texte: typeof x.texte === 'string' ? x.texte.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).join('\n').trim().slice(0, 400) : '',
      icone: [0, 1, 2, 3, 4].includes(icone) ? icone : 0,
      saison: boolOr(x.saison, false),
      lien: x.lien === '' ? '' : homeLink(x.lien, ''),
      lienTexte: oneLine(x.lienTexte, 60),
      khutba: boolOr(x.khutba, false),
      femmes: boolOr(x.femmes, false),
      zakat: zak,
      zakatAnnee: oneLine(x.zakatAnnee, 12),
      on: boolOr(x.on, true),
    };
  }).filter((x) => (x.kind === 'libre' ? true : (seen.has(x.kind) ? false : (seen.add(x.kind), true))));
  // Les trois cartes à rôle propre existent toujours (masquées si elles avaient disparu).
  for (const k of ['prieres', 'jumua', 'aid']) {
    if (!seen.has(k)) items.push({ ...def.items.find((x) => x.kind === k), on: false });
  }
  const sec = (k) => (i[k] && typeof i[k] === 'object' ? i[k] : {});
  const flags = (k) => Object.fromEntries(Object.keys(def[k]).map((f) => [f, boolOr(sec(k)[f], def[k][f])]));
  return {
    items,
    autres: flags('autres'),
    equipements: flags('equipements'),
    question: { on: boolOr(sec('question').on, def.question.on), lien: homeLink(sec('question').lien, def.question.lien) },
  };
}

// ---------------------------------------------------------------------------------------------
// Pages des services (étapes S3 à S5) : Cours, Mariages, Funérailles, Aide alimentaire, Espace femmes.
// Chaque clé est nettoyée d'après un schéma : ['s', max] une ligne, ['t', max] texte sur plusieurs
// lignes, ['b'] oui/non, ['n', min, max] nombre entier, ['hm'] heure HH:MM, ['date'] AAAA-MM-JJ,
// ['e', [valeurs]] choix, ['set', [valeurs]] plusieurs choix, ['img', max] image réduite,
// ['list', max, {champs}] liste, ['fixed', n, {champs}] liste de longueur fixe, {…} objet.
const HM_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const multi = (v, max) => (typeof v === 'string'
  ? v.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).join('\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, max)
  : '');

function cleanWith(spec, v, d) {
  if (Array.isArray(spec)) {
    const [t, a, b] = spec;
    switch (t) {
      case 's': return typeof v === 'string' ? oneLine(v, a) : d;
      case 't': return typeof v === 'string' ? multi(v, a) : d;
      case 'b': return boolOr(v, d);
      case 'n': {
        if (v === '' || v === null) return d;
        const n = typeof v === 'number' ? v : Number(String(v).replace(',', '.'));
        return Number.isFinite(n) ? Math.min(b, Math.max(a, Math.round(n))) : d;
      }
      case 'hm': return typeof v === 'string' && (v === '' || HM_RE.test(v)) ? v : d;
      case 'date': return typeof v === 'string' && (v === '' || DATE_RE.test(v)) ? v : d;
      case 'e': return a.includes(v) ? v : d;
      case 'set': return Array.isArray(v) ? a.filter((x) => v.includes(x)) : d;
      case 'img': return typeof v === 'string' && (v === '' || (v.length <= a && PHOTO_RE.test(v))) ? v : d;
      case 'list': {
        const tmpl = Array.isArray(d) && d.length ? d[0] : {};
        const src = Array.isArray(v) ? v : d;
        return src.filter((x) => x && typeof x === 'object').slice(0, a).map((x) => cleanWith(b, x, Array.isArray(v) ? itemDefault(b, tmpl) : x));
      }
      case 'fixed': {
        const src = Array.isArray(v) ? v : [];
        return d.map((dx, k) => cleanWith(b, src[k] && typeof src[k] === 'object' ? src[k] : dx, dx));
      }
      default: return d;
    }
  }
  const o = v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  const out = {};
  for (const k of Object.keys(spec)) out[k] = cleanWith(spec[k], o[k], d ? d[k] : undefined);
  return out;
}

// Valeur par défaut d'un nouvel élément de liste : champs vides, interrupteurs comme le modèle.
function itemDefault(spec, tmpl) {
  const out = {};
  for (const k of Object.keys(spec)) {
    const t = Array.isArray(spec[k]) ? spec[k][0] : 'obj';
    out[k] = t === 'b' ? (tmpl[k] !== undefined ? tmpl[k] : true) : t === 'set' ? [] : t === 'n' ? 0 : t === 'e' ? tmpl[k] : t === 'obj' ? itemDefault(spec[k], tmpl[k] || {}) : '';
  }
  return out;
}

const AGES = ['5-8', '9-12', '13-17', 'adulte'];
const NIVEAUX = ['deb', 'int', 'av'];
const JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
const LIST_ITEM = { titre: ['s', 160], on: ['b'] };

export const SERVICE_PAGE_SCHEMAS = {
  cours: {
    annee: ['s', 20], delai: ['e', ['24 h', '48 h', '1 semaine']], essai: ['b'], attente: ['b'], inscriptions: ['b'],
    items: ['list', 30, {
      titre: ['s', 80], matiere: ['e', ['coran', 'arabe']], ages: ['set', AGES], niveaux: ['set', NIVEAUX], jour: ['e', JOURS],
      debut: ['hm'], fin: ['hm'], places: ['n', 0, 999], prix: ['n', 0, 10000], prof: ['s', 80], on: ['b'],
    }],
    infos: { on: ['b'], tarifs: ['t', 400], essai: ['t', 400], lieu: ['s', 80], lieuTexte: ['t', 400] },
  },
  mariages: {
    duree: ['s', 40], delai: ['s', 40],
    etapes: ['list', 10, { titre: ['s', 80], quand: ['s', 40], texte: ['t', 600], on: ['b'] }],
    docs: { on: ['b'], items: ['list', 15, LIST_ITEM] },
    form: { on: ['b'] },
  },
  funerailles: {
    responsable: ['s', 80], telephone: ['s', 30], courriel: ['s', 120], h24: ['b'], rappel911: ['b'],
    etapes: ['list', 10, { titre: ['s', 80], texte: ['t', 600], on: ['b'] }],
    docs: { on: ['b'], items: ['list', 15, LIST_ITEM] },
    charge: { on: ['b'], texte: ['t', 600] },
  },
  aide: {
    form: { on: ['b'], besoins: ['list', 8, { titre: ['s', 40], on: ['b'] }], recup: ['b'], livraison: ['b'], delai: ['e', ['24 h', '48 h', '72 h']] },
    manque: { on: ['b'], items: ['list', 15, { titre: ['s', 60], niveau: ['e', ['tres', 'demande', 'suffisant']], on: ['b'] }] },
    depot: { on: ['b'], adresse: ['s', 120], quand: ['s', 120], note: ['t', 300] },
    argent: { on: ['b'], courriel: ['s', 120], note: ['t', 300] },
  },
  femmes: {
    jours: ['fixed', 7, { on: ['b'], de1: ['hm'], a1: ['hm'], de2: ['hm'], a2: ['hm'] }],
    fermeture: ['date'], plan: ['img', 200000],
    pratique: { on: ['b'], entree: ['s', 160], acces: ['s', 160], ablutions: ['s', 160], jumua: ['s', 160], enfants: ['s', 160], responsable: ['s', 160] },
    regles: { on: ['b'], items: ['list', 15, LIST_ITEM] },
  },
};

const docs = (...t) => t.map((titre) => ({ titre, on: true }));
const fjour = (de1, a1, de2 = '', a2 = '') => ({ on: true, de1, a1, de2, a2 });
DEFAULT_SETTINGS.cours = {
  annee: '2026–2027', delai: '48 h', essai: true, attente: true, inscriptions: true,
  items: [
    { titre: 'Coran — Éveil', matiere: 'coran', ages: ['5-8'], niveaux: ['deb'], jour: 'Samedi', debut: '09:30', fin: '10:30', places: 4, prix: 25, prof: 'Enseignante : Sœur Amina' },
    { titre: 'Coran — Lecture et tajwid', matiere: 'coran', ages: ['9-12'], niveaux: ['deb', 'int'], jour: 'Samedi', debut: '10:45', fin: '12:00', places: 6, prix: 30, prof: 'Enseignant : Frère Youssef' },
    { titre: 'Coran — Mémorisation (hifz)', matiere: 'coran', ages: ['9-12', '13-17'], niveaux: ['av'], jour: 'Dimanche', debut: '10:00', fin: '12:00', places: 2, prix: 35, prof: 'Enseignant : Imam Karim' },
    { titre: 'Arabe — Premiers pas', matiere: 'arabe', ages: ['5-8', '9-12'], niveaux: ['deb'], jour: 'Dimanche', debut: '13:00', fin: '14:30', places: 8, prix: 30, prof: 'Enseignante : Sœur Leïla' },
    { titre: 'Arabe — Ados', matiere: 'arabe', ages: ['13-17'], niveaux: ['int', 'av'], jour: 'Mardi', debut: '18:30', fin: '20:00', places: 5, prix: 35, prof: 'Enseignant : Frère Samir' },
    { titre: 'Coran — Adultes', matiere: 'coran', ages: ['adulte'], niveaux: ['deb', 'int', 'av'], jour: 'Jeudi', debut: '19:30', fin: '21:00', places: 7, prix: 40, prof: 'Enseignant : Imam Karim' },
    { titre: 'Arabe — Adultes débutants', matiere: 'arabe', ages: ['adulte'], niveaux: ['deb'], jour: 'Mercredi', debut: '19:00', fin: '20:30', places: 0, prix: 40, prof: 'Enseignante : Sœur Leïla' },
  ].map((x) => ({ ...x, on: true })),
  infos: {
    on: true,
    tarifs: '−20 % dès le 2e enfant d’une même famille. Personne n’est refusé faute de moyens : parlez-nous-en en toute discrétion.',
    essai: 'Venez 10 minutes avant ; un test de niveau rapide et bienveillant est proposé.',
    lieu: '174 rue Lafontaine', lieuTexte: 'Salle de classe à l’étage ; les parents peuvent attendre dans la salle commune.',
  },
};
DEFAULT_SETTINGS.mariages = {
  duree: 'environ 6 semaines', delai: '3 jours ouvrables',
  etapes: [
    { titre: 'Premier contact', quand: 'Jour 1', texte: 'Remplissez la demande de rendez-vous ci-dessous. L’association vous répond sous 3 jours ouvrables avec une date de rencontre.', on: true },
    { titre: 'Rencontre avec l’imam', quand: 'Semaine 1 à 2', texte: 'Un entretien de 45 minutes avec les deux futurs époux : intentions, conditions du contrat, mahr et questions pratiques.', on: true },
    { titre: 'Documents', quand: 'Semaine 2 à 4', texte: 'Rassemblez les documents de la liste. Cochez-les au fur et à mesure : votre progression s’affiche.', on: true },
    { titre: 'Cérémonie (nikah)', quand: 'Semaine 4 à 6', texte: 'Célébration à la mosquée, en présence du tuteur (wali) et de deux témoins. Prévoyez environ 45 minutes.', on: true },
    { titre: 'Démarches civiles', quand: 'À coordonner', texte: 'Le mariage religieux et le mariage civil sont deux démarches distinctes. L’association vous indique comment les coordonner au Québec.', on: true },
  ],
  docs: {
    on: true,
    items: docs('Pièce d’identité avec photo des deux époux', 'Coordonnées de deux témoins musulmans', 'Accord du tuteur (wali) de l’épouse',
      'Montant ou nature du mahr convenu', 'Certificat de divorce ou de décès du conjoint précédent, s’il y a lieu', 'Preuve des démarches civiles (si déjà faites)'),
  },
  form: { on: true },
};
DEFAULT_SETTINGS.funerailles = {
  responsable: '', telephone: '', courriel: 'associationrdl.ascil@gmail.com', h24: true, rappel911: true,
  etapes: [
    { titre: 'Appelez l’association', texte: 'À tout moment, jour et nuit. Un bénévole vous rappelle en moins de 30 minutes et vous accompagne pour la suite.', on: true },
    { titre: 'Obtenez le constat de décès', texte: 'Il est délivré par le médecin ou l’hôpital. Gardez-en une copie : il sera demandé pour toutes les démarches.', on: true },
    { titre: 'Contactez l’entreprise funéraire', texte: 'L’association vous oriente vers une entreprise qui connaît les rites musulmans (toilette mortuaire, linceul, transport).', on: true },
    { titre: 'Toilette mortuaire et prière de la janaza', texte: 'La toilette (ghusl) est faite par des bénévoles du même sexe. La prière de la janaza a lieu le plus tôt possible, idéalement dans les 24 à 48 heures.', on: true },
    { titre: 'Inhumation', texte: 'Dans la section musulmane d’un cimetière de la région, ou rapatriement si la famille le souhaite. L’association vous aide dans les démarches.', on: true },
  ],
  docs: { on: true, items: docs('Constat de décès', 'Pièce d’identité du défunt', 'Carte d’assurance maladie', 'Coordonnées d’un membre de la famille') },
  charge: { on: true, texte: 'Accompagnement de la famille, organisation de la toilette mortuaire et de la prière de la janaza, mise en relation avec l’entreprise funéraire.' },
};
DEFAULT_SETTINGS.aide = {
  form: { on: true, besoins: docs('Épicerie', 'Produits halal', 'Produits pour bébé', 'Repas du Ramadan'), recup: true, livraison: true, delai: '48 h' },
  manque: {
    on: true,
    items: [
      { titre: 'Riz, pâtes, semoule', niveau: 'tres', on: true }, { titre: 'Huile et conserves', niveau: 'demande', on: true },
      { titre: 'Lait et aliments pour bébé', niveau: 'demande', on: true }, { titre: 'Couches', niveau: 'demande', on: true },
      { titre: 'Produits d’hygiène', niveau: 'tres', on: true },
    ],
  },
  depot: { on: true, adresse: '174 rue Lafontaine', quand: 'Samedi et dimanche, 10 h – 14 h', note: 'Produits non périssables, non ouverts, non périmés.' },
  argent: { on: true, courriel: 'associationrdl.ascil@gmail.com', note: 'Indiquez « aide alimentaire » dans le message.' },
};
DEFAULT_SETTINGS.femmes = {
  jours: [fjour('17:00', '21:30'), fjour('17:00', '21:30'), fjour('17:00', '21:30'), fjour('17:00', '21:30'),
    fjour('11:30', '14:00', '17:00', '21:30'), fjour('09:00', '21:30'), fjour('09:00', '21:30')],
  fermeture: '', plan: '',
  pratique: {
    on: true, entree: 'Porte latérale, côté stationnement, avec sonnette.', acces: 'Rampe d’accès et espace de plain-pied.',
    ablutions: 'Salle d’ablutions réservée aux femmes.', jumua: '30 places. Arrivez vers 12 h 15.',
    enfants: 'Coin calme pour les enfants accompagnés.', responsable: 'associationrdl.ascil@gmail.com',
  },
  regles: {
    on: true,
    items: docs('Tenue couvrante ; des foulards sont prêtés à l’entrée.', 'Téléphones en silencieux pendant la prière.',
      'Les enfants restent accompagnés.', 'Merci de ranger tapis et chaises après les cours.'),
  },
};

const servicePageCleaner = (key) => (input) => cleanWith(SERVICE_PAGE_SCHEMAS[key], input, DEFAULT_SETTINGS[key]);
export const cleanCoursSettings = servicePageCleaner('cours');
export const cleanMariagesSettings = servicePageCleaner('mariages');
export const cleanFuneraillesSettings = servicePageCleaner('funerailles');
export const cleanAideSettings = servicePageCleaner('aide');
export const cleanFemmesSettings = servicePageCleaner('femmes');

// Clés modifiables par la route générique /api/admin/settings/:key, et par qui.
// « event_registration » n'y figure pas : elle passe par /api/admin/events/settings
// (superadmin et responsable événements), qui la valide.
export const GENERIC_KEYS = {
  home: { roles: ['superadmin', 'editor'], clean: cleanHomeSettings },
  pages: { roles: ['superadmin', 'editor'], clean: cleanPagesSettings },
  alert: { roles: ['superadmin', 'editor'], clean: cleanAlertSettings },
  season: { roles: ['superadmin', 'editor'], clean: cleanSeasonSettings },
  languages: { roles: ['superadmin', 'editor'], clean: cleanLanguagesSettings },
  horaires: { roles: ['superadmin', 'editor'], clean: cleanHorairesSettings },
  khutba: { roles: ['superadmin', 'editor'], clean: cleanKhutbaSettings },
  rappel: { roles: ['superadmin', 'editor'], clean: cleanRappelSettings },
  // Photos de l’équipe incluses (réduites dans le panneau) : corps de requête plus grand.
  apropos: { roles: ['superadmin', 'editor'], clean: cleanAproposSettings, maxBytes: 1000000 },
  campagne: { roles: ['superadmin', 'editor'], clean: cleanCampagneSettings },
  services: { roles: ['superadmin', 'editor'], clean: cleanServicesSettings },
  cours: { roles: ['superadmin', 'editor'], clean: cleanCoursSettings },
  mariages: { roles: ['superadmin', 'editor'], clean: cleanMariagesSettings },
  funerailles: { roles: ['superadmin', 'editor'], clean: cleanFuneraillesSettings },
  aide: { roles: ['superadmin', 'editor'], clean: cleanAideSettings },
  // Plan d'accès inclus (image réduite dans le panneau) : corps de requête plus grand.
  femmes: { roles: ['superadmin', 'editor'], clean: cleanFemmesSettings, maxBytes: 400000 },
};

// Réglages lisibles publiquement par /api/settings/:key.
export const PUBLIC_KEYS = ['home', 'pages', 'alert', 'season', 'languages', 'horaires', 'khutba', 'rappel', 'apropos', 'services',
  'cours', 'mariages', 'funerailles', 'aide', 'femmes'];

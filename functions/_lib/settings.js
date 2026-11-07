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

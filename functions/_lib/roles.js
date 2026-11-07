// Rôles et pages autorisées. Une seule source de vérité, utilisée par le middleware et l'API.

export const ROLES = {
  superadmin: { label: 'Superadmin', home: '/SA-Panneau.dc.html' },
  editor: { label: 'Éditeur', home: '/SA-Panneau.dc.html' },
  events: { label: 'Responsable événements', home: '/SA-Evenements.dc.html' },
};

// Rôles que le superadmin peut attribuer (jamais 'superadmin').
export const ASSIGNABLE = ['editor', 'events'];

// Page superadmin -> rôles autorisés. Une page absente de la liste est réservée
// au superadmin et à l'éditeur.
const PAGE_ROLES = {
  'SA-Comptes': ['superadmin'],
  'SA-Evenements': ['superadmin', 'editor', 'events'],
};
const DEFAULT_ROLES = ['superadmin', 'editor'];

export function pageKey(path) {
  const m = /^\/(SA-[A-Za-z]+)(\.dc)?(\.html)?$/.exec(path);
  return m ? m[1] : null;
}

export function canOpenPage(role, key) {
  return (PAGE_ROLES[key] || DEFAULT_ROLES).includes(role);
}

export function homeFor(role) {
  return (ROLES[role] || ROLES.editor).home;
}

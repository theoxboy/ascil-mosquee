# Backend du superadmin (Cloudflare Pages Functions + D1)

Le site statique reste servi depuis la racine du dépôt. L'API vit dans `functions/`,
sur le même domaine : pas de CORS, cookie de session `HttpOnly; Secure; SameSite=Strict`.
Base : D1 `ascil-mosquee`, liée sous le nom `DB` (voir `wrangler.toml` et Pages → Paramètres → Liaisons).

## Feuille de route

| Étape | Contenu | État |
|---|---|---|
| 1 | Compte superadmin (un seul, imposé par la base), sessions, limitation des essais, journal ; connexion et déconnexion ; pages `SA-*` protégées côté serveur | en ligne |
| 2a | Autres comptes à rôle limité (`editor`, `events`), mot de passe provisoire à changer à la 1re connexion, page `SA-Comptes.html` | en ligne |
| 2 | Réglages des widgets de l'accueil (`site_settings` clé `home`) ; « Enregistrer » du panneau Accueil ; l'accueil public les applique | en ligne |
| 2b | Statistiques réelles (`page_views`, `/api/admin/stats`) et bandeau du panneau Accueil | en ligne |
| 2c | Inscriptions aux événements (`event_registrations`, clé `event_registration`), panneau Événements, export CSV | en ligne |
| Site entier | « Pages publiées » (clé `pages`) ; « Compte et sécurité » avec les vraies données de session | en ligne |
| Site entier | « Bannière d'alerte » (clé `alert`) : bande en haut de toutes les pages publiques, avec message, lien, période et couleur | fait, à pousser |
| Site entier | « Saison et langues » : mode Ramadan / Aïd et langues | à faire |
| 3 | Pages créées dans le superadmin (`custom_pages`, blocs, lien `/p/<slug>`, brouillon / publiée) | à faire |
| 4 | Horaires, annonces, dons : API sur les tables existantes `prayer_times`, `announcements`, `donations`, `events` | à faire |

Les tables existantes ne sont jamais recréées : on les complète avec `ALTER TABLE`.

## Migrations

| Fichier | Contenu |
|---|---|
| `0001_superadmin_auth.sql` | complète `admins` (identifiant, mot de passe haché…), un seul superadmin ; `admin_sessions`, `login_attempts`, `audit_log` |
| `0002_comptes_roles.sql` | `admins.must_change_password`, `admins.created_by` |
| `0003_site_settings.sql` | `site_settings (key, value JSON, updated_at ISO, updated_by)` + clé `home` |
| `0004_page_views.sql` | `page_views (path, viewed_date, count)` : visites anonymes, sans cookie ni IP |
| `0005_event_registrations.sql` | `event_registrations` + clé `event_registration` |
| `0006_dates_iso_et_limites.sql` | `site_settings.updated_at` remis au format ISO ; `rate_limits` (limite des inscriptions publiques) |

Les migrations sont appliquées à la main dans la console D1. Après chaque application,
enregistrer la ligne correspondante dans `d1_migrations`, sinon `wrangler d1 migrations apply --remote`
tenterait de la rejouer (un `ALTER TABLE` rejoué échoue) :

```sql
INSERT OR IGNORE INTO d1_migrations (name) VALUES ('0006_dates_iso_et_limites.sql');
```

## Réglages (`site_settings`)

| Clé | Écrite par | Route | Lue par le public |
|---|---|---|---|
| `home` | superadmin, editor | `PUT /api/admin/settings/home` | `GET /api/settings/home` |
| `pages` | superadmin, editor | `PUT /api/admin/settings/pages` | `GET /api/settings/pages` + middleware |
| `alert` | superadmin, editor | `PUT /api/admin/settings/alert` | `GET /api/settings/alert` |
| `event_registration` | superadmin, events | `PUT /api/admin/events/settings` | `GET /api/events/registration-info` |

La route générique `/api/admin/settings/:key` n'accepte que les clés de `GENERIC_KEYS`
(`functions/_lib/settings.js`), chacune avec ses rôles et sa validation : aucune clé arbitraire.
La lecture publique `/api/settings/:key` est limitée à `PUBLIC_KEYS` (`home`, `pages`, `alert`).
`updated_at` est toujours une date ISO, `updated_by` l'id du compte.

## Routes

- **Authentification** (`functions/api/auth/`)
  - `POST login`, `POST logout`, `GET me`, `POST password` ;
  - `GET sessions` liste les appareils connectés, `DELETE sessions` déconnecte les autres.
- **Comptes** (`/api/admin/accounts`, superadmin) : liste, création avec mot de passe provisoire, modification, désactivation, réinitialisation.
- **Journal** (`GET /api/admin/audit`, superadmin) : les dernières actions, affichées dans Site entier → Compte et sécurité.
- **Statistiques** : `GET /api/admin/stats`.
- **Visites** : `POST /api/views`, qui ne compte que les pages connues du site.
- **Événements, côté public** :
  - `GET /api/events/registration-info` ;
  - `POST /api/events/register` : 5 inscriptions par IP en 15 min, code `ASC-XXXX-XXXX` tiré par `crypto.getRandomValues`, places vérifiées et réservées en une seule requête SQL (pas de dépassement de jauge).
- **Événements, côté admin** :
  - `GET/PUT /api/admin/events/settings` ;
  - `GET /api/admin/events/registrations` : liste nominative pour le superadmin et le responsable événements, synthèse chiffrée seulement pour l'éditeur ;
  - `DELETE /api/admin/events/registrations` ;
  - `GET /api/admin/events/export` (CSV, superadmin et responsable événements).
  - Toutes ces routes ne portent que sur l'événement en cours (`event_slug`).

Rôles et pages autorisées : `functions/_lib/roles.js` (superadmin : tout ; editor : tout sauf Comptes ;
events : Événements seulement). Le middleware renvoie chaque rôle vers sa page s'il en ouvre une autre.

## Scripts de génération des pages : ordre obligatoire

Les pages `SA-*` sont générées depuis la maquette, puis « branchées » sur l'API par des scripts qui
modifient les pages générées. Régénérer sans rebrancher efface les branchements.

1. `scripts/install_superadmin.py /Users/mac/Documents/mosque/superadmin.html .` régénère les pages `SA-*`.
   **Il relance lui-même les étapes 2 à 4**, sauf avec `--sans-branchements`.
2. `scripts/wire_homepage.py` : accueil public (réglages, visites), panneau Accueil, bandeau statistiques.
3. `scripts/wire_events.py` : inscriptions publiques, panneau Événements.
4. `scripts/wire_site.py` : Site entier (Pages publiées, bannière d'alerte, Compte et sécurité), et sur le site public :
   masquage des pages et affichage de la bannière d'alerte.

Les scripts 2 à 4 peuvent être relancés seuls autant de fois que nécessaire : ils remplacent
leurs propres ajouts au lieu de les dupliquer.

Autres scripts : `scripts/create-superadmin.mjs` (`--sql` pour la console D1, `--reset` pour un nouveau mot de passe).

## Sécurité

- Mots de passe : PBKDF2-SHA256, 100 000 itérations, sel aléatoire, hachés côté serveur (ou sur le Mac pour le superadmin).
- Sessions : jeton de 256 bits, seule son empreinte SHA-256 est stockée ; 12 h, ou 30 jours avec « Rester connecté ».
- Connexion : 5 échecs en 15 minutes, par IP ou par identifiant, bloquent pendant 15 minutes.
- Écritures refusées si elles ne viennent pas du site (en-tête `Origin`).
- `functions/`, `migrations/`, `scripts/`, `wrangler.toml` ne sont jamais servis.
- `_routes.json` limite les Functions à l'API, au superadmin et aux pages publiques masquables.

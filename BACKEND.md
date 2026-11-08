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
| Accueil | Panneau Accueil fiabilisé : vraie logique (`scripts/panneau_component.js`), heures et annonces modifiables, rubriques du menu, ordres, nombre d'annonces, menu « … » (exporter, importer, valeurs d'origine) ; accueil public : durée de chargement, date hégirienne, ordre des cartes | fait, à pousser |
| 2b | Statistiques réelles (`page_views`, `/api/admin/stats`) et bandeau du panneau Accueil | en ligne |
| 2c | Inscriptions aux événements (`event_registrations`, clé `event_registration`), panneau Événements, export CSV | en ligne |
| Site entier | « Pages publiées » (clé `pages`, pastilles d'état réel pour niveaux 1/2/3, interrupteur Accueil verrouillé) ; « Compte et sécurité » avec les vraies données de session et journal détaillé (nom des pages modifiées) | fait, à pousser |
| Site entier | « Bannière d'alerte » (clé `alert`) : bande en haut de toutes les pages publiques, avec message, lien, période, couleur, aperçu en direct et cohérence message vide / OFF | fait, à pousser |
| Site entier | « Mode du site » (clé `season`) : bandeau Ramadan / Aïd en haut de l'accueil pendant la période ; « Langues » (clé `languages`, interrupteur Français verrouillé) | fait, à pousser |
| 5a | Créer une page : base (`custom_pages`, `page_redirects`) et API (créer, lire, modifier, dupliquer, supprimer) | en ligne |
| 5b | Créer une page : écrans « Mes pages » (création avec titre, lien et visibilité, Brouillon par défaut) et éditeur (blocs Texte, Bouton, Tableau complet, compteurs, sauvegarde haut/bas et suppression avec confirmation) | fait, à pousser |
| 5c | Créer une page : affichage public `/p/<lien>` (publiée, lien privé, brouillon pour les comptes connectés) | en ligne |
| 5d | Créer une page : pages proposées dans les liens de la bannière d'alerte, des boutons de l'accueil et de l'éditeur | en ligne |
| H1 | Horaires : `prayer_times` complétée (lever, une ligne par jour) ; clé `horaires` (bloc Aujourd'hui, vendredi, Ramadan, Aïd, Qibla) | en ligne |
| H2 | Horaires : API du tableau du mois (`GET`/`PUT /api/admin/prayer-times`) et API publique du mois et du jour (`GET /api/prayer-times`, repli sur les défauts Accueil) | en ligne |
| H3 | Horaires : panneau `SA-Horaires` (« Horaires du mois », tableau mensuel éditable, copie sur tout le mois, collage Excel, réglages `horaires`, dates Ramadan depuis `season`, Jumu'a depuis le tableau mensuel) | en ligne |
| H4 | Horaires : page publique (et M-/T-) reliée à la base : heures du jour, tableau du mois avec « Aujourd'hui » sur le vrai jour, carte du vendredi, Ramadan (dates du Mode du site, Suhoor, Iftar, Tarawih), Aïd, Qibla, réglages du bloc Aujourd'hui ; bouton PDF retiré (`scripts/wire_prieres.py`) | en ligne |
| H5 | Horaires : heures du jour sur les 58 pages publiques (barre « Prochaine prière », menu mobile, pied de page, carte « Prochaine prière » de l'accueil), sur toutes les heures remplies ; le script de l'accueil ne garde que l'affichage des puces et de la progression | en ligne |
| H6 | Horaires : onglets « Langue de la khutba » (clé `khutba` : vendredis datés, langue, traduction, imam, nombre affiché, mode) et « Rappel de prière » (clé `rappel` : prières et délais proposés, délai par défaut, titre, son, vibration) ; pages N2-Khutba et N3-Rappel reliées (vraies notifications page ouverte, choix mémorisés sur l'appareil, fichier calendrier .ics du mois) | en ligne |
| A | À propos : onglet « L’association » (clé `apropos` : présentation, valeurs, histoire datée, liens du projet, équipe avec photos réduites et accord écrit, chiffres et sources) et onglet « Campagne en direct » (clé `campagne` : donateurs, mise à jour automatique depuis `donations`, étapes, dons par semaine, derniers dons ; objectif et récolté dans `home.campagne`) ; pages APropos et N3-Campagne reliées, simulation retirée ; route publique `GET /api/campagne` | en ligne |
| S1 | Services : onglet « Tous les services » (clé `services` : cartes ordonnées, affichées ou masquées, cartes libres ajoutées ou supprimées ; prières et Jumu'a avec les heures du tableau du mois ; Aïd avec le lieu commun `horaires.aid.lieu` et la Zakat al-Fitr ; cartes « Les autres services », équipements, bloc « Une question ? ») ; interrupteurs « Page publiée » des 6 onglets reliés à `pages` ; page Services (et M-/T-) reliée, mentions « à confirmer » retirées | fait, à pousser |
| 4 | Annonces, dons : API sur les tables existantes `announcements`, `donations`, `events` | à faire |

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
| `0007_custom_pages.sql` | `custom_pages` (titre, lien unique, blocs JSON, visibilité, mise en page, largeur, description) ; `page_redirects` (ancienne adresse → page) |
| `0008_prayer_times.sql` | complète `prayer_times` : colonne `lever`, index unique `ux_prayer_times_date` (une ligne par jour, date AAAA-MM-JJ) |

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
| `season` | superadmin, editor | `PUT /api/admin/settings/season` | `GET /api/settings/season` (accueil) |
| `languages` | superadmin, editor | `PUT /api/admin/settings/languages` | `GET /api/settings/languages` |
| `horaires` | superadmin, editor | `PUT /api/admin/settings/horaires` | `GET /api/settings/horaires` (page Horaires) |
| `khutba` | superadmin, editor | `PUT /api/admin/settings/khutba` | `GET /api/settings/khutba` (page Langue de la khutba) |
| `rappel` | superadmin, editor | `PUT /api/admin/settings/rappel` | `GET /api/settings/rappel` (page Rappel de prière) |
| `apropos` | superadmin, editor | `PUT /api/admin/settings/apropos` (corps jusqu’à 1 Mo : photos) | `GET /api/settings/apropos` (page À propos) |
| `services` | superadmin, editor | `PUT /api/admin/settings/services` | `GET /api/settings/services` (page Services) |
| `campagne` | superadmin, editor | `PUT /api/admin/settings/campagne` | `GET /api/campagne` (calculé : objectif et récolté de `home`, ou totaux de `donations` en mode automatique) |
| `event_registration` | superadmin, events | `PUT /api/admin/events/settings` | `GET /api/events/registration-info` |

La route générique `/api/admin/settings/:key` n'accepte que les clés de `GENERIC_KEYS`
(`functions/_lib/settings.js`), chacune avec ses rôles et sa validation : aucune clé arbitraire.
La lecture publique `/api/settings/:key` est limitée à `PUBLIC_KEYS` (`home`, `pages`, `alert`, `season`, `languages`, `horaires`, `khutba`, `rappel`, `apropos`).
En mode automatique de la campagne, `GET /api/settings/home` et le tableau de bord renvoient le montant récolté calculé depuis `donations` (tous les dons de la table).

Horaires : les heures sont dans `prayer_times` (une ligne par jour) ; une case vide prend la valeur par défaut de la carte
« Prochaine prière » de l'Accueil (`home.priere` : Fajr 06:30, Jumu'a 12:30, Icha 19:00), puis « — ». Les dates du Ramadan viennent de la clé `season`.
Routes du tableau mensuel : `GET`/`PUT /api/admin/prayer-times` (ou `/:month`, superadmin + éditeur) et `GET /api/prayer-times` (ou `/today`, `/:month`, `/:date`, publique sans authentification).

Liens de l'accueil (`home`) : seuls « Page : … », `/p/<lien>` et `https://…` sont acceptés ; toute autre valeur
revient à la valeur par défaut. La bannière accepte aussi un lien vers une page créée (`{ type: 'custom', slug }`).

Limites connues : le mode du site ne change pas les couleurs du site (pas de variables de couleur),
et les textes ne sont pas traduits : les langues ne règlent que ce que propose le sélecteur.
`updated_at` est toujours une date ISO, `updated_by` l'id du compte.

## Routes

- **Authentification** (`functions/api/auth/`)
  - `POST login`, `POST logout`, `GET me`, `POST password` ;
  - `GET sessions` liste les appareils connectés, `DELETE sessions` déconnecte les autres.
- **Comptes** (`/api/admin/accounts`, superadmin) : liste, création avec mot de passe provisoire, modification, désactivation, réinitialisation.
- **Journal** (`GET /api/admin/audit`, superadmin) : les dernières actions, affichées dans Site entier → Compte et sécurité.
- **Pages créées** (`/api/admin/pages`, superadmin et éditeur) :
  - `GET` liste, `POST { title, slug?, visibility? }` crée une page (en brouillon par défaut ; lien tiré du titre et rendu unique s'il n'est pas fourni) ;
  - `GET/PUT/DELETE /api/admin/pages/:id` ; changer le lien crée une redirection depuis l'ancien ;
  - `POST /api/admin/pages/:id/duplicate` (copie en brouillon) ;
  - règles (lien, blocs Texte / Bouton / Tableau, limites) dans `functions/_lib/custom-pages.js`.
- **Pages publiques** : `GET /p/<lien>` (`functions/p/[slug].js`), rendu serveur sans script
  (`functions/_lib/render-page.js`) : publiée = visible et indexée ; lien privé = visible, jamais indexée ;
  brouillon = comptes connectés seulement (bandeau), sinon page introuvable ; ancienne adresse = 301 ;
  mise en page « avec menu et pied » = en-tête, pied et bannière d'alerte du site ; « vierge » = sans.
- **Réglages, valeurs d'origine** : `GET /api/admin/settings/:key?defaults=1` (sans rien enregistrer).
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
   **Il relance lui-même les étapes 2 à 9**, sauf avec `--sans-branchements`.
2. `scripts/wire_homepage.py` : accueil public (réglages, visites), panneau Accueil, bandeau statistiques.
   Il remplace la logique du panneau par `scripts/panneau_component.js` (état unique : interrupteurs,
   ordre, cartes, annonces, heures) ; le script `#sa-panneau-sync` enregistre via `window.__saHome`.
3. `scripts/wire_events.py` : inscriptions publiques, panneau Événements.
4. `scripts/wire_site.py` : tout Site entier (pages publiées, mode du site, langues, bannière d'alerte, compte et sécurité),
   et sur le site public : masquage des pages, bannière d'alerte, sélecteur de langues, bandeau de saison (accueil).

5. `scripts/wire_pages.py` : Créer une page (« Mes pages » et l'éditeur `SA-PageEditeur.dc.html?id=<page>`),
   et les liens de l'accueil (pages créées proposées, « Lien externe… » qui demande l'adresse).
6. `scripts/wire_horaires.py` : panneau `SA-Horaires` (« Horaires du mois » : choix du mois courant + 2 suivants,
   tableau mensuel éditable relié à `/api/admin/prayer-times/:month`, « Copier une heure sur tout le mois »,
   « Coller depuis Excel », réglages reliés à `horaires`, dates Ramadan lues depuis `season`, Jumu'a lu/écrit dans le tableau mensuel).
7. `scripts/wire_prieres.py` : les 58 pages publiques, heures de prière tirées de la base (`GET /api/prayer-times`) ; page Horaires :
   tableau du mois, cartes et réglages `horaires`. Le script `#ascil-prayer-live` range les données dans `window.__ascilPrayer`
   et prévient la page (événement `ascil:prayer`).
8. `scripts/wire_apropos.py` : panneau `SA-APropos` (clés `apropos`, `campagne`, objectif et récolté de `home`)
   et pages publiques APropos et N3-Campagne (données de `/api/settings/apropos` et `/api/campagne`, relues chaque minute sur la campagne).
9. `scripts/wire_services.py` : panneau `SA-Services` (clé `services`, lieu de l'Aïd dans `horaires`, pages publiées) et page publique Services
10. `scripts/fix_inputs.py` : **toujours en dernier**. Les pages sont rendues par React : un champ écrit
   avec `value="…"` dans la maquette devient « contrôlé » et refuse toute saisie (impossible d'écrire ou
   de choisir une date). Le script transforme ces valeurs en valeurs de départ (`defaultValue`,
   `defaultChecked`). Le contenu des balises `<script>` n'est pas touché (champs construits en HTML par les panneaux). Les scripts 2 à 9 s'appuient sur les attributs d'origine, d'où cet ordre.

Les scripts 2 à 9 peuvent être relancés seuls autant de fois que nécessaire : ils remplacent
leurs propres ajouts au lieu de les dupliquer.

Autres scripts : `scripts/create-superadmin.mjs` (`--sql` pour la console D1, `--reset` pour un nouveau mot de passe).

## Sécurité

- Mots de passe : PBKDF2-SHA256, 100 000 itérations, sel aléatoire, hachés côté serveur (ou sur le Mac pour le superadmin).
- Sessions : jeton de 256 bits, seule son empreinte SHA-256 est stockée ; 12 h, ou 30 jours avec « Rester connecté ».
- Connexion : 5 échecs en 15 minutes, par IP ou par identifiant, bloquent pendant 15 minutes.
- Écritures refusées si elles ne viennent pas du site (en-tête `Origin`).
- `functions/`, `migrations/`, `scripts/`, `wrangler.toml` ne sont jamais servis.
- `_routes.json` limite les Functions à l'API, au superadmin, aux pages publiques masquables et à `/p/*`.
- `/p/<lien>` : en-tête `Content-Security-Policy` sans aucun script, tout texte échappé.

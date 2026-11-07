# Backend du superadmin (Cloudflare Pages Functions + D1)

Le site statique reste servi depuis la racine du dépôt. L'API vit dans `functions/`,
sur le même domaine : pas de CORS, cookie de session `HttpOnly; Secure; SameSite=Strict`.
Base : D1 `ascil-mosquee`, liée sous le nom `DB` (voir `wrangler.toml`).

## Feuille de route

| Étape | Contenu | État |
|---|---|---|
| 1 | Compte superadmin (un seul, imposé par la base), sessions, limitation des essais, journal ; connexion et déconnexion reliées au frontend ; pages `SA-*` protégées côté serveur | **fait, testé en local sur une copie du schéma de prod** |
| 2 | Réglages des widgets de l'accueil (`site_settings`, JSON versionné) + API + bouton « Enregistrer » du panneau ; l'accueil public lit ces réglages | **fait, testé en local** |
| 3 | Pages créées dans le superadmin (`custom_pages`, blocs, lien personnalisable `/p/<slug>`, brouillon / publiée) | à faire |
| 4 | Événements, annonces, dons : API sur les tables existantes `events`, `announcements`, `donations` (+ `prayer_times` pour les horaires) | à faire |
| 5 | Journal des modifications affiché dans « Site entier », export / import des réglages | à faire |

Les tables existantes ne sont jamais recréées : on les complète avec `ALTER TABLE`.
`prayer_times`, `events`, `donations` et `announcements` ne sont touchées par aucune migration à ce stade.

## Ce que fait l'étape 1

- `migrations/0001_superadmin_auth.sql` :
  - complète `admins` avec `ALTER TABLE` ;
  - ajoute un identifiant unique et impose un seul superadmin ;
  - crée `admin_sessions`, `login_attempts` et `audit_log`.
- `functions/_middleware.js` :
  - redirige toute page `SA-*` vers `superadmin.html?next=…` sans session valide ;
  - renvoie vers le panneau si l'on est déjà connecté ;
  - ne sert jamais `functions/`, `migrations/`, `scripts/`, `wrangler.toml` ;
  - refuse les requêtes d'écriture venant d'un autre site.
- `functions/api/auth/*` :
  - `POST login` ;
  - `POST logout` ;
  - `GET me` ;
  - `POST password`, qui ferme aussi les autres sessions.
- Mots de passe : PBKDF2-SHA256, 100 000 itérations, sel aléatoire.
- Jetons de session : 256 bits, seule leur empreinte SHA-256 est stockée.
- Durée de session : 12 h, ou 30 jours avec « Rester connecté ».
- 5 échecs en 15 minutes, par IP ou par identifiant, bloquent la connexion pendant 15 minutes.
- `_routes.json` : les Functions ne s'exécutent que sur ces chemins. Le reste du site ne consomme aucune invocation.
- `scripts/create-superadmin.mjs` :
  - crée l'unique superadmin, ou change son mot de passe avec `--reset` ;
  - le hachage se fait sur votre machine.
- `scripts/install_superadmin.py` : régénère les pages `SA-*` à partir de la maquette, avec le branchement connexion / déconnexion.

## Mise en ligne de l'étape 1 (dans cet ordre)

Schéma relevé en ligne le 07/11/2026 : `admins (id, email, role, created_at)`, vide.
La migration `0001` la **complète** avec `ALTER TABLE`, sans la recréer. Elle ne touche pas
`prayer_times`, `events`, `donations` ni `announcements`.

1. Console D1 (dashboard → D1 → ascil-mosquee → Console) : coller le SQL de `0001`.
   Ce SQL inclut l'enregistrement dans `d1_migrations`, pour que wrangler ne le rejoue pas plus tard.
   Vérifier ensuite avec `PRAGMA table_info(admins)`.
2. Créer le superadmin. Le mot de passe est haché sur votre Mac :
   ```bash
   node scripts/create-superadmin.mjs --sql
   ```
   Coller le SQL affiché dans la console D1.
3. Pages → Paramètres → Liaisons : ajouter une liaison D1 nommée `DB`, reliée à `ascil-mosquee`.
   `wrangler.toml` déclare la même liaison.
4. Pousser sur `main` : Cloudflare Pages déploie le site et les Functions.
5. Contrôler la mise en ligne :
   - `/api/auth/me` répond `401` en JSON (et non `503`) ;
   - `/SA-Panneau.dc.html` renvoie vers la connexion ;
   - la connexion fonctionne.

## Tester en local

```bash
# recréer d'abord en local les 5 tables de prod (schéma relevé ci-dessus), puis :
npx wrangler@4 d1 migrations apply ascil-mosquee --local
node scripts/create-superadmin.mjs --local
npx wrangler@4 pages dev --port 8790
```

La base locale vit dans `.wrangler/` (ignorée par git).

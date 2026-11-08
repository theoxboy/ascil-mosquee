-- Étape R : mur « Dua et annonces » (page N3-Dua). Chaque message est relu dans le panneau
-- (Ressources → Dua et annonces) avant d'apparaître sur le mur.
-- Nouvelle table : aucune table existante n'est modifiée. L'adresse IP n'est pas conservée ici
-- (les limites d'envoi, de « J'ai fait une dua » et de signalement utilisent rate_limits, migration 0006).

CREATE TABLE IF NOT EXISTS dua_messages (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  type         TEXT    NOT NULL,                      -- dua, ann
  categorie    TEXT,                                  -- catégorie d'une annonce (Covoiturage, Logement…)
  texte        TEXT    NOT NULL,
  signature    TEXT    NOT NULL,
  status       TEXT    NOT NULL DEFAULT 'attente',    -- attente, publie, refuse
  signale      INTEGER NOT NULL DEFAULT 0,            -- 1 : signalé par un visiteur, retiré du mur jusqu'à relecture
  amin         INTEGER NOT NULL DEFAULT 0,            -- compteur « J'ai fait une dua »
  created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_dua_messages_status ON dua_messages(status, type, published_at);

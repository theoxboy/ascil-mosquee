-- Étapes M1 à M5 : nouveaux blocs des pages créées (« Créer une page »).
--  - media        : photos envoyées depuis le panneau (fichiers rangés dans l'espace KV « MEDIA ») ;
--  - page_widgets : code des widgets HTML / CSS / JS / Python (affichés dans une boîte isolée, /w/<id>) ;
--  - custom_forms : formulaires créés dans le panneau (Formulaires) ;
--  - form_entries : réponses envoyées par les visiteurs à ces formulaires.
-- Nouvelles tables uniquement : aucune table existante n'est modifiée.

CREATE TABLE IF NOT EXISTS media (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  file_key    TEXT    NOT NULL UNIQUE,                 -- clé du fichier dans KV, ex. 3f9a…c2.jpg
  mime        TEXT    NOT NULL,                        -- image/jpeg, image/png, image/webp, image/gif
  size        INTEGER NOT NULL,                        -- octets
  width       INTEGER,
  height      INTEGER,
  name        TEXT    NOT NULL DEFAULT '',             -- nom d'origine du fichier (affiché dans le panneau)
  created_at  TEXT    NOT NULL,
  created_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_media_created ON media(created_at);

CREATE TABLE IF NOT EXISTS page_widgets (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT    NOT NULL DEFAULT '',
  lang        TEXT    NOT NULL DEFAULT 'web' CHECK (lang IN ('web', 'python')),
  html        TEXT    NOT NULL DEFAULT '',
  css         TEXT    NOT NULL DEFAULT '',
  js          TEXT    NOT NULL DEFAULT '',             -- JavaScript, ou code Python si lang = 'python'
  net         INTEGER NOT NULL DEFAULT 0,              -- 1 = le widget peut joindre Internet
  height      INTEGER NOT NULL DEFAULT 400,            -- hauteur affichée, en pixels
  created_at  TEXT    NOT NULL,
  updated_at  TEXT    NOT NULL,
  created_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL,
  updated_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS custom_forms (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT    NOT NULL,
  intro       TEXT    NOT NULL DEFAULT '',
  fields      TEXT    NOT NULL DEFAULT '[]',           -- JSON : champs du formulaire
  bouton      TEXT    NOT NULL DEFAULT 'Envoyer',
  merci       TEXT    NOT NULL DEFAULT '',             -- message affiché après l'envoi
  open        INTEGER NOT NULL DEFAULT 1,              -- 0 = fermé, n'accepte plus de réponses
  created_at  TEXT    NOT NULL,
  updated_at  TEXT    NOT NULL,
  created_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL,
  updated_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS form_entries (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  form_id     INTEGER NOT NULL REFERENCES custom_forms(id) ON DELETE CASCADE,
  data        TEXT    NOT NULL,                        -- JSON : { idDuChamp: valeur }
  page_slug   TEXT,                                    -- page d'où vient la réponse
  status      TEXT    NOT NULL DEFAULT 'nouveau' CHECK (status IN ('nouveau', 'lu', 'traite')),
  created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_form_entries_form ON form_entries(form_id, created_at);
CREATE INDEX IF NOT EXISTS idx_form_entries_status ON form_entries(status, created_at);

-- Étape 5a : pages créées dans le superadmin (« Créer une page »).
-- Adresse publique : /p/<slug>. Les blocs (texte, bouton, tableau) sont stockés en JSON,
-- validés par l'API (functions/_lib/custom-pages.js).

CREATE TABLE IF NOT EXISTS custom_pages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT    NOT NULL UNIQUE COLLATE NOCASE,          -- lettres minuscules, chiffres, tirets
  title       TEXT    NOT NULL,
  blocks      TEXT    NOT NULL DEFAULT '[]',                   -- JSON
  visibility  TEXT    NOT NULL DEFAULT 'draft'
              CHECK (visibility IN ('draft', 'published', 'private')),
  layout      TEXT    NOT NULL DEFAULT 'site' CHECK (layout IN ('site', 'blank')),
  width       TEXT    NOT NULL DEFAULT 'normal' CHECK (width IN ('normal', 'large', 'full')),
  description TEXT    NOT NULL DEFAULT '',
  created_at  TEXT    NOT NULL,                                -- ISO
  updated_at  TEXT    NOT NULL,                                -- ISO
  created_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL,
  updated_by  INTEGER REFERENCES admins(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_custom_pages_visibility ON custom_pages(visibility);

-- Quand le lien d'une page change, l'ancienne adresse redirige vers la nouvelle.
CREATE TABLE IF NOT EXISTS page_redirects (
  old_slug   TEXT    PRIMARY KEY COLLATE NOCASE,
  page_id    INTEGER NOT NULL REFERENCES custom_pages(id) ON DELETE CASCADE,
  created_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_page_redirects_page ON page_redirects(page_id);

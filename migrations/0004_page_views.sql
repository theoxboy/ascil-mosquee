-- Étape 2b : Statistiques et suivi de fréquentation anonymisé
CREATE TABLE IF NOT EXISTS page_views (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  path        TEXT    NOT NULL,
  viewed_date TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d', 'now')),
  count       INTEGER NOT NULL DEFAULT 1,
  UNIQUE(path, viewed_date)
);
CREATE INDEX IF NOT EXISTS idx_page_views_date ON page_views(viewed_date);
CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path);

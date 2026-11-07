-- Migration 0005 : Inscriptions aux événements (étape 2c)

CREATE TABLE IF NOT EXISTS event_registrations (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  event_slug      TEXT    NOT NULL DEFAULT 'iftar-2027',
  event_title     TEXT    NOT NULL,
  code            TEXT    NOT NULL UNIQUE,
  name            TEXT    NOT NULL,
  contact         TEXT    NOT NULL,
  attendees_count INTEGER NOT NULL DEFAULT 1,
  is_vegetarian   INTEGER NOT NULL DEFAULT 0,
  status          TEXT    NOT NULL DEFAULT 'confirmed', -- 'confirmed', 'cancelled'
  notes           TEXT,
  created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reg_event ON event_registrations(event_slug, status);
CREATE INDEX IF NOT EXISTS idx_reg_code  ON event_registrations(code);
CREATE INDEX IF NOT EXISTS idx_reg_date  ON event_registrations(created_at);

-- Initialise les réglages par défaut de la jauge et de l'événement si non existants
INSERT OR IGNORE INTO site_settings (key, value, updated_at)
VALUES (
  'event_registration',
  '{"event_slug":"iftar-2027","event_title":"Iftar communautaire","date_str":"Samedi 20 février 2027 · 17 h 15","location":"174 rue Lafontaine","description":"Repas de rupture du jeûne ouvert à tous : familles, voisins, étudiants. Gratuit, dons bienvenus.","total_seats":120,"max_per_reg":6,"deadline":"2027-02-18","is_open":true,"opt_vege":true,"opt_code":true,"opt_agenda":true}',
  strftime('%s', 'now')
);

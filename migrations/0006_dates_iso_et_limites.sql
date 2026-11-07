-- Relecture du 07/11/2026, points 5 et 7.

-- Point 5 : site_settings.updated_at toujours au format ISO (comme la migration 0003).
-- La migration 0005 et l'ancienne route des événements écrivaient un nombre de secondes.
UPDATE site_settings
   SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', CAST(updated_at AS INTEGER), 'unixepoch')
 WHERE updated_at NOT LIKE '%T%' AND CAST(updated_at AS INTEGER) > 0;

-- Point 7 : limite d'essais des formulaires publics (inscriptions aux événements).
-- Une ligne par essai, conservée 24 h ; l'IP sert uniquement à compter les essais.
CREATE TABLE IF NOT EXISTS rate_limits (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  bucket TEXT    NOT NULL,                              -- ex. events.register
  ip     TEXT    NOT NULL,
  at     INTEGER NOT NULL                               -- millisecondes epoch
);
CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup ON rate_limits(bucket, ip, at);

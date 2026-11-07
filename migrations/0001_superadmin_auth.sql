-- Étape 1 : compte superadmin, sessions, limitation des essais, journal.
--
-- La table « admins » existe déjà en ligne : (id, email, role, created_at), vide au 07/11/2026.
-- On la COMPLÈTE avec ALTER TABLE, on ne la recrée pas. Les autres tables existantes
-- (prayer_times, events, donations, announcements) ne sont pas touchées.

ALTER TABLE admins ADD COLUMN username TEXT;
ALTER TABLE admins ADD COLUMN password_hash TEXT;         -- pbkdf2_sha256$<iter>$<sel>$<empreinte>
ALTER TABLE admins ADD COLUMN display_name TEXT;
ALTER TABLE admins ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;
ALTER TABLE admins ADD COLUMN last_login_at TEXT;
ALTER TABLE admins ADD COLUMN password_changed_at TEXT;

-- Identifiant unique, sans tenir compte des majuscules.
CREATE UNIQUE INDEX IF NOT EXISTS ux_admins_username ON admins(username COLLATE NOCASE);
-- Un seul superadmin pour commencer : la base elle-même refuse un second.
CREATE UNIQUE INDEX IF NOT EXISTS ux_admins_one_superadmin ON admins(role) WHERE role = 'superadmin';

-- Le jeton de session n'est jamais stocké : seule son empreinte SHA-256 l'est.
CREATE TABLE IF NOT EXISTS admin_sessions (
  id           TEXT    PRIMARY KEY,                     -- sha256(jeton) en hexadécimal
  admin_id     INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
  created_at   INTEGER NOT NULL,                        -- millisecondes epoch
  expires_at   INTEGER NOT NULL,
  last_seen_at INTEGER NOT NULL,
  ip           TEXT,
  user_agent   TEXT
);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_admin   ON admin_sessions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);

-- Limite les tentatives de connexion (5 échecs en 15 min par IP ou par identifiant).
CREATE TABLE IF NOT EXISTS login_attempts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  ip           TEXT,
  username     TEXT COLLATE NOCASE,
  success      INTEGER NOT NULL,
  attempted_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip   ON login_attempts(ip, attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(username, attempted_at);

-- Journal des modifications (alimentera « Site entier → Journal des modifications »).
CREATE TABLE IF NOT EXISTS audit_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_id   INTEGER REFERENCES admins(id) ON DELETE SET NULL,
  action     TEXT    NOT NULL,                          -- ex. auth.login, auth.logout, settings.update
  target     TEXT,
  details    TEXT,                                      -- JSON
  ip         TEXT,
  created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

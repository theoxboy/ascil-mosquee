-- Étape S2 : boîte de réception des formulaires publics (Contact, puis Cours, Mariages,
-- Funérailles, Aide alimentaire, Espace femmes). Aucun courriel n'est envoyé : les demandes
-- se lisent dans le panneau, Contact → Demandes reçues.
-- Nouvelle table : aucune table existante n'est modifiée. L'adresse IP n'est pas conservée ici
-- (la limite d'essais utilise la table rate_limits, migration 0006).

CREATE TABLE IF NOT EXISTS form_messages (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  source     TEXT    NOT NULL,                       -- contact, cours, mariages, funerailles, aide, femmes
  sujet      TEXT,
  nom        TEXT    NOT NULL,
  contact    TEXT    NOT NULL,                       -- courriel ou téléphone
  message    TEXT    NOT NULL,
  details    TEXT,                                   -- champs propres au formulaire (JSON)
  status     TEXT    NOT NULL DEFAULT 'nouveau',     -- nouveau, lu, traite
  created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_form_messages_status ON form_messages(status, created_at);
CREATE INDEX IF NOT EXISTS idx_form_messages_source ON form_messages(source, created_at);

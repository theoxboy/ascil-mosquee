-- Étape 2 : Réglages du site (accueil et autres pages)
CREATE TABLE IF NOT EXISTS site_settings (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,                            -- JSON
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_by INTEGER REFERENCES admins(id)
);
CREATE INDEX IF NOT EXISTS idx_site_settings_updated ON site_settings(updated_at);

-- Réglages initiaux réels pour la page d'accueil de l'ASCIL
INSERT OR IGNORE INTO site_settings (key, value) VALUES (
  'home',
  '{
    "general": {
      "email": "associationrdl.ascil@gmail.com",
      "facebook": "https://www.facebook.com/",
      "address": "174 rue Lafontaine",
      "city": "Rivière-du-Loup (Québec)",
      "mapUrl": "https://maps.google.com/?q=174+rue+Lafontaine+Riviere-du-Loup"
    },
    "ordre": ["acces", "campagne", "annonces", "bienvenue", "invitation"],
    "on": {
      "chargement": true, "bandeau": true, "compte": true, "mail": true, "fb": true,
      "don": true, "langue": true, "horaires": true, "apropos": true, "services": true,
      "evenements": true, "ressources": true, "contact": true, "hero": true, "priere": true,
      "hegirien": true, "progression": true, "puces": true, "acces": true, "campagne": true,
      "barre": true, "annonces": true, "bienvenue": true, "invitation": true, "haut": true,
      "pHor": true, "pIti": true, "pFb": true, "pTcom": true, "pCciq": true, "pMail": true
    },
    "chargement": {
      "duration": "normale"
    },
    "hero": {
      "h1": "Page : Horaires du mois",
      "h2": "Page : Faire un don"
    },
    "priere": {
      "fajr": "06:30",
      "lever": "",
      "dohr": "",
      "jumua": "12:30",
      "asr": "",
      "maghreb": "",
      "icha": "19:00"
    },
    "acces": {
      "cartes": [
        { "id": "vendredi", "on": true, "lien": "Page : Horaires du mois" },
        { "id": "trouver", "on": true, "lien": "Page : Contact" },
        { "id": "campagne", "on": true, "lien": "Page : Faire un don" }
      ]
    },
    "campagne": {
      "objectif": 350000,
      "recolte": 140000,
      "btnInterac": "Page : Faire un don",
      "btnSuivre": "Page : Campagne en direct"
    },
    "annonces": {
      "max": 3,
      "btnTous": "Page : Événements",
      "items": [
        {
          "id": 0,
          "date": "Oct. 2026",
          "titre": "Lancement de la campagne nouveau lieu",
          "resume": "Objectif 350 000 $ pour acquérir et transformer un bâtiment en mosquée.",
          "lien": "Page : Événements",
          "on": true
        },
        {
          "id": 1,
          "date": "27 mai 2026",
          "titre": "Aïd al-Adha 1447",
          "resume": "Prière célébrée à la salle louée du 15 rue Frontenac.",
          "lien": "Page : Événements",
          "on": true
        },
        {
          "id": 2,
          "date": "25 avr. 2026",
          "titre": "Journée de parrainage d’orphelins",
          "resume": "Avec l’organisme Soleil des Orphelins, au 174 rue Lafontaine.",
          "lien": "Page : Événements",
          "on": true
        }
      ]
    },
    "bienvenue": {
      "lien": "Page : Contact"
    },
    "invitation": {
      "lien": "Page : Contact"
    },
    "pied": {
      "tcom": "https://www.tcomq.ca/",
      "cciq": ""
    }
  }'
);

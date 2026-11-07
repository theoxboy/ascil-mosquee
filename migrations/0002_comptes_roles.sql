-- Étape 2a : comptes supplémentaires à rôle limité.
-- Rôles : 'superadmin' (un seul, déjà imposé par ux_admins_one_superadmin),
--         'editor' (contenu du site), 'events' (événements et inscriptions).
-- Les rôles sont vérifiés par l'API ; la table existante est seulement complétée.

-- 1 = le compte doit choisir son propre mot de passe à la prochaine connexion
--     (cas d'un compte créé ou d'un mot de passe réinitialisé par le superadmin).
ALTER TABLE admins ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0;
-- Qui a créé ce compte (id du superadmin).
ALTER TABLE admins ADD COLUMN created_by INTEGER;

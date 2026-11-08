-- Étape H1 (Horaires) : le tableau du mois devient la source unique des heures de prière.
-- La table prayer_times existe déjà en ligne : (id, date, fajr, dohr, asr, maghreb, isha, jumuha, source).
-- On la COMPLÈTE : heure du lever du soleil, et une seule ligne par jour (date au format AAAA-MM-JJ).
-- Avant d'appliquer : vérifier qu'aucune date n'apparaît deux fois (sinon l'index unique échoue).

ALTER TABLE prayer_times ADD COLUMN lever TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS ux_prayer_times_date ON prayer_times(date);

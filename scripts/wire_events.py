"""Branchement dynamique des inscriptions aux événements (étape 2c).

1. Pages publiques d'inscription :
   - N3-Inscription.dc.html
   - M-N3-Inscription.dc.html (mobile)
   - T-N3-Inscription.dc.html (tablette)
   -> Script #ascil-inscription-sync :
      - Charge les données réelles et places restantes depuis GET /api/events/registration-info
      - Gère les sélecteurs de places et options
      - Soumet l'inscription via POST /api/events/register sans compte en < 1 min
      - Affiche l'écran de confirmation avec le code unique ASC-XXXX
      - Génère le téléchargement du fichier .ics (Ajouter à mon agenda)

2. Panneau d'administration :
   - SA-Evenements.dc.html
   -> Script #sa-evenements-sync :
      - Charge et sauvegarde les réglages de jauge et dates via GET/PUT /api/admin/events/settings
      - Affiche le résumé en direct et la liste complète des inscrits via GET /api/admin/events/registrations
      - Permet l'annulation d'une inscription via DELETE /api/admin/events/registrations?id=...
      - Connecte le bouton « Exporter la liste (.csv) » vers /api/admin/events/export
      - Connecte le bouton « Écrire aux inscrits » (mailto: en Cci)
"""

import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

PUBLIC_INSCRIPTION_SYNC_SCRIPT = r'''<script id="ascil-inscription-sync">
(function() {
  var eventData = null;
  var currentCount = 1;
  var isVeg = false;

  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function downloadIcs(title, dateStr, location, desc) {
    // Fichier iCalendar universel (.ics)
    var nowStr = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    // Événement Iftar ou personnalisé (défaut : 20 fév 2027 17h15 - 20h00 heure de Montréal/Toronto)
    var dtStart = '20270220T221500Z'; // 17h15 EST en UTC
    var dtEnd   = '20270221T010000Z'; // 20h00 EST en UTC

    var ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//ASCIL//Evenements//FR',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'UID:ascil-' + Date.now() + '@ascil-mosquee.pages.dev',
      'DTSTAMP:' + nowStr,
      'DTSTART:' + dtStart,
      'DTEND:' + dtEnd,
      'SUMMARY:' + (title || 'Événement ASCIL'),
      'DESCRIPTION:' + (desc || ''),
      'LOCATION:' + (location || '174 rue Lafontaine, Rivière-du-Loup'),
      'STATUS:CONFIRMED',
      'END:VEVENT',
      'END:VCALENDAR'
    ].join('\r\n');

    var blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'evenement-ascil.ics';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function updateUI(ev) {
    if (!ev) return;
    eventData = ev;

    // 1. Titre & infos
    var titleEl = document.getElementById('ev-t');
    if (titleEl && ev.title) titleEl.textContent = ev.title;

    var dateEl = document.querySelector('section[aria-labelledby="ev-t"] p.tnum:first-of-type');
    if (dateEl && ev.date_str) {
      dateEl.innerHTML = '<svg class="icon" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C49A4A" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px"><rect x="4" y="5" width="16" height="15" rx="2"></rect><path d="M4 10h16M9 3v4M15 3v4"></path></svg>' + esc(ev.date_str);
    }

    var locEl = document.querySelector('section[aria-labelledby="ev-t"] p:nth-of-type(2)');
    if (locEl && ev.location) {
      locEl.innerHTML = '<svg class="icon" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C49A4A" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"></path><circle cx="12" cy="9.5" r="2.5"></circle></svg>' + esc(ev.location);
    }

    var descEl = document.querySelector('section[aria-labelledby="ev-t"] p:nth-of-type(3)');
    if (descEl && ev.description) descEl.textContent = ev.description;

    // 2. Places & Jauge
    var total = ev.total_seats || 120;
    var reserved = ev.reserved_seats || 0;
    var remaining = typeof ev.remaining_seats === 'number' ? ev.remaining_seats : Math.max(0, total - reserved);
    var pct = Math.min(100, Math.round((reserved / total) * 100));

    var placesTxtEl = document.querySelector('section[aria-labelledby="ev-t"] .prog')?.previousElementSibling?.firstElementChild;
    var pctTxtEl = document.querySelector('section[aria-labelledby="ev-t"] .prog')?.previousElementSibling?.lastElementChild;
    var progBar = document.querySelector('section[aria-labelledby="ev-t"] .prog i');

    if (placesTxtEl) {
      placesTxtEl.textContent = remaining > 0 ? (remaining + ' places restantes sur ' + total) : 'Complet';
    }
    if (pctTxtEl) {
      pctTxtEl.textContent = pct + ' % réservé';
    }
    if (progBar) {
      progBar.style.width = pct + '%';
    }

    // 3. Option végétarienne
    var vegLabel = document.querySelector('input[type="checkbox"]')?.closest('label');
    if (vegLabel && ev.opt_vege === false) {
      vegLabel.style.display = 'none';
    }

    // 4. Si complet ou fermé
    var formCard = document.querySelector('.card[aria-live="polite"]');
    var submitBtn = document.querySelector('.card[aria-live="polite"] button.btn-gold');
    if (!ev.is_open || remaining <= 0) {
      if (submitBtn) {
        submitBtn.setAttribute('disabled', 'true');
        submitBtn.textContent = 'Inscriptions closes';
      }
    }
  }

  function init() {
    fetch('/api/events/registration-info')
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (d && d.ok && d.event) {
          updateUI(d.event);
        }
      })
      .catch(function() {});

    // Gestion des compteurs de personnes − / +
    document.addEventListener('click', function(e) {
      var t = e.target;
      var minusBtn = t && (t.matches('button[aria-label="Une personne de moins"]') || t.closest('button[aria-label="Une personne de moins"]'));
      var plusBtn = t && (t.matches('button[aria-label="Une personne de plus"]') || t.closest('button[aria-label="Une personne de plus"]'));

      var countSpan = document.querySelector('button[aria-label="Une personne de plus"]')?.previousElementSibling;
      var ctaBtn = document.querySelector('.card[aria-live="polite"] button.btn-gold');

      if (minusBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (currentCount > 1) currentCount--;
        if (countSpan) countSpan.textContent = currentCount;
        if (ctaBtn) ctaBtn.textContent = 'Réserver ' + currentCount + ' place' + (currentCount > 1 ? 's' : '');
        return;
      }

      if (plusBtn) {
        e.preventDefault();
        e.stopPropagation();
        var max = (eventData && eventData.max_per_reg) || 6;
        if (eventData && typeof eventData.remaining_seats === 'number') {
          max = Math.min(max, eventData.remaining_seats);
        }
        if (currentCount < max) currentCount++;
        if (countSpan) countSpan.textContent = currentCount;
        if (ctaBtn) ctaBtn.textContent = 'Réserver ' + currentCount + ' place' + (currentCount > 1 ? 's' : '');
        return;
      }

      // Soumission du formulaire
      var isSubmit = t && (t.matches('.card[aria-live="polite"] button.btn-gold') || t.closest('.card[aria-live="polite"] button.btn-gold'));
      if (isSubmit) {
        e.preventDefault();
        e.stopPropagation();
        var btn = t.closest('.card[aria-live="polite"] button.btn-gold') || t;

        var nameIn = document.getElementById('i1');
        var contactIn = document.getElementById('i2');
        var vegBox = document.querySelector('input[type="checkbox"]');

        var nameVal = (nameIn ? nameIn.value : '').trim();
        var contactVal = (contactIn ? contactIn.value : '').trim();

        // Validation
        var hasErr = false;
        if (!nameVal) {
          if (nameIn) nameIn.style.borderColor = '#B3261E';
          hasErr = true;
        } else if (nameIn) {
          nameIn.style.borderColor = '#CDBF9C';
        }

        if (!contactVal) {
          if (contactIn) contactIn.style.borderColor = '#B3261E';
          hasErr = true;
        } else if (contactIn) {
          contactIn.style.borderColor = '#CDBF9C';
        }

        if (hasErr) return;

        btn.setAttribute('disabled', 'true');
        btn.textContent = 'Enregistrement…';

        var payload = {
          name: nameVal,
          contact: contactVal,
          attendees_count: currentCount,
          is_vegetarian: vegBox ? vegBox.checked : false
        };

        fetch('/api/events/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        .then(function(r) { return r.json(); })
        .then(function(res) {
          if (res && res.ok) {
            // Affichage de l'écran de confirmation
            var formCard = document.querySelector('.card[aria-live="polite"]');
            if (formCard) {
              formCard.innerHTML = [
                '<div style="text-align:center;padding:10px 4px">',
                '  <span class="pop" style="display:inline-flex;width:64px;height:64px;border-radius:50%;background:#0E4D3C;color:#fff;align-items:center;justify-content:center">',
                '    <svg class="icon" aria-hidden="true" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>',
                '  </span>',
                '  <p class="h3" style="margin-top:14px;font-size:26px;color:#0E4D3C;font-weight:700">C’est réservé !</p>',
                '  <p style="margin:8px 0 0;color:#202124;font-size:16px">' + esc(res.name) + ', votre réservation pour <strong>' + res.attendees_count + ' place' + (res.attendees_count > 1 ? 's' : '') + '</strong> est confirmée.</p>',
                '  <p style="margin:4px 0 0;font-size:14px;color:#555">' + esc(res.event_title || '') + (res.is_vegetarian ? ' (repas végétarien inclus)' : '') + '</p>',
                '  <p class="tnum" style="margin:18px auto 0;display:inline-block;padding:10px 20px;border-radius:12px;background:#F3EAD8;font-weight:800;font-size:20px;color:#0E4D3C;letter-spacing:.08em">Code : ' + esc(res.code) + '</p>',
                '  <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:20px">',
                '    <button type="button" id="btn-add-agenda" class="btn btn-ghost" style="min-height:44px;font-weight:600">Ajouter à mon agenda (.ics)</button>',
                '    <button type="button" id="btn-new-reg" class="btn btn-ghost" style="min-height:44px;font-weight:600">Nouvelle inscription</button>',
                '  </div>',
                '  <p class="muted" style="margin:16px 0 0;font-size:14px">Pour modifier ou annuler, écrivez à l’association en indiquant votre code.</p>',
                '</div>'
              ].join('');

              var agendaBtn = document.getElementById('btn-add-agenda');
              if (agendaBtn) {
                agendaBtn.addEventListener('click', function() {
                  downloadIcs(res.event_title, res.date_str, res.location, 'Réservation ASCIL code ' + res.code);
                  agendaBtn.textContent = 'Téléchargé ✓';
                });
              }

              var newRegBtn = document.getElementById('btn-new-reg');
              if (newRegBtn) {
                newRegBtn.addEventListener('click', function() {
                  location.reload();
                });
              }
            }

            // Rafraîchir les places affichées
            fetch('/api/events/registration-info')
              .then(function(r) { return r.ok ? r.json() : null; })
              .then(function(d) { if (d && d.event) updateUI(d.event); });

          } else {
            btn.removeAttribute('disabled');
            btn.textContent = 'Réserver ' + currentCount + ' place' + (currentCount > 1 ? 's' : '');
            alert(res.message || 'Une erreur est survenue lors de l’inscription.');
          }
        })
        .catch(function() {
          btn.removeAttribute('disabled');
          btn.textContent = 'Réserver ' + currentCount + ' place' + (currentCount > 1 ? 's' : '');
          alert('Erreur réseau. Veuillez vérifier votre connexion.');
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
'''

ADMIN_EVENEMENTS_SYNC_SCRIPT = r'''<script id="sa-evenements-sync">
(function() {
  var initialSettings = null;
  var isDirty = false;
  var allRegistrations = [];

  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function toast(msg) {
    var existing = document.getElementById('sa-toast');
    if (!existing) {
      existing = document.createElement('div');
      existing.id = 'sa-toast';
      existing.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0E4D3C;color:#fff;padding:12px 24px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.25);font-size:14px;font-weight:600;z-index:99999;transition:opacity .2s;opacity:0;pointer-events:none;';
      document.body.appendChild(existing);
    }
    existing.textContent = msg;
    existing.style.opacity = '1';
    clearTimeout(window.__saToastTimer);
    window.__saToastTimer = setTimeout(function() {
      existing.style.opacity = '0';
    }, 3200);
  }

  function setStatus(dirty, text) {
    isDirty = dirty;
    var dot = document.querySelector('header.top .sdot');
    var p = document.querySelector('header.top .status');
    var saveBtn = document.querySelector('header.top button.btn-gold');
    var cancelBtn = document.querySelector('header.top button.btn-onDark');

    if (dot) dot.style.background = dirty ? '#C49A4A' : '#1D7A58';
    if (p) p.innerHTML = '<span class="sdot" aria-hidden="true" style="width:9px;height:9px;border-radius:50%;background:' + (dirty ? '#C49A4A' : '#1D7A58') + '"></span>' + (text || (dirty ? 'Modifications non enregistrées' : 'Tout est enregistré'));
    if (saveBtn) {
      if (dirty) saveBtn.removeAttribute('disabled');
      else saveBtn.setAttribute('disabled', 'true');
    }
    if (cancelBtn) {
      if (dirty) cancelBtn.removeAttribute('disabled');
      else cancelBtn.setAttribute('disabled', 'true');
    }
  }

  function markDirty() {
    setStatus(true);
  }

  function getSwitch(label, fallback) {
    var sw = document.querySelector('button.sw[aria-label="' + label + '"]');
    if (!sw) return fallback != null ? fallback : false;
    return sw.getAttribute('aria-checked') === 'true';
  }

  function setSwitch(label, val) {
    var sw = document.querySelector('button.sw[aria-label="' + label + '"]');
    if (!sw) return;
    sw.setAttribute('aria-checked', val ? 'true' : 'false');
  }

  function loadSettings() {
    fetch('/api/admin/events/settings', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !d.ok || !d.settings) return;
        var s = d.settings;
        initialSettings = JSON.parse(JSON.stringify(s));

        // Formulaire Jauge / Inscription (sp-3)
        var f19 = document.getElementById('f19');
        var f20 = document.getElementById('f20');
        var f21 = document.getElementById('f21');
        var f22 = document.getElementById('f22');

        if (f19 && s.event_title) {
          // Si l'option n'existe pas, on l'ajoute
          var exists = false;
          for (var i = 0; i < f19.options.length; i++) {
            if (f19.options[i].value === s.event_title || f19.options[i].text === s.event_title) {
              f19.selectedIndex = i;
              exists = true;
              break;
            }
          }
          if (!exists) {
            var opt = document.createElement('option');
            opt.value = s.event_title;
            opt.text = s.event_title;
            f19.appendChild(opt);
            f19.value = s.event_title;
          }
        }

        if (f20 && s.total_seats != null) f20.value = s.total_seats;
        if (f21 && s.max_per_reg != null) f21.value = s.max_per_reg;
        if (f22 && s.deadline != null) f22.value = s.deadline;

        setSwitch('Inscriptions ouvertes', s.is_open);
        setSwitch('Option « Repas végétarien »', s.opt_vege);
        setSwitch('Code de confirmation', s.opt_code);
        setSwitch('Bouton « Ajouter à mon agenda »', s.opt_agenda);

        setStatus(false, 'Tout est enregistré');
      })
      .catch(function() {});
  }

  function loadRegistrations() {
    fetch('/api/admin/events/registrations', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !d.ok) return;
        allRegistrations = d.registrations || [];
        var sm = d.summary || {};

        // Résumé en haut de la carte
        var infoP = document.querySelector('#sp-3 section[aria-label="Inscrits"] p.info');
        if (infoP) {
          var totalSeats = initialSettings ? initialSettings.total_seats : 120;
          infoP.textContent = (sm.total_attendees || 0) + ' places réservées sur ' + totalSeats + ' · ' + (sm.total_registrations || 0) + ' inscription(s) confirmée(s) · ' + (sm.vegetarian_count || 0) + ' repas végétarien(s)';
        }

        // Tableau des inscrits
        renderRegistrationsTable(allRegistrations);
      })
      .catch(function() {});
  }

  function renderRegistrationsTable(list) {
    var cardB = document.querySelector('#sp-3 section[aria-label="Inscrits"] .card-b');
    if (!cardB) return;

    var existingWrap = document.getElementById('sa-reg-list-wrap');
    if (!existingWrap) {
      existingWrap = document.createElement('div');
      existingWrap.id = 'sa-reg-list-wrap';
      existingWrap.style.marginTop = '18px';
      cardB.appendChild(existingWrap);
    }

    if (!list || list.length === 0) {
      existingWrap.innerHTML = '<p style="color:#5E6460;font-style:italic;margin-top:12px">Aucune inscription enregistrée pour le moment.</p>';
      return;
    }

    var html = [
      '<div style="overflow-x:auto;border:1px solid #E4D9C0;border-radius:12px;margin-top:14px;background:#fff">',
      '  <table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left">',
      '    <thead>',
      '      <tr style="background:#F6EEDF;color:#0E4D3C;font-weight:700;border-bottom:1px solid #E4D9C0">',
      '        <th style="padding:10px 12px">Code</th>',
      '        <th style="padding:10px 12px">Nom</th>',
      '        <th style="padding:10px 12px">Contact</th>',
      '        <th style="padding:10px 12px;text-align:center">Places</th>',
      '        <th style="padding:10px 12px;text-align:center">Végé</th>',
      '        <th style="padding:10px 12px">Date</th>',
      '        <th style="padding:10px 12px;text-align:center">Statut</th>',
      '        <th style="padding:10px 12px;text-align:right">Action</th>',
      '      </tr>',
      '    </thead>',
      '    <tbody>'
    ];

    list.forEach(function(r) {
      var isConfirmed = r.status === 'confirmed';
      var statusTag = isConfirmed
        ? '<span style="display:inline-block;padding:2px 8px;border-radius:12px;background:#EAF3EF;color:#0E4D3C;font-weight:700;font-size:11px">Confirmé</span>'
        : '<span style="display:inline-block;padding:2px 8px;border-radius:12px;background:#FDEBEB;color:#B3261E;font-weight:700;font-size:11px">Annulé</span>';

      var dateStr = (r.created_at || '').slice(0, 16).replace('T', ' ');

      html.push(
        '<tr style="border-bottom:1px solid #F1E9DB;' + (!isConfirmed ? 'opacity:.6' : '') + '">',
        '  <td style="padding:10px 12px;font-family:monospace;font-weight:700;color:#0E4D3C">' + esc(r.code) + '</td>',
        '  <td style="padding:10px 12px;font-weight:600">' + esc(r.name) + '</td>',
        '  <td style="padding:10px 12px"><a href="' + (r.contact && r.contact.includes('@') ? 'mailto:' + esc(r.contact) : 'tel:' + esc(r.contact)) + '" style="color:#0E4D3C;text-decoration:underline">' + esc(r.contact) + '</a></td>',
        '  <td style="padding:10px 12px;text-align:center;font-weight:700" class="tnum">' + (r.attendees_count || 1) + '</td>',
        '  <td style="padding:10px 12px;text-align:center">' + (r.is_vegetarian ? '🌱 Oui' : '—') + '</td>',
        '  <td style="padding:10px 12px;color:#666;font-size:12px" class="tnum">' + esc(dateStr) + '</td>',
        '  <td style="padding:10px 12px;text-align:center">' + statusTag + '</td>',
        '  <td style="padding:10px 12px;text-align:right">',
        isConfirmed
          ? '    <button type="button" class="btn-cancel-reg" data-id="' + r.id + '" data-code="' + esc(r.code) + '" style="background:#FFF0F0;color:#B3261E;border:1px solid #F5C2C2;border-radius:8px;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer">Annuler</button>'
          : '    <span style="color:#999;font-size:11px">—</span>',
        '  </td>',
        '</tr>'
      );
    });

    html.push('</tbody></table></div>');
    existingWrap.innerHTML = html.join('');
  }

  function collectPayload() {
    var f19 = document.getElementById('f19');
    var f20 = document.getElementById('f20');
    var f21 = document.getElementById('f21');
    var f22 = document.getElementById('f22');

    return {
      event_slug: initialSettings ? initialSettings.event_slug : 'iftar-2027',
      event_title: f19 ? f19.value : 'Iftar communautaire',
      date_str: initialSettings ? initialSettings.date_str : 'Samedi 20 février 2027 · 17 h 15',
      location: initialSettings ? initialSettings.location : '174 rue Lafontaine',
      description: initialSettings ? initialSettings.description : '',
      total_seats: parseInt(f20 ? f20.value : 120, 10) || 120,
      max_per_reg: parseInt(f21 ? f21.value : 6, 10) || 6,
      deadline: f22 ? f22.value : '2027-02-18',
      is_open: getSwitch('Inscriptions ouvertes', true),
      opt_vege: getSwitch('Option « Repas végétarien »', true),
      opt_code: getSwitch('Code de confirmation', true),
      opt_agenda: getSwitch('Bouton « Ajouter à mon agenda »', true)
    };
  }

  function init() {
    loadSettings();
    loadRegistrations();

    // Surveillance des champs
    document.addEventListener('input', function(e) {
      if (e.target && e.target.closest('#sp-3')) markDirty();
    });
    document.addEventListener('change', function(e) {
      if (e.target && e.target.closest('#sp-3')) markDirty();
    });

    document.addEventListener('click', function(e) {
      var t = e.target;
      if (t && t.matches('button.sw') && t.closest('#sp-3')) {
        setTimeout(markDirty, 50);
      }

      // Enregistrer
      var isSave = t && (t.matches('header.top button.btn-gold') || t.closest('header.top button.btn-gold'));
      if (isSave) {
        e.preventDefault();
        e.stopPropagation();
        var btn = t.closest('header.top button.btn-gold') || t;
        btn.setAttribute('disabled', 'true');
        btn.textContent = 'Enregistrement…';

        var payload = collectPayload();
        fetch('/api/admin/events/settings', {
          method: 'PUT',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        .then(function(r) { return r.json(); })
        .then(function(d) {
          btn.textContent = 'Enregistrer';
          if (d && d.ok) {
            initialSettings = JSON.parse(JSON.stringify(d.settings || payload));
            setStatus(false, 'Tout est enregistré');
            toast('Paramètres d’inscription enregistrés avec succès.');
            loadRegistrations();
          } else {
            btn.removeAttribute('disabled');
            toast('Erreur : ' + (d.message || 'Échec de la sauvegarde.'));
          }
        })
        .catch(function() {
          btn.textContent = 'Enregistrer';
          btn.removeAttribute('disabled');
          toast('Erreur de communication avec le serveur.');
        });
        return;
      }

      // Annuler les changements
      var isCancel = t && (t.matches('header.top button.btn-onDark') || t.closest('header.top button.btn-onDark'));
      if (isCancel) {
        e.preventDefault();
        e.stopPropagation();
        if (initialSettings) {
          loadSettings();
          toast('Modifications annulées.');
        }
        return;
      }

      // Exporter CSV
      var isExport = t && (t.textContent.includes('Exporter la liste (.csv)') || t.closest('button')?.textContent.includes('Exporter la liste (.csv)'));
      if (isExport) {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = '/api/admin/events/export';
        return;
      }

      // Écrire aux inscrits
      var isMailto = t && (t.textContent.includes('Écrire aux inscrits') || t.closest('button')?.textContent.includes('Écrire aux inscrits'));
      if (isMailto) {
        e.preventDefault();
        e.stopPropagation();
        var emails = allRegistrations
          .filter(function(r) { return r.status === 'confirmed' && r.contact && r.contact.includes('@'); })
          .map(function(r) { return r.contact.trim(); });

        var uniqueEmails = Array.from(new Set(emails));
        if (uniqueEmails.length === 0) {
          alert('Aucune adresse courriel trouvée parmi les inscrits confirmés.');
          return;
        }

        var mailtoUrl = 'mailto:associationrdl.ascil@gmail.com?bcc=' + encodeURIComponent(uniqueEmails.join(',')) + '&subject=' + encodeURIComponent('Information — ' + (initialSettings ? initialSettings.event_title : 'Événement ASCIL'));
        window.location.href = mailtoUrl;
        return;
      }

      // Annuler une réservation individuelle
      if (t && t.matches('button.btn-cancel-reg')) {
        e.preventDefault();
        e.stopPropagation();
        var regId = t.getAttribute('data-id');
        var regCode = t.getAttribute('data-code');
        if (!confirm('Voulez-vous vraiment annuler l’inscription ' + regCode + ' ? Les places seront immédiatement libérées.')) {
          return;
        }

        t.setAttribute('disabled', 'true');
        t.textContent = 'Annulation…';

        fetch('/api/admin/events/registrations?id=' + regId, {
          method: 'DELETE',
          credentials: 'same-origin'
        })
        .then(function(r) { return r.json(); })
        .then(function(d) {
          if (d && d.ok) {
            toast('Inscription ' + regCode + ' annulée.');
            loadRegistrations();
          } else {
            t.removeAttribute('disabled');
            t.textContent = 'Annuler';
            toast('Erreur : ' + (d.message || 'Impossible d’annuler l’inscription.'));
          }
        })
        .catch(function() {
          t.removeAttribute('disabled');
          t.textContent = 'Annuler';
          toast('Erreur de connexion.');
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
'''

def update_file(path, script_tag, script_id):
    content = path.read_text(encoding='utf-8')
    m = re.search(r'<script type="__bundler/template">(.*?)</script>', content, re.S)
    if not m:
        raise ValueError(f"No __bundler/template in {path}")
    tpl = json.loads(m.group(1))

    # Supprime toute version antérieure de ce script
    pat = re.compile(r'<script id="' + re.escape(script_id) + r'">.*?</script>\s*', re.S)
    tpl = pat.sub('', tpl)

    # Insère immédiatement avant </body>
    idx_body = tpl.rindex('</body>')
    tpl = tpl[:idx_body] + script_tag + '\n' + tpl[idx_body:]

    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl

    i = content.index('<script type="__bundler/template">')
    j = content.index('</script>', i)
    new_content = content[:i] + '<script type="__bundler/template">' + enc + content[j:]
    path.write_text(new_content, encoding='utf-8')
    print(f"Modifié avec succès : {path.name} (script #{script_id})")

def main():
    # 1. Panneau superadmin / responsable événements
    panneau = ROOT / 'SA-Evenements.dc.html'
    update_file(panneau, ADMIN_EVENEMENTS_SYNC_SCRIPT, 'sa-evenements-sync')

    # 2. Pages d'inscription publiques
    for name in ['N3-Inscription.dc.html', 'M-N3-Inscription.dc.html', 'T-N3-Inscription.dc.html']:
        p = ROOT / name
        if p.exists():
            update_file(p, PUBLIC_INSCRIPTION_SYNC_SCRIPT, 'ascil-inscription-sync')

if __name__ == '__main__':
    main()

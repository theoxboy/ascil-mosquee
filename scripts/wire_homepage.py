"""Branchement dynamique de la page d'accueil, des statistiques (étape 2b) et du panneau superadmin.

1. SA-Panneau.dc.html :
   - Bandeau synthétique des statistiques réelles (Campagne, Visites, Événements, Sécurité)
   - Pré-remplit les champs et réglages depuis GET /api/admin/settings/home
   - Récupère les métriques en direct depuis GET /api/admin/stats
   - Détecte toute modification (texte, sélecteurs, interrupteurs, ordre)
   - Sauvegarde vers PUT /api/admin/settings/home lors du clic sur « Enregistrer »
   - Rétablit les valeurs en cas de clic sur « Annuler »

2. Main.dc.html, index.html, M-Accueil.dc.html, T-Accueil.dc.html :
   - Enregistre anonymement la visite via POST /api/views (sans cookies, sans IP)
   - Charge les réglages depuis le cache immédiat (localStorage) et l'API GET /api/settings/home
   - Applique en direct :
     • Coordonnées (adresse, courriel, facebook, lien itinéraire)
     • Heures de prière et calcul dynamique de la prochaine prière (compte à rebours, puces, footer, menu)
     • Campagne nouveau lieu (objectif, récolté, pourcentage, barre de progression)
     • Dernières annonces (titres, dates, résumés, liens)
     • Affichage / masquage de tous les widgets
     • Réordonnancement dynamique des 5 sections modulaires selon settings.ordre
"""

import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

STATS_BANNER_HTML = r'''   <!-- Bandeau des statistiques réelles (étape 2b) -->
   <div id="sa-stats-banner" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:2px 0 6px">
    <div style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Campagne</span>
      <span style="font-size:15px">💰</span>
     </div>
     <div id="stat-campagne-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-campagne-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
    <div style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Visites du site</span>
      <span style="font-size:15px">👁️</span>
     </div>
     <div id="stat-visits-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-visits-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
    <div style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Événements</span>
      <span style="font-size:15px">📅</span>
     </div>
     <div id="stat-events-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-events-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
    <div id="stat-card-sec" style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Sécurité & Accès</span>
      <span style="font-size:15px">🛡️</span>
     </div>
     <div id="stat-sec-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-sec-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
   </div>'''

PANNEAU_SYNC_SCRIPT = r'''<script id="sa-panneau-sync">
(function() {
  var lastSettings = null;
  var isDirty = false;

  function setStatus(dirty, msg) {
    isDirty = dirty;
    var dot = document.querySelector('header.top p.status span.sdot');
    var statusTxt = document.querySelector('header.top p.status');
    var saveBtn = document.querySelector('header.top button.btn-gold');
    var cancelBtn = document.querySelector('header.top button.btn-onDark');

    if (dot) dot.style.background = dirty ? '#C49A4A' : '#7FB89F';
    if (statusTxt) {
      var sdot = statusTxt.querySelector('span.sdot');
      statusTxt.innerHTML = '';
      if (sdot) statusTxt.appendChild(sdot);
      statusTxt.appendChild(document.createTextNode(msg || (dirty ? 'Changements non enregistrés' : 'Tout est enregistré')));
    }
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

  function toast(msg) {
    var t = document.getElementById('__sa_toast');
    if (!t) {
      t = document.createElement('div');
      t.id = '__sa_toast';
      t.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:9999;background:#1E2B26;color:#fff;padding:12px 24px;border-radius:999px;font-weight:600;font-size:14px;box-shadow:0 10px 24px rgba(0,0,0,.25);transition:opacity .3s ease';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    t.hidden = false;
    clearTimeout(t._timer);
    t._timer = setTimeout(function() {
      t.style.opacity = '0';
      setTimeout(function() { t.hidden = true; }, 300);
    }, 2800);
  }

  function setVal(id, v) {
    var el = document.getElementById(id);
    if (el && v != null) el.value = v;
  }
  function getVal(id) {
    var el = document.getElementById(id);
    return el ? el.value.trim() : '';
  }

  function setSwitch(label, on) {
    var sw = document.querySelector('button.sw[aria-label="' + label + '"]');
    if (sw) {
      sw.setAttribute('aria-checked', on ? 'true' : 'false');
      if (on) sw.style.background = '#0E4D3C';
      else sw.style.background = '#CFC6B1';
    }
  }
  function getSwitch(label, fallback) {
    var sw = document.querySelector('button.sw[aria-label="' + label + '"]');
    if (sw) return sw.getAttribute('aria-checked') === 'true';
    return fallback != null ? fallback : true;
  }

  function loadStats() {
    fetch('/api/admin/stats', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !d.ok) return;

        // 1. Campagne
        if (d.campagne) {
          var cVal = document.getElementById('stat-campagne-val');
          var cSub = document.getElementById('stat-campagne-sub');
          if (cVal) cVal.textContent = (d.campagne.recolte || 0).toLocaleString('fr-CA') + ' $';
          if (cSub) cSub.textContent = (d.campagne.pct || 0) + ' % de ' + (d.campagne.objectif || 0).toLocaleString('fr-CA') + ' $';
        }

        // 2. Visites
        if (d.visits) {
          var vVal = document.getElementById('stat-visits-val');
          var vSub = document.getElementById('stat-visits-sub');
          if (vVal) vVal.textContent = (d.visits.total || 0).toLocaleString('fr-CA') + ' visites';
          if (vSub) vSub.textContent = (d.visits.today || 0) + ' aujourd’hui · ' + (d.visits.week || 0) + ' ces 7 jours';
        }

        // 3. Événements
        if (d.events) {
          var eVal = document.getElementById('stat-events-val');
          var eSub = document.getElementById('stat-events-sub');
          if (eVal) eVal.textContent = (d.events.count || 0) + ' événement(s)';
          if (eSub) eSub.textContent = (d.events.registrations || 0) + ' inscription(s)';
        }

        // 4. Sécurité
        var secCard = document.getElementById('stat-card-sec');
        if (d.security) {
          if (secCard) secCard.style.display = '';
          var sVal = document.getElementById('stat-sec-val');
          var sSub = document.getElementById('stat-sec-sub');
          if (sVal) sVal.textContent = (d.security.activeAdmins || 0) + ' compte(s) actif(s)';
          if (sSub) sSub.textContent = (d.security.activeSessions || 0) + ' session(s) · ' + (d.security.recentFailures || 0) + ' échec récent';
        } else if (secCard) {
          secCard.style.display = 'none';
        }
      })
      .catch(function() {});
  }

  function populateUI(s) {
    if (!s) return;
    lastSettings = JSON.parse(JSON.stringify(s));

    if (s.general) {
      setVal('f-mail', s.general.email);
      setVal('f-fb', s.general.facebook);
      setVal('f-adr', s.general.address);
      setVal('f-ville', s.general.city);
      setVal('f-map', s.general.mapUrl);
    }

    if (s.chargement) setVal('f-dur', s.chargement.duration === 'rapide' ? 'Rapide (environ 1,5 s)' : 'Normale (environ 3 s)');

    if (s.hero) {
      setVal('f-h1', s.hero.h1);
      setVal('f-h2', s.hero.h2);
    }

    if (s.priere) {
      setVal('h-0', s.priere.fajr);
      setVal('h-1', s.priere.lever);
      setVal('h-2', s.priere.dohr);
      setVal('h-3', s.priere.jumua);
      setVal('h-4', s.priere.asr);
      setVal('h-5', s.priere.maghreb);
      setVal('h-6', s.priere.icha);
    }

    if (s.acces && Array.isArray(s.acces.cartes)) {
      s.acces.cartes.forEach(function(c, i) {
        setVal('k-' + i, c.lien);
      });
    }

    if (s.campagne) {
      setVal('f-obj', s.campagne.objectif ? String(s.campagne.objectif).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '350 000');
      setVal('f-rec', s.campagne.recolte ? String(s.campagne.recolte).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '0');
      setVal('f-int', s.campagne.btnInterac);
      setVal('f-sui', s.campagne.btnSuivre);
    }

    if (s.annonces) {
      setVal('f-tous', s.annonces.btnTous);
      if (Array.isArray(s.annonces.items)) {
        s.annonces.items.forEach(function(item, idx) {
          setVal('a-d-' + idx, item.date);
          setVal('a-t-' + idx, item.titre);
          setVal('a-r-' + idx, item.resume);
          setVal('a-l-' + idx, item.lien);
        });
      }
    }

    if (s.bienvenue) setVal('f-bv', s.bienvenue.lien);
    if (s.invitation) setVal('f-inv', s.invitation.lien);

    if (s.pied) {
      setVal('f-tcom', s.pied.tcom);
      setVal('f-cciq', s.pied.cciq);
    }

    if (s.on) {
      setSwitch('Afficher l’écran de chargement', s.on.chargement !== false);
      setSwitch('Afficher le bandeau du haut', s.on.bandeau !== false);
      setSwitch('Compte à rebours', s.on.compte !== false);
      setSwitch('Courriel', s.on.mail !== false);
      setSwitch('Lien Facebook', s.on.fb !== false);
      setSwitch('Bouton « Faire un don »', s.on.don !== false);
      setSwitch('Sélecteur de langue', s.on.langue !== false);
      setSwitch('Horaires', s.on.horaires !== false);
      setSwitch('À propos', s.on.apropos !== false);
      setSwitch('Services', s.on.services !== false);
      setSwitch('Événements', s.on.evenements !== false);
      setSwitch('Ressources', s.on.ressources !== false);
      setSwitch('Contact', s.on.contact !== false);
      setSwitch('Afficher le héros', s.on.hero !== false);
      setSwitch('Afficher la prochaine prière', s.on.priere !== false);
      setSwitch('Date hégirienne', s.on.hegirien !== false);
      setSwitch('Barre de progression', s.on.progression !== false);
      setSwitch('Puces des prières', s.on.puces !== false);
      setSwitch('Afficher les accès rapides', s.on.acces !== false);
      setSwitch('Afficher la campagne', s.on.campagne !== false);
      setSwitch('Barre de progression de la campagne', s.on.barre !== false);
      setSwitch('Afficher les annonces', s.on.annonces !== false);
      setSwitch('Afficher Bienvenue aux visiteurs', s.on.bienvenue !== false);
      setSwitch('Afficher l’invitation', s.on.invitation !== false);
      setSwitch('Afficher le bouton Revenir en haut', s.on.haut !== false);
      setSwitch('Horaires résumés', s.on.pHor !== false);
      setSwitch('Bouton « Itinéraire »', s.on.pIti !== false);
      setSwitch('Page Facebook de l’ASCIL', s.on.pFb !== false);
      setSwitch('TCOM — annonces Ramadan et Aïd', s.on.pTcom !== false);
      setSwitch('CCIQ — annonces Ramadan et Aïd', s.on.pCciq !== false);
    }

    setStatus(false, 'Tout est enregistré');
  }

  function collectPayload() {
    var cleanNum = function(v) { return parseInt(String(v || '').replace(/[^\d]/g, ''), 10) || 0; };
    var durVal = getVal('f-dur');
    var isRapide = durVal.toLowerCase().indexOf('rapide') !== -1;

    var ordre = [];
    var NAME_TO_ID = {
      'Accès rapides': 'acces',
      'Campagne nouveau lieu': 'campagne',
      'Dernières annonces': 'annonces',
      'Bienvenue aux visiteurs': 'bienvenue',
      'Invitation': 'invitation'
    };
    var olItems = document.querySelectorAll('#w-ordre ol li.item');
    olItems.forEach(function(li) {
      for (var name in NAME_TO_ID) {
        if (li.textContent.indexOf(name) !== -1) {
          ordre.push(NAME_TO_ID[name]);
          break;
        }
      }
    });
    if (!ordre.length) {
      ordre = lastSettings && lastSettings.ordre ? lastSettings.ordre : ['acces', 'campagne', 'annonces', 'bienvenue', 'invitation'];
    }

    return {
      general: {
        email: getVal('f-mail') || 'associationrdl.ascil@gmail.com',
        facebook: getVal('f-fb') || 'https://www.facebook.com/',
        address: getVal('f-adr') || '174 rue Lafontaine',
        city: getVal('f-ville') || 'Rivière-du-Loup (Québec)',
        mapUrl: getVal('f-map') || 'https://maps.google.com/?q=174+rue+Lafontaine+Riviere-du-Loup'
      },
      ordre: ordre,
      on: {
        chargement: getSwitch('Afficher l’écran de chargement'),
        bandeau: getSwitch('Afficher le bandeau du haut'),
        compte: getSwitch('Compte à rebours'),
        mail: getSwitch('Courriel'),
        fb: getSwitch('Lien Facebook'),
        don: getSwitch('Bouton « Faire un don »'),
        langue: getSwitch('Sélecteur de langue'),
        horaires: getSwitch('Horaires'),
        apropos: getSwitch('À propos'),
        services: getSwitch('Services'),
        evenements: getSwitch('Événements'),
        ressources: getSwitch('Ressources'),
        contact: getSwitch('Contact'),
        hero: getSwitch('Afficher le héros'),
        priere: getSwitch('Afficher la prochaine prière'),
        hegirien: getSwitch('Date hégirienne'),
        progression: getSwitch('Barre de progression'),
        puces: getSwitch('Puces des prières'),
        acces: getSwitch('Afficher les accès rapides'),
        campagne: getSwitch('Afficher la campagne'),
        barre: getSwitch('Barre de progression de la campagne'),
        annonces: getSwitch('Afficher les annonces'),
        bienvenue: getSwitch('Afficher Bienvenue aux visiteurs'),
        invitation: getSwitch('Afficher l’invitation'),
        haut: getSwitch('Afficher le bouton Revenir en haut'),
        pHor: getSwitch('Horaires résumés'),
        pIti: getSwitch('Bouton « Itinéraire »'),
        pFb: getSwitch('Page Facebook de l’ASCIL'),
        pTcom: getSwitch('TCOM — annonces Ramadan et Aïd'),
        pCciq: getSwitch('CCIQ — annonces Ramadan et Aïd'),
        pMail: getSwitch('Courriel', true)
      },
      chargement: {
        duration: isRapide ? 'rapide' : 'normale'
      },
      hero: {
        h1: getVal('f-h1') || 'Page : Horaires du mois',
        h2: getVal('f-h2') || 'Page : Faire un don'
      },
      priere: {
        fajr: getVal('h-0'),
        lever: getVal('h-1'),
        dohr: getVal('h-2'),
        jumua: getVal('h-3'),
        asr: getVal('h-4'),
        maghreb: getVal('h-5'),
        icha: getVal('h-6')
      },
      acces: {
        cartes: [
          { id: 'vendredi', on: getSwitch('Afficher Prière du vendredi', true), lien: getVal('k-0') || 'Page : Horaires du mois' },
          { id: 'trouver', on: getSwitch('Afficher Nous trouver', true), lien: getVal('k-1') || 'Page : Contact' },
          { id: 'campagne', on: getSwitch('Afficher Nouveau lieu — campagne en cours', true), lien: getVal('k-2') || 'Page : Faire un don' }
        ]
      },
      campagne: {
        objectif: cleanNum(getVal('f-obj')) || 350000,
        recolte: cleanNum(getVal('f-rec')),
        btnInterac: getVal('f-int') || 'Page : Faire un don',
        btnSuivre: getVal('f-sui') || 'Page : Campagne en direct'
      },
      annonces: {
        max: 3,
        btnTous: getVal('f-tous') || 'Page : Événements',
        items: [
          {
            id: 0,
            date: getVal('a-d-0') || 'Oct. 2026',
            titre: getVal('a-t-0') || 'Lancement de la campagne nouveau lieu',
            resume: getVal('a-r-0') || 'Objectif 350 000 $ pour acquérir et transformer un bâtiment en mosquée.',
            lien: getVal('a-l-0') || 'Page : Événements',
            on: true
          },
          {
            id: 1,
            date: getVal('a-d-1') || '27 mai 2026',
            titre: getVal('a-t-1') || 'Aïd al-Adha 1447',
            resume: getVal('a-r-1') || 'Prière célébrée à la salle louée du 15 rue Frontenac.',
            lien: getVal('a-l-1') || 'Page : Événements',
            on: true
          },
          {
            id: 2,
            date: getVal('a-d-2') || '25 avr. 2026',
            titre: getVal('a-t-2') || 'Journée de parrainage d’orphelins',
            resume: getVal('a-r-2') || 'Avec l’organisme Soleil des Orphelins, au 174 rue Lafontaine.',
            lien: getVal('a-l-2') || 'Page : Événements',
            on: true
          }
        ]
      },
      bienvenue: {
        lien: getVal('f-bv') || 'Page : Contact'
      },
      invitation: {
        lien: getVal('f-inv') || 'Page : Contact'
      },
      pied: {
        tcom: getVal('f-tcom') || 'https://www.tcomq.ca/',
        cciq: getVal('f-cciq') || ''
      }
    };
  }

  function init() {
    fetch('/api/admin/settings/home', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (d && d.ok && d.settings) {
          populateUI(d.settings);
        }
      })
      .catch(function() {});

    loadStats();
  }

  document.addEventListener('input', function() { markDirty(); });
  document.addEventListener('change', function() { markDirty(); });
  document.addEventListener('click', function(e) {
    var t = e.target;
    if (t && (t.matches('button.sw') || t.closest('button.sw'))) {
      setTimeout(markDirty, 50);
    }
    if (t && (t.matches('#w-ordre button.ico') || t.closest('#w-ordre button.ico'))) {
      setTimeout(markDirty, 50);
    }
    if (t && t.closest('.seg')) {
      setTimeout(markDirty, 50);
    }

    var isSave = t && (t.matches('header.top button.btn-gold') || t.closest('header.top button.btn-gold'));
    if (isSave) {
      e.preventDefault();
      e.stopPropagation();
      var btn = t.closest('header.top button.btn-gold') || t;
      btn.setAttribute('disabled', 'true');
      btn.textContent = 'Enregistrement…';

      var payload = collectPayload();
      fetch('/api/admin/settings/home', {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        btn.textContent = 'Enregistrer';
        if (d && d.ok) {
          lastSettings = JSON.parse(JSON.stringify(d.settings || payload));
          setStatus(false, 'Tout est enregistré');
          toast('Réglages enregistrés. Le site est à jour.');
          loadStats();
        } else {
          btn.removeAttribute('disabled');
          toast('Erreur : ' + (d.message || 'La sauvegarde a échoué.'));
        }
      })
      .catch(function() {
        btn.textContent = 'Enregistrer';
        btn.removeAttribute('disabled');
        toast('Erreur de connexion avec le serveur.');
      });
      return;
    }

    var isCancel = t && (t.matches('header.top button.btn-onDark') || t.closest('header.top button.btn-onDark'));
    if (isCancel) {
      e.preventDefault();
      e.stopPropagation();
      if (lastSettings) {
        populateUI(lastSettings);
        toast('Changements annulés.');
      }
      return;
    }
  }, true);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
'''

PUBLIC_HOME_SYNC_SCRIPT = r'''<script id="ascil-home-sync">
(function() {
  var URL_MAP = {
    'Page : Horaires du mois': 'Horaires.dc.html',
    'Page : Rappel de prière': 'N3-Rappel.dc.html',
    'Page : Langue de la khutba': 'N2-Khutba.dc.html',
    'Page : Faire un don': 'Dons.dc.html',
    'Page : Campagne en direct': 'N3-Campagne.dc.html',
    'Page : Événements': 'Evenements.dc.html',
    'Page : Calendrier du mois': 'N3-Calendrier.dc.html',
    'Page : Contact': 'Contact.dc.html',
    'Page : Ressources': 'Ressources.dc.html',
    'Page : À propos': 'APropos.dc.html',
    'Page : Services': 'Services.dc.html'
  };

  function toUrl(val) {
    if (!val) return '';
    return URL_MAP[val] || val;
  }

  function escHtml(str) {
    var d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
  }
  function escAttr(str) {
    return String(str || '').replace(/"/g, '&quot;');
  }

  function updatePrayerDisplay(p, on) {
    var tz = 'America/Toronto';
    var d = new Date();
    var parts = [];
    try {
      parts = new Intl.DateTimeFormat('en-US', { timeZone: tz, hour: '2-digit', minute: '2-digit', hourCycle: 'h23', weekday: 'short' }).formatToParts(d);
    } catch (e) {}
    var g = function(t) { var x = parts.find(function(q) { return q.type === t; }); return x ? x.value : ''; };
    var mins = (parseInt(g('hour'), 10) % 24) * 60 + parseInt(g('minute'), 10);
    var isFri = g('weekday') === 'Fri';

    function parseMins(str) {
      if (!str || !str.includes(':')) return null;
      var bits = str.trim().split(':');
      var h = parseInt(bits[0], 10), m = parseInt(bits[1], 10);
      if (isNaN(h) || isNaN(m)) return null;
      return h * 60 + m;
    }

    var list = [];
    if (p.fajr) list.push({ n: 'Fajr', t: parseMins(p.fajr), val: p.fajr });
    if (isFri && p.jumua) list.push({ n: 'Jumu’a', t: parseMins(p.jumua), val: p.jumua });
    else if (!isFri && p.dohr) list.push({ n: 'Dohr', t: parseMins(p.dohr), val: p.dohr });
    if (p.asr) list.push({ n: 'Asr', t: parseMins(p.asr), val: p.asr });
    if (p.maghreb) list.push({ n: 'Maghreb', t: parseMins(p.maghreb), val: p.maghreb });
    if (p.icha) list.push({ n: 'Icha', t: parseMins(p.icha), val: p.icha });

    var known = list.filter(function(x) { return x.t !== null; });
    if (!known.length) return;

    var next = known.find(function(x) { return x.t > mins; });
    var tomorrow = false;
    if (!next) {
      next = known[0];
      tomorrow = true;
    }

    var diff = next.t - mins + (tomorrow ? 1440 : 0);
    var hh = Math.floor(diff / 60), mm = diff % 60;
    var countdown = 'dans ' + (hh ? hh + ' h ' + String(mm).padStart(2, '0') : mm + ' min');

    var topNext = document.querySelector('header.hdr .tnum strong');
    var topCountdown = document.querySelector('header.hdr .tnum span.hide-m:last-child');
    if (topNext) {
      topNext.innerHTML = escHtml(next.n) + '<span class="hide-m"> — ' + (tomorrow ? 'demain' : 'aujourd’hui') + '</span>&nbsp;' + escHtml(next.val);
    }
    if (topCountdown) {
      topCountdown.textContent = '· ' + countdown;
    }

    var ppTitle = document.getElementById('pp-title');
    if (ppTitle) {
      var ppWrap = ppTitle.closest('.pad-m');
      if (ppWrap) {
        var ppName = ppWrap.querySelector('.serif');
        if (ppName) ppName.textContent = next.n;
        var ppTime = ppWrap.querySelector('.big-m');
        if (ppTime) ppTime.textContent = next.val;
        var ppCd = ppWrap.querySelector('.tnum p:last-child');
        if (ppCd) {
          var live = ppCd.querySelector('.live');
          ppCd.innerHTML = '';
          if (live) ppCd.appendChild(live);
          ppCd.appendChild(document.createTextNode(countdown));
        }
        var selInfo = ppWrap.querySelector('div.stack-m p[aria-live="polite"]');
        if (selInfo) {
          selInfo.innerHTML = '<strong>' + escHtml(next.n) + '</strong> — ' + escHtml(next.val) + ', ' + countdown;
        }

        var chips = ppWrap.querySelectorAll('.g5 button.chip');
        var chipValues = [
          { n: 'Fajr', v: p.fajr },
          { n: isFri ? 'Jumu’a' : 'Dohr', v: isFri ? p.jumua : p.dohr },
          { n: 'Asr', v: p.asr },
          { n: 'Maghreb', v: p.maghreb },
          { n: 'Icha', v: p.icha }
        ];
        chips.forEach(function(chip, idx) {
          if (chipValues[idx]) {
            var timeSpan = chip.querySelector('span:last-child');
            if (timeSpan) timeSpan.textContent = chipValues[idx].v || '—';
          }
        });

        var g5 = ppWrap.querySelector('.g5');
        if (g5 && on.puces === false) g5.style.display = 'none';
        else if (g5) g5.style.display = '';

        var prog = ppWrap.querySelector('.prog');
        if (prog && on.progression === false) prog.style.display = 'none';
        else if (prog) prog.style.display = '';
      }
    }

    var footHor = document.querySelector('footer .g4 > div:first-child > p.tnum');
    if (footHor) {
      footHor.textContent = 'Fajr ' + (p.fajr || '—') + ' — Jumu’a ' + (p.jumua || '12:30') + ' — Icha ' + (p.icha || '—');
    }

    var mobDrawer = document.querySelector('.menu-in .tnum');
    if (mobDrawer) {
      var cells = mobDrawer.querySelectorAll('div > div:last-child');
      if (cells.length >= 3) {
        cells[0].textContent = p.fajr || '—';
        cells[1].textContent = isFri ? (p.jumua || '12:30') : (p.dohr || '—');
        cells[2].textContent = p.icha || '—';
      }
    }
  }

  function applySettings(s) {
    if (!s) return;
    try {
      if (s.on && s.on.chargement === false) {
        var ld = document.querySelector('div[role="status"][aria-label="Chargement"]');
        if (ld) { ld.style.display = 'none'; ld.remove(); }
      }

      var topBar = document.querySelector('header.hdr > div:first-child');
      if (topBar && s.on) {
        if (s.on.bandeau === false) {
          topBar.style.display = 'none';
        } else {
          topBar.style.display = '';
          var topMail = topBar.querySelector('a[href^="mailto:"]');
          var topFb = topBar.querySelector('a[href*="facebook.com"]');
          var topCompte = topBar.querySelector('.tnum');
          if (topMail) topMail.style.display = s.on.mail === false ? 'none' : '';
          if (topFb) topFb.style.display = s.on.fb === false ? 'none' : '';
          if (topCompte) {
            var cdSpan = topCompte.querySelector('.hide-m:last-child');
            if (cdSpan) cdSpan.style.display = s.on.compte === false ? 'none' : '';
          }
        }
      }

      if (s.general) {
        if (s.general.email) {
          document.querySelectorAll('a[href^="mailto:"]').forEach(function(a) {
            a.href = 'mailto:' + s.general.email;
            if (a.textContent.includes('@')) {
              var svg = a.querySelector('svg');
              if (svg) {
                a.innerHTML = '';
                a.appendChild(svg);
                a.appendChild(document.createTextNode(s.general.email));
              } else {
                a.textContent = s.general.email;
              }
            }
          });
        }
        if (s.general.facebook) {
          document.querySelectorAll('a[href*="facebook.com"]').forEach(function(a) {
            a.href = s.general.facebook;
          });
        }
        if (s.general.mapUrl) {
          document.querySelectorAll('a[href*="maps.google.com"]').forEach(function(a) {
            a.href = s.general.mapUrl;
          });
        }
        if (s.general.address || s.general.city) {
          var footAdr = document.querySelector('footer .g4 > div:first-child > p:nth-of-type(1)');
          if (footAdr) {
            footAdr.innerHTML = (s.general.address || '174 rue Lafontaine') + '<br>' + (s.general.city || 'Rivière-du-Loup (Québec)');
          }
          var cardAdr = document.querySelector('section[aria-label="Accès rapides"] a[href="Contact.dc.html"] p.h3');
          if (cardAdr) {
            cardAdr.textContent = 'Nous trouver — ' + (s.general.address || '174 rue Lafontaine');
          }
        }
      }

      if (s.on) {
        var donBtn = document.querySelectorAll('.don-btn');
        donBtn.forEach(function(b) { b.style.display = s.on.don === false ? 'none' : ''; });
        var langDesk = document.querySelectorAll('.lang-desk');
        langDesk.forEach(function(l) { l.style.display = s.on.langue === false ? 'none' : ''; });

        var menuItems = [
          ['horaires', 'Horaires.dc.html'],
          ['apropos', 'APropos.dc.html'],
          ['services', 'Services.dc.html'],
          ['evenements', 'Evenements.dc.html'],
          ['ressources', 'Ressources.dc.html'],
          ['contact', 'Contact.dc.html']
        ];
        menuItems.forEach(function(item) {
          var k = item[0], href = item[1];
          if (s.on[k] === false) {
            document.querySelectorAll('.nav-desk a[href="' + href + '"], nav[aria-label="Menu mobile"] a[href="' + href + '"]').forEach(function(a) {
              var parentDd = a.closest('.dd');
              if (parentDd) parentDd.style.display = 'none';
              else a.style.display = 'none';
            });
          } else {
            document.querySelectorAll('.nav-desk a[href="' + href + '"], nav[aria-label="Menu mobile"] a[href="' + href + '"]').forEach(function(a) {
              var parentDd = a.closest('.dd');
              if (parentDd) parentDd.style.display = '';
              else a.style.display = '';
            });
          }
        });
      }

      var heroSec = document.querySelector('section[aria-labelledby="hero-t"]');
      if (heroSec && s.on) {
        heroSec.style.display = s.on.hero === false ? 'none' : '';
        if (s.hero) {
          var h1Btn = heroSec.querySelector('.btn-gold');
          var h2Btn = heroSec.querySelector('.btn-ghost');
          if (h1Btn && s.hero.h1) h1Btn.href = toUrl(s.hero.h1);
          if (h2Btn && s.hero.h2) h2Btn.href = toUrl(s.hero.h2);
        }
      }

      var priereSec = document.querySelector('section[aria-labelledby="pp-title"]');
      if (priereSec && s.on) {
        priereSec.style.display = s.on.priere === false ? 'none' : '';
      }
      if (s.priere) {
        updatePrayerDisplay(s.priere, s.on || {});
      }

      var accesSec = document.querySelector('section[aria-label="Accès rapides"]');
      if (accesSec && s.on) {
        accesSec.style.display = s.on.acces === false ? 'none' : '';
        if (s.acces && Array.isArray(s.acces.cartes)) {
          var cards = accesSec.querySelectorAll('.wrap.g3 > a.card');
          s.acces.cartes.forEach(function(k, idx) {
            if (cards[idx]) {
              cards[idx].style.display = k.on === false ? 'none' : '';
              if (k.lien) cards[idx].href = toUrl(k.lien);
            }
          });
        }
      }

      var campSec = document.querySelector('section[aria-labelledby="camp-t"]');
      if (campSec && s.on) {
        campSec.style.display = s.on.campagne === false ? 'none' : '';
      }
      if (campSec && s.campagne) {
        var obj = Number(s.campagne.objectif) || 350000;
        var rec = Number(s.campagne.recolte) || 0;
        var pct = Math.min(100, Math.round((rec / obj) * 100));

        var objEl = campSec.querySelector('p.serif.tnum');
        if (objEl) objEl.textContent = obj.toLocaleString('fr-CA') + ' $';

        var barWrap = campSec.querySelector('div[role="progressbar"]');
        var recText = campSec.querySelector('p.tnum:not(.serif)');
        var noRecMsg = campSec.querySelector('p.ph');

        if (s.on && s.on.barre === false) {
          if (barWrap) barWrap.style.display = 'none';
        } else if (barWrap) {
          barWrap.style.display = '';
        }

        if (rec > 0) {
          if (barWrap) {
            barWrap.setAttribute('aria-valuemax', String(obj));
            var bar = barWrap.querySelector('.bar');
            if (bar) bar.style.width = pct + '%';
          }
          if (recText) {
            recText.style.display = '';
            recText.textContent = rec.toLocaleString('fr-CA') + ' $ récoltés · ' + pct + ' %';
          }
          if (noRecMsg) noRecMsg.style.display = 'none';
        } else {
          if (barWrap) barWrap.style.display = 'none';
          if (recText) recText.style.display = 'none';
          if (noRecMsg) noRecMsg.style.display = '';
        }

        if (s.campagne.btnInterac) {
          var btnInt = campSec.querySelector('a.btn-green');
          if (btnInt) btnInt.href = toUrl(s.campagne.btnInterac);
        }
        if (s.campagne.btnSuivre) {
          var btnSui = campSec.querySelector('a.link');
          if (btnSui) btnSui.href = toUrl(s.campagne.btnSuivre);
        }
      }

      var annSec = document.querySelector('section[aria-labelledby="ann-t"]');
      if (annSec && s.on) {
        annSec.style.display = s.on.annonces === false ? 'none' : '';
      }
      if (annSec && s.annonces) {
        if (s.annonces.btnTous) {
          var tousLink = annSec.querySelector('a.link');
          if (tousLink) tousLink.href = toUrl(s.annonces.btnTous);
        }
        if (Array.isArray(s.annonces.items)) {
          var max = s.annonces.max || 3;
          var activeItems = s.annonces.items.filter(function(a) { return a.on !== false; }).slice(0, max);
          var annContainer = annSec.querySelector('.g3');
          if (annContainer && activeItems.length) {
            annContainer.innerHTML = activeItems.map(function(item) {
              return '<a class="card" href="' + escAttr(toUrl(item.lien || 'Page : Événements')) + '">'
                + '<span class="pill tnum" style="background:#0E4D3C;color:#fff">' + escHtml(item.date) + '</span>'
                + '<p class="h3" style="margin-top:16px;font-size:20px">' + escHtml(item.titre) + '</p>'
                + '<p class="muted" style="margin:8px 0 0">' + escHtml(item.resume) + '</p>'
                + '</a>';
            }).join('');
          }
        }
      }

      var bvSec = document.querySelector('section[aria-labelledby="bv-t"]');
      if (bvSec && s.on) {
        bvSec.style.display = s.on.bienvenue === false ? 'none' : '';
        if (s.bienvenue && s.bienvenue.lien) {
          var bvLink = bvSec.querySelector('a.link');
          if (bvLink) bvLink.href = toUrl(s.bienvenue.lien);
        }
      }

      var invSec = document.querySelector('section[aria-label="Invitation"]');
      if (invSec && s.on) {
        invSec.style.display = s.on.invitation === false ? 'none' : '';
        if (s.invitation && s.invitation.lien) {
          var invBtn = invSec.querySelector('a.btn-green');
          if (invBtn) invBtn.href = toUrl(s.invitation.lien);
        }
      }

      var toTop = document.querySelector('.totop');
      if (toTop && s.on) {
        toTop.style.display = s.on.haut === false ? 'none' : '';
      }

      if (s.pied) {
        if (s.pied.tcom) {
          var tcom = document.querySelector('a[href*="tcomq.ca"]');
          if (tcom) tcom.href = s.pied.tcom;
        }
        if (s.pied.cciq) {
          var cciq = document.querySelector('footer a[href="#"]:last-of-type');
          if (cciq && s.pied.cciq) cciq.href = s.pied.cciq;
        }
      }
      if (s.on) {
        var footRows = document.querySelectorAll('footer ul:last-of-type li');
        if (footRows.length >= 4) {
          footRows[0].style.display = s.on.pFb === false ? 'none' : '';
          footRows[1].style.display = s.on.pTcom === false ? 'none' : '';
          footRows[2].style.display = s.on.pCciq === false ? 'none' : '';
          footRows[3].style.display = s.on.pMail === false ? 'none' : '';
        }
        var footIti = document.querySelector('footer a.btn-gold');
        if (footIti) footIti.style.display = s.on.pIti === false ? 'none' : '';
        var footHor = document.querySelector('footer .g4 > div:first-child > p.tnum');
        if (footHor) footHor.style.display = s.on.pHor === false ? 'none' : '';
      }

      if (Array.isArray(s.ordre) && s.ordre.length) {
        var main = document.querySelector('main.pagein');
        if (main) {
          var secMap = {
            acces: main.querySelector('section[aria-label="Accès rapides"]'),
            campagne: main.querySelector('section[aria-labelledby="camp-t"]'),
            annonces: main.querySelector('section[aria-labelledby="ann-t"]'),
            bienvenue: main.querySelector('section[aria-labelledby="bv-t"]'),
            invitation: main.querySelector('section[aria-label="Invitation"]')
          };
          var anchor = main.querySelector('.totop') || null;
          s.ordre.forEach(function(id) {
            var el = secMap[id];
            if (el && main.contains(el)) {
              if (anchor) main.insertBefore(el, anchor);
              else main.appendChild(el);
            }
          });
        }
      }
    } catch (err) {
      console.warn('[ascil-sync] applySettings error:', err);
    }
  }

  // 1. Enregistrement anonyme de la visite (sans cookies, sans IP)
  try {
    var pName = location.pathname || '/';
    if (!sessionStorage.getItem('ascil_viewed_' + pName)) {
      sessionStorage.setItem('ascil_viewed_' + pName, '1');
      fetch('/api/views', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: pName })
      }).catch(function() {});
    }
  } catch (e) {}

  // 2. Cache local immédiat
  try {
    var cached = localStorage.getItem('ascil_home_settings');
    if (cached) applySettings(JSON.parse(cached));
  } catch (e) {}

  // 3. Mise à jour en direct
  function syncLive() {
    fetch('/api/settings/home')
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (d && d.ok && d.settings) {
          try { localStorage.setItem('ascil_home_settings', JSON.stringify(d.settings)); } catch (e) {}
          applySettings(d.settings);
        }
      })
      .catch(function() {});
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncLive);
  } else {
    syncLive();
  }
})();
</script>
'''

def update_file(path, script_tag, script_id, inject_html=None, inject_anchor=None):
    content = path.read_text(encoding='utf-8')
    m = re.search(r'<script type="__bundler/template">(.*?)</script>', content, re.S)
    if not m:
        raise ValueError(f"No __bundler/template in {path}")
    tpl = json.loads(m.group(1))

    # Supprime toute version antérieure de ce script
    pat = re.compile(r'<script id="' + re.escape(script_id) + r'">.*?</script>\s*', re.S)
    tpl = pat.sub('', tpl)

    # Injection HTML optionnelle (ex. bandeau stats)
    if inject_html and inject_anchor and inject_anchor in tpl:
        # Supprime ancienne version du bandeau si présente
        tpl = re.sub(r'\s*<!-- Bandeau des statistiques réelles \(étape 2b\) -->.*?</div>\s*</div>', '', tpl, flags=re.S)
        idx_anchor = tpl.index(inject_anchor) + len(inject_anchor)
        tpl = tpl[:idx_anchor] + '\n' + inject_html + tpl[idx_anchor:]

    # Insère immédiatement avant </body>
    idx_body = tpl.rindex('</body>')
    tpl = tpl[:idx_body] + script_tag + '\n' + tpl[idx_body:]

    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl

    i = content.index('<script type="__bundler/template">') + len('<script type="__bundler/template">')
    j = content.index('</script>', i)
    new_content = content[:i] + enc + content[j:]
    path.write_text(new_content, encoding='utf-8')
    print(f"Modifié avec succès : {path.name} (script #{script_id})")

def main():
    # 1. Panneau superadmin (avec bandeau stats)
    panneau = ROOT / 'SA-Panneau.dc.html'
    intro_anchor = 'L’aperçu change tout de suite ; le site, après <strong>Enregistrer</strong>.</p>\n   </div>'
    update_file(panneau, PANNEAU_SYNC_SCRIPT, 'sa-panneau-sync', inject_html=STATS_BANNER_HTML, inject_anchor=intro_anchor)

    # 2. Pages d'accueil publiques
    for name in ['Main.dc.html', 'index.html', 'M-Accueil.dc.html', 'T-Accueil.dc.html']:
        p = ROOT / name
        if p.exists():
            update_file(p, PUBLIC_HOME_SYNC_SCRIPT, 'ascil-home-sync')

if __name__ == '__main__':
    main()

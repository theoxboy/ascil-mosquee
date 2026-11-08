"""Boîte de réception (étape S2) : écran « Demandes reçues » et formulaire Contact.

- Panneau SA-Contact : nouvel onglet « Demandes reçues » (premier onglet de la rubrique Contact) :
  filtres (statut, formulaire, recherche), une carte par demande, statut nouveau / lu / traité,
  « Répondre » (courriel ou téléphone), suppression définitive après confirmation.
  Routes : GET / PATCH / DELETE /api/admin/forms (table form_messages, migration 0009).
- Page publique Contact (PC, M-, T-) : le formulaire n'ouvre plus le logiciel de courriel, il envoie
  le message à POST /api/forms (champ piège invisible, délai minimal, limite d'envois).

Ordre : après wire_services.py, avant fix_inputs.py. Idempotent.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def rep(tpl, old, new, count=1):
    n = tpl.count(old)
    assert n == count, f'{n} occurrence(s) au lieu de {count} : {old[:90]!r}'
    return tpl.replace(old, new)


SOURCES = [('', 'Tous les formulaires'), ('contact', 'Contact'), ('cours', 'Cours'), ('mariages', 'Mariages'),
           ('funerailles', 'Funérailles'), ('aide', 'Aide alimentaire'), ('femmes', 'Espace femmes')]
STATUSES = [('', 'Toutes'), ('nouveau', 'Nouvelles'), ('lu', 'Lues'), ('traite', 'Traitées')]

# =====================================================================================
# 1. Panneau SA-Contact : onglet « Demandes reçues »
# =====================================================================================

INBOX_HTML = (
    '<div id="sp-in" class="sp"><div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Boîte de réception</p>'
    '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Demandes reçues</h2>'
    '<p style="margin:6px 0 0;color:#4F5E57;max-width:620px">Les messages envoyés depuis les formulaires du site. '
    'Aucun courriel n’est envoyé : ils se lisent ici, et vous répondez depuis votre propre courriel.</p></div>'
    '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
    '<span class="tag" id="in-count" style="background:#F3EAD8;color:#7A5A1E">Chargement…</span>'
    '<button type="button" class="btn btn-line" id="in-refresh">Actualiser</button></div></div>'
    '<section class="card" aria-label="Liste des demandes reçues"><div class="card-b">'
    '<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end">'
    '<div class="fld" style="flex:1 1 150px;min-width:0"><label class="lbl" for="in-status">Statut</label><sc-raw-select class="in" id="in-status">'
    + ''.join(f'<option>{t}</option>' for _, t in STATUSES) + '</sc-raw-select></div>'
    '<div class="fld" style="flex:1 1 170px;min-width:0"><label class="lbl" for="in-source">Formulaire</label><sc-raw-select class="in" id="in-source">'
    + ''.join(f'<option>{t}</option>' for _, t in SOURCES) + '</sc-raw-select></div>'
    '<div class="fld" style="flex:2 1 220px;min-width:0"><label class="lbl" for="in-q">Rechercher</label>'
    '<input class="in" id="in-q" type="search" placeholder="Nom, courriel, mot du message" autocomplete="off" style="inline-size:100%;min-inline-size:0"></div>'
    '</div><div id="in-list" aria-live="polite"></div></div></section></div>'
)

INBOX_SCRIPT = r'''<script id="sa-inbox">
(function () {
  var STATUS = __STATUS__;
  var SOURCES = __SOURCES__;
  var TAG = {
    nouveau: ['Nouvelle', '#F3EAD8', '#7A5A1E'],
    lu: ['Lue', '#EEF1EF', '#3D4A44'],
    traite: ['Traitée', '#DCEFE6', '#0E4D3C']
  };
  var MAIL_RE = /^[^@\s<>"]+@[^@\s<>"]+\.[^@\s<>"]{2,}$/;
  var items = [], busy = false, started = false, qTimer = null, reqNo = 0;

  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function toast(m) { var c = window.__saContactToast; if (c) c(m); else window.alert(m); }
  function pick(id, list) {
    var e = el(id), t = e ? String(e.value).trim() : '';
    for (var i = 0; i < list.length; i++) if (list[i][1] === t) return list[i][0];
    return '';
  }
  function when(iso) {
    var d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : String(iso).replace(' ', 'T') + 'Z');
    if (isNaN(d)) return esc(iso);
    return esc(d.toLocaleString('fr-CA', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }));
  }
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function setCount(c) {
    var t = el('in-count');
    if (!t) return;
    t.textContent = !c ? '—' : c.nouveau ? c.nouveau + (c.nouveau > 1 ? ' nouvelles demandes' : ' nouvelle demande') : 'Aucune nouvelle demande';
    t.style.background = c && c.nouveau ? '#C49A4A' : '#F3EAD8';
    t.style.color = c && c.nouveau ? '#1E2B26' : '#7A5A1E';
  }
  function reply(x) {
    var c = String(x.contact || '').trim();
    if (MAIL_RE.test(c)) {
      return '<a class="btn btn-green" href="mailto:' + esc(c) + '?subject=' + encodeURIComponent('ASCIL : ' + (x.sujet || 'votre message')) + '">Répondre par courriel</a>';
    }
    var tel = c.replace(/[^\d+]/g, '');
    return tel ? '<a class="btn btn-green" href="tel:' + esc(tel) + '">Appeler</a>' : '';
  }
  function card(x) {
    var tg = TAG[x.status] || TAG.lu, isNew = x.status === 'nouveau';
    var det = x.details ? Object.keys(x.details).map(function (k) {
      return '<div style="display:flex;gap:8px;flex-wrap:wrap"><dt style="font-weight:600;color:#3D4A44">' + esc(k) + ' :</dt><dd style="margin:0;overflow-wrap:anywhere;white-space:pre-line">' + esc(x.details[k]) + '</dd></div>';
    }).join('') : '';
    var who = esc(x.nom);
    return '<li data-id="' + x.id + '" style="border:1px solid #E4D9C0;border-left:4px solid ' + (isNew ? '#C49A4A' : '#E4D9C0') + ';border-radius:14px;background:#fff;padding:14px 16px;display:flex;flex-direction:column;gap:10px">' +
      '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
      '<span class="tag" style="background:' + tg[1] + ';color:' + tg[2] + '">' + tg[0] + '</span>' +
      '<span class="tag" style="background:#F7F3EA;color:#3D4A44">' + esc(x.sourceLabel || x.source) + '</span>' +
      '<span style="margin-left:auto;font-size:13px;color:#4F5E57">' + when(x.created_at) + '</span></div>' +
      '<div><p style="margin:0;font-weight:700;color:#0E4D3C;font-size:16px;overflow-wrap:anywhere">' + who + '</p>' +
      '<p style="margin:2px 0 0;color:#3D4A44;overflow-wrap:anywhere">' + esc(x.contact) + '</p></div>' +
      (x.sujet ? '<p style="margin:0;font-weight:600;overflow-wrap:anywhere">Sujet : ' + esc(x.sujet) + '</p>' : '') +
      '<p style="margin:0;white-space:pre-line;overflow-wrap:anywhere;line-height:1.5">' + esc(x.message) + '</p>' +
      (det ? '<dl style="margin:0;display:flex;flex-direction:column;gap:4px;font-size:14px">' + det + '</dl>' : '') +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">' + reply(x) +
      '<button type="button" class="btn btn-line" data-in-act="' + (x.status === 'nouveau' ? 'lu' : 'nouveau') + '" data-id="' + x.id + '">' +
        (x.status === 'nouveau' ? 'Marquer comme lue' : 'Marquer comme nouvelle') + '</button>' +
      (x.status !== 'traite' ? '<button type="button" class="btn btn-line" data-in-act="traite" data-id="' + x.id + '">Marquer comme traitée</button>' : '') +
      '<button type="button" class="btn" data-in-act="del" data-id="' + x.id + '" style="background:#fff;border-color:#B3261E;color:#B3261E;margin-left:auto">Supprimer</button>' +
      '</div></li>';
  }
  function render(filtered) {
    var w = el('in-list');
    if (!w) return;
    if (!items.length) {
      w.innerHTML = '<div style="text-align:center;padding:36px 12px;color:#4F5E57">' +
        '<p style="margin:0;font-weight:700;color:#0E4D3C;font-size:17px">' + (filtered ? 'Aucune demande ne correspond à ces filtres.' : 'Aucune demande pour l’instant.') + '</p>' +
        '<p style="margin:6px auto 0;max-width:480px">' + (filtered ? 'Changez le statut, le formulaire ou la recherche.' :
          'Les messages envoyés depuis la page Contact, puis depuis les formulaires des services, arriveront ici.') + '</p></div>';
      return;
    }
    w.innerHTML = '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:12px">' + items.map(card).join('') + '</ul>' +
      '<p class="hint" style="margin:12px 0 0">' + items.length + (items.length > 1 ? ' demandes affichées' : ' demande affichée') + (items.length >= 500 ? ' (les 500 plus récentes)' : '') + '.</p>';
  }
  function load() {
    var st = pick('in-status', STATUS), so = pick('in-source', SOURCES), q = el('in-q') ? el('in-q').value.trim() : '';
    var qs = [];
    if (st) qs.push('status=' + st);
    if (so) qs.push('source=' + so);
    if (q) qs.push('q=' + encodeURIComponent(q));
    var my = ++reqNo, w = el('in-list');
    if (w && !items.length) w.innerHTML = '<p class="hint" style="margin:0">Chargement des demandes…</p>';
    api('/api/admin/forms' + (qs.length ? '?' + qs.join('&') : '')).then(function (d) {
      if (my !== reqNo) return;
      if (!d || !d.ok) {
        setCount(null);
        if (w) w.innerHTML = '<p class="hint" style="margin:0;color:#B3261E">' + esc((d && d.message) || 'Impossible de charger les demandes. Rechargez la page.') + '</p>';
        return;
      }
      items = d.messages || [];
      setCount(d.counts);
      render(!!(st || so || q));
    }, function () {
      if (w) w.innerHTML = '<p class="hint" style="margin:0;color:#B3261E">Impossible de joindre le serveur. Vérifiez votre connexion, puis cliquez sur Actualiser.</p>';
    });
  }
  function act(b) {
    if (busy) return;
    var id = parseInt(b.getAttribute('data-id'), 10), a = b.getAttribute('data-in-act');
    var x = items.filter(function (m) { return m.id === id; })[0];
    if (!x) return;
    var p;
    if (a === 'del') {
      if (!window.confirm('Supprimer définitivement la demande de ' + x.nom + ' ? Elle ne pourra pas être récupérée.')) return;
      p = api('/api/admin/forms?id=' + id, 'DELETE');
    } else {
      p = api('/api/admin/forms', 'PATCH', { id: id, status: a });
    }
    busy = true;
    b.setAttribute('aria-busy', 'true');
    p.then(function (d) {
      busy = false;
      b.removeAttribute('aria-busy');
      if (!d || !d.ok) { toast((d && d.message) || 'L’action a échoué. Réessayez dans un instant.'); return; }
      toast(a === 'del' ? 'Demande supprimée.' : a === 'traite' ? 'Demande marquée comme traitée.' : a === 'lu' ? 'Demande marquée comme lue.' : 'Demande marquée comme nouvelle.');
      load();
    }, function () {
      busy = false;
      b.removeAttribute('aria-busy');
      toast('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
    });
  }
  function start() {
    if (started || !el('in-list')) return;
    started = true;
    document.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-in-act]');
      if (b) { act(b); return; }
      if (e.target.closest && e.target.closest('#in-refresh')) load();
    });
    document.addEventListener('change', function (e) {
      var t = e.target;
      if (t && (t.id === 'in-status' || t.id === 'in-source')) load();
    });
    document.addEventListener('input', function (e) {
      if (!e.target || e.target.id !== 'in-q') return;
      clearTimeout(qTimer);
      qTimer = setTimeout(load, 300);
    });
    load();
  }
  if (el('in-list')) start();
  else {
    var mo = new MutationObserver(function () { if (el('in-list')) { mo.disconnect(); start(); } });
    mo.observe(document.documentElement, { childList: true, subtree: true });
  }
})();
</script>
'''

TOAST_HOOK = "  componentWillUnmount() { clearTimeout(this.tt); }"
TOAST_HOOK_NEW = ("  componentDidMount() { window.__saContactToast = (m) => this.flash(m); }\n"
                  "  componentWillUnmount() { clearTimeout(this.tt); if (window.__saContactToast) window.__saContactToast = null; }")


def wire_panel():
    path = ROOT / 'SA-Contact.dc.html'
    s, i, j, tpl = load(path)
    if 'id="sp-in"' not in tpl:
        tpl = rep(tpl, '<div class="side-sub"><a href="#sp-0">Page Contact</a>',
                  '<div class="side-sub"><a href="#sp-in">Demandes reçues</a><a href="#sp-0">Page Contact</a>')
        tpl = rep(tpl, 'aria-label="Pages de cette rubrique"><a href="#sp-0">Page Contact</a>',
                  'aria-label="Pages de cette rubrique"><a href="#sp-in">Demandes reçues</a><a href="#sp-0">Page Contact</a>')
        tpl = rep(tpl, '<div id="sp-0" class="sp">', INBOX_HTML + '<div id="sp-0" class="sp">')
        tpl = rep(tpl, 'L’adresse, la carte, l’étiquette de visite, le formulaire et la page 404.',
                  'Les demandes reçues, l’adresse, la carte, l’étiquette de visite, le formulaire et la page 404.')
    if '__saContactToast' not in tpl:
        tpl = rep(tpl, TOAST_HOOK, TOAST_HOOK_NEW)
    sync = (INBOX_SCRIPT.replace('__STATUS__', json.dumps([list(x) for x in STATUSES], ensure_ascii=False))
            .replace('__SOURCES__', json.dumps([list(x) for x in SOURCES], ensure_ascii=False)))
    tpl = re.sub(r'<script id="sa-inbox">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + sync + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Contact.dc.html : onglet Demandes reçues ajouté')


# =====================================================================================
# 2. Page publique Contact : envoi vers la boîte de réception
# =====================================================================================

SEND_NEW = (
    "send: () => { if (this.state.sending) return; const v = this.v, errs = {}; "
    "if (!(v.name || '').trim()) errs.name = 1; if (!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(v.mail || '')) errs.mail = 1; "
    "if (!(v.msg || '').trim()) errs.msg = 1; this.setState({ errs, sendErr: '' }); if (Object.keys(errs).length) return; "
    "const g = (id) => { const e = document.getElementById(id); return e ? String(e.value) : ''; }; "
    "this.setState({ sending: true }); "
    "fetch('/api/forms', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, "
    "body: JSON.stringify({ source: 'contact', nom: v.name, contact: v.mail, sujet: g('f-suj'), message: g('f-msg') || v.msg, hp: g('f-site'), t: Date.now() - (this.t0 || 0) }) })"
    ".then((r) => r.json().catch(() => ({ ok: false })))"
    ".then((d) => { if (d && d.ok) this.setState({ sending: false, sent: true }); "
    "else this.setState({ sending: false, sendErr: (d && d.message) || 'Votre message n’a pas pu être envoyé. Réessayez dans un instant.' }); }, "
    "() => this.setState({ sending: false, sendErr: 'Impossible de joindre le site. Vérifiez votre connexion et réessayez.' })); },\n"
    "      sendLbl: this.state.sending ? 'Envoi en cours…' : 'Envoyer le message', sendBusy: String(!!this.state.sending), "
    "sendErr: this.state.sendErr || '', hasSendErr: !!this.state.sendErr,"
)

HONEYPOT = ('<div aria-hidden="true" style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden">'
            '<label for="f-site">Site web (laisser vide)</label><input id="f-site" type="text" tabindex="-1" autocomplete="off"></div>')


def patch_contact(tpl):
    if '/api/forms' in tpl:
        return tpl
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    code, n = re.subn(r"send: \(\) => \{ const v = this\.v, errs = \{\};.*?sent: Object\.keys\(errs\)\.length === 0 \}\); \},",
                      lambda _: SEND_NEW, code, count=1, flags=re.S)
    assert n == 1, 'fonction send introuvable'
    code = rep(code, 'this.v = {}; }', 'this.v = {}; this.t0 = Date.now(); }')
    tpl = tpl[:la] + code + tpl[lb:]

    tpl = rep(tpl, '<form style="display:flex;flex-direction:column;gap:18px" aria-label="Formulaire de contact">',
              '<form style="display:flex;flex-direction:column;gap:18px;position:relative" aria-label="Formulaire de contact">')
    tpl = rep(tpl, 'class="btn btn-green" sc-camel-on-click="{{send}}">',
              'class="btn btn-green" sc-camel-on-click="{{send}}" aria-busy="{{sendBusy}}">')
    tpl = rep(tpl, 'Préparer le courriel</button>', '{{sendLbl}}</button>')
    a = tpl.index('aria-busy="{{sendBusy}}">')
    b = tpl.rindex('<button type="button" class="btn btn-green"', 0, a)
    err = ('<sc-if value="{{hasSendErr}}" hint-placeholder-val="{{ false }}"><p class="err" role="alert" style="margin:0">{{sendErr}}</p></sc-if>')
    tpl = tpl[:b] + HONEYPOT + err + tpl[b:]
    tpl = rep(tpl, 'Votre logiciel de courriel s’ouvre avec le message prérempli. Aucune donnée n’est conservée sur ce site.',
              'Votre message arrive directement à l’association, qui vous répond à l’adresse indiquée. Seuls ses responsables le lisent.')
    tpl = rep(tpl, '>Votre courriel est prêt</p>', '>Message envoyé</p>')
    tpl = rep(tpl, 'Il ne reste qu’à l’envoyer depuis votre logiciel de courriel.', 'Merci. L’association vous répondra à l’adresse indiquée.')
    return tpl


def wire_public():
    for prefix in ('', 'M-', 'T-'):
        path = ROOT / f'{prefix}Contact.dc.html'
        s, i, j, tpl = load(path)
        save(path, s, i, j, patch_contact(tpl))
    print('3 pages publiques Contact (PC, M-, T-) : formulaire relié à la boîte de réception')


if __name__ == '__main__':
    wire_panel()
    wire_public()

"""Branche les heures de prière du site public sur la base (étape H4).

Source unique : le tableau du mois (table prayer_times, API publique GET /api/prayer-times),
avec repli sur les heures de la carte « Prochaine prière » de l'Accueil quand une case est vide.

Pages Horaires.dc.html, M-Horaires.dc.html, T-Horaires.dc.html :
1. Logique de la page : les heures du jour (barre du haut « Prochaine prière », tableau
   « Aujourd'hui », compte à rebours, menu mobile, pied de page) viennent de la base.
   Le script #ascil-prayer-live charge les données, les range dans window.__ascilPrayer et
   prévient la page (événement « ascil:prayer »), qui se redessine.
2. Tableau « Mois complet » : mois courant (fuseau America/Toronto) lu dans la base,
   « AUJOURD'HUI » sur le vrai jour, vendredis mis en évidence avec l'heure de Jumu'a,
   colonnes Suhoor / Iftar pendant le Ramadan (si activées). Bouton PDF retiré.
3. Réglages « horaires » (Superadmin → Horaires) : bloc Aujourd'hui (affichage, compte à
   rebours, date hégirienne, liens Rappel et Khutba), filtre Vendredis, carte du vendredi
   (affichage, heure du prochain vendredi, minutes d'avance, conseil de stationnement),
   Ramadan (dates du « Mode du site », Suhoor, Iftar, Tarawih), Aïd (dates, heures, lieu,
   itinéraire), Qibla (degrés, repère).

Idempotent : la logique et le balisage ne sont modifiés qu'une fois (repère ascil-prayer),
le script #ascil-prayer-live est remplacé à chaque passage.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'
MARK = '/*ascil-prayer*/'
PAGES = ['Horaires.dc.html', 'M-Horaires.dc.html', 'T-Horaires.dc.html']


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
    assert n == count, f'{n} occurrence(s) au lieu de {count} : {old[:80]!r}'
    return tpl.replace(old, new)


def resub(tpl, pattern, repl, flags=re.S):
    out, n = re.subn(pattern, repl, tpl, count=1, flags=flags)
    assert n == 1, f'motif introuvable : {pattern[:80]!r}'
    return out


# ---------------------------------------------------------------------------
# 1. Logique de la page (classe Component)
# ---------------------------------------------------------------------------

HOR_VALS = r'''  /*ascil-prayer*/
  horVals(PT, k) {
    const HS = PT.horaires || {};
    const g = (sec, key, d) => (HS[sec] && HS[sec][key] !== undefined && HS[sec][key] !== null ? HS[sec][key] : d);
    const today = PT.date || '';
    const days = Array.isArray(PT.days) ? PT.days : [];
    const defs = PT.defaults || {};
    const fmtDay = (iso) => { try { return new Intl.DateTimeFormat('fr-CA', { timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(iso + 'T12:00:00Z')); } catch (e) { return iso; } };
    let friTime = k.tJ;
    if (!k.isFri && today) {
      const f = days.find((d) => d.date > today && new Date(d.date + 'T12:00:00Z').getUTCDay() === 5);
      if (f) friTime = f.jumuha || defs.jumuha || k.tJ;
    }
    const avance = Number(g('vendredi', 'avance', 15)) || 0;
    const conseil = g('vendredi', 'conseil', true) !== false;
    let friNote = 'Khutba suivie de la prière.';
    if (avance > 0) friNote += ' Conseil : arrivez ' + avance + ' minutes à l\u2019avance' + (conseil ? ', le stationnement étant limité dans la rue.' : '.');
    else if (conseil) friNote += ' Le stationnement est limité dans la rue.';
    const S = PT.season || {};
    const hasRam = S.mode === 'ramadan' && !!S.from && !!S.to;
    const inRam = hasRam && !!today && today >= S.from && today <= S.to;
    let ramIntro = 'Les horaires du Ramadan seront publiés ici dès l\u2019annonce officielle.';
    if (hasRam) ramIntro = today && today > S.to ? 'Le Ramadan s\u2019est terminé le ' + fmtDay(S.to) + '.' : 'Du ' + fmtDay(S.from) + ' au ' + fmtDay(S.to) + '.';
    const rp = [];
    if (inRam && g('ramadan', 'suhoor', true)) rp.push('Suhoor jusqu\u2019à ' + k.tF);
    if (inRam && g('ramadan', 'iftar', true) && k.tM) rp.push('Iftar à ' + k.tM);
    const ramToday = rp.length ? 'Aujourd\u2019hui : ' + rp.join(' · ') + '.' : '';
    const tarH = g('ramadan', 'tarawih', false) ? g('ramadan', 'tarawihHeure', '') : '';
    const ramTar = hasRam && !(today && today > S.to) && tarH ? 'Tarawih chaque soir à ' + tarH + '.' : '';
    const aidL = [];
    [['fitrDate', 'fitrHeure', 'Aïd al-Fitr'], ['adhaDate', 'adhaHeure', 'Aïd al-Adha']].forEach((a) => {
      const dd = g('aid', a[0], ''), hh = g('aid', a[1], '');
      if (dd && (!today || dd >= today)) aidL.push(a[2] + ' : ' + fmtDay(dd) + (hh ? ' à ' + hh : '') + '.');
    });
    const aidHref = String(g('aid', 'itineraire', 'https://maps.google.com/?q=15+rue+Frontenac+Riviere-du-Loup') || '');
    const qDeg = String(g('qibla', 'degres', '61,6') || '61,6');
    const qNum = parseFloat(qDeg.replace(',', '.'));
    const qRepere = String(g('qibla', 'repere', '') || '');
    const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
    const ym = PT.month || today.slice(0, 7);
    const mName = ym ? MOIS[parseInt(ym.slice(5, 7), 10) - 1] + ' ' + ym.slice(0, 4) : '';
    const showRam = g('ramadan', 'on', true) !== false, showAid = g('aid', 'on', true) !== false, showQibla = g('qibla', 'on', true) !== false;
    const showRappel = g('aujourdhui', 'lienRappel', true) !== false, showKhutba = g('aujourdhui', 'lienKhutba', true) !== false;
    return {
      showAuj: g('aujourdhui', 'on', true) !== false, showCompte: g('aujourdhui', 'compte', true) !== false,
      showHijri: g('aujourdhui', 'hijri', true) !== false, showRappel, showKhutba, showLinks: showRappel || showKhutba,
      showFri: g('vendredi', 'on', true) !== false, friTime, friNote,
      showFriFilter: g('mois', 'vendredis', true) !== false,
      monthTitle: mName ? mName.charAt(0).toUpperCase() + mName.slice(1) : 'Mois complet',
      showRam, ramIntro, ramToday, hasRamToday: !!ramToday, ramTar, hasRamTar: !!ramTar,
      showAid, aidDates: aidL.length ? aidL.join(' ') : 'Date selon l\u2019annonce TCOM.',
      aidLieu: String(g('aid', 'lieu', 'Salle louée — 15 rue Frontenac') || 'Lieu à confirmer'), aidHref, hasAidHref: !!aidHref,
      showQibla, qDeg, qRot: Number.isFinite(qNum) ? qNum : 61.6, qRepere, hasQRepere: !!qRepere,
      showSand: showRam || showAid || showQibla,
    };
  }

  renderVals() {'''

LOGIC = [
    ('componentDidMount() { ',
     "componentDidMount() { this.onPrayer = () => this.setState({ now: Date.now() }); "
     "try { window.addEventListener('ascil:prayer', this.onPrayer); } catch (e) {} "),
    ('componentWillUnmount() { ',
     "componentWillUnmount() { try { window.removeEventListener('ascil:prayer', this.onPrayer); } catch (e) {} "),
    ('\n  renderVals() {', '\n' + HOR_VALS),
    (r"""    const known = [{ n: 'Fajr', t: 390 }].concat(isFri ? [{ n: 'Jumu\u2019a', t: 750 }] : []).concat([{ n: 'Icha', t: 1140 }]);
    let next = known.find((x) => x.t > mins); let tomorrow = false;
    if (!next) { next = { n: 'Fajr', t: 390 }; tomorrow = true; }""",
     r"""    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const PD = PT.today || {};
    const pt = (k, d) => (typeof PD[k] === 'string' && /^\d\d:\d\d$/.test(PD[k]) ? PD[k] : d);
    const toM = (s) => parseInt(s.slice(0, 2), 10) * 60 + parseInt(s.slice(3), 10);
    const tF = pt('fajr', '06:30'), tL = pt('lever', ''), tD = pt('dohr', ''), tA = pt('asr', ''), tM = pt('maghreb', ''), tI = pt('isha', '19:00'), tJ = pt('jumuha', '12:30');
    const known = [['Fajr', tF], isFri ? ['Jumu\u2019a', tJ] : ['Dohr', tD], ['Asr', tA], ['Maghreb', tM], ['Icha', tI]].filter((x) => x[1]).map((x) => ({ n: x[0], t: toM(x[1]) })).sort((a, b) => a.t - b.t);
    let next = known.find((x) => x.t > mins); let tomorrow = false;
    if (!next) { next = known[0]; tomorrow = true; }"""),
    (r"""      mk('Fajr', 'Fajr', 'الفجر', '06:30'),
      mk('Lever', 'Lever du soleil', 'الشروق', ''),
      isFri ? mk('Jumu\u2019a', 'Jumu\u2019a', 'الجمعة', '12:30') : mk('Dohr', 'Dohr', 'الظهر', ''),
      mk('Asr', 'Asr', 'العصر', ''),
      mk('Maghreb', 'Maghreb', 'المغرب', ''),
      mk('Icha', 'Icha', 'العشاء', '19:00'),""",
     r"""      mk('Fajr', 'Fajr', 'الفجر', tF),
      mk('Lever', 'Lever du soleil', 'الشروق', tL),
      isFri ? mk('Jumu\u2019a', 'Jumu\u2019a', 'الجمعة', tJ) : mk('Dohr', 'Dohr', 'الظهر', tD),
      mk('Asr', 'Asr', 'العصر', tA),
      mk('Maghreb', 'Maghreb', 'المغرب', tM),
      mk('Icha', 'Icha', 'العشاء', tI),"""),
    ("const prevK = known.filter((x) => x.t <= mins).pop() || { n: 'Icha', t: 1140 - 1440 };",
     "const prevK = known.filter((x) => x.t <= mins).pop() || { n: known[known.length - 1].n, t: known[known.length - 1].t - 1440 };"),
    ("dohrTime: '12:30',",
     "dohrTime: tJ, fajrTime: tF, jumuaTime: tJ, ichaTime: tI, ...this.horVals(PT, { tF, tM, tJ, isFri }),"),
]


def patch_logic(tpl):
    a = tpl.index('<script type="text/x-dc"')
    b = tpl.index('</script>', a)
    code = tpl[a:b]
    if MARK in code:
        return tpl
    for old, new in LOGIC:
        code = rep(code, old, new)
    return tpl[:a] + code + tpl[b:]


# ---------------------------------------------------------------------------
# 2. Balisage de la page Horaires
# ---------------------------------------------------------------------------

def sc_if(name, inner, default='true'):
    return f'<sc-if value="{{{{{name}}}}}" hint-placeholder-val="{{{{ {default} }}}}">{inner}</sc-if>'


MONTH_PLACEHOLDER = ('<div id="ascil-month"><p class="muted" style="margin:0;padding:18px 16px">'
                     'Chargement des horaires du mois…</p></div>')


def patch_markup(tpl):
    if 'id="ascil-month"' in tpl:
        return tpl

    # Menu mobile et pied de page : heures du jour.
    tpl = rep(tpl, '<div style="font-size:13px">Fajr</div><div style="font-size:22px;font-weight:700;color:#fff">06:30</div>',
              '<div style="font-size:13px">Fajr</div><div style="font-size:22px;font-weight:700;color:#fff">{{fajrTime}}</div>')
    tpl = rep(tpl, '<div style="font-size:13px">Icha</div><div style="font-size:22px;font-weight:700;color:#fff">19:00</div>',
              '<div style="font-size:13px">Icha</div><div style="font-size:22px;font-weight:700;color:#fff">{{ichaTime}}</div>')
    tpl = rep(tpl, 'Fajr 06:30 — Jumu’a 12:30 — Icha 19:00', 'Fajr {{fajrTime}} — Jumu’a {{jumuaTime}} — Icha {{ichaTime}}')

    # Bloc « Aujourd'hui » : date hégirienne, compte à rebours, liens, affichage du bloc.
    h = '<p class="muted" style="margin:4px 0 0">{{hijri}}</p>'
    tpl = rep(tpl, h, sc_if('showHijri', h))
    tpl = resub(tpl, r'(<p class="tnum" style="margin:0;display:inline-flex[^"]*">(?:(?!</p>).)*?\{\{nextName\}\} \{\{countdown\}\}</p>)',
                lambda m: sc_if('showCompte', m.group(1)))
    tpl = resub(tpl, r'(<a class="btn btn-ghost" href="(?:[MT]-)?N3-Rappel\.dc\.html"(?:(?!</a>).)*</a>)', lambda m: sc_if('showRappel', m.group(1)))
    tpl = resub(tpl, r'(<a class="btn btn-ghost" href="(?:[MT]-)?N2-Khutba\.dc\.html"(?:(?!</a>).)*</a>)', lambda m: sc_if('showKhutba', m.group(1)))
    tpl = resub(tpl, r'(<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px"><sc-if value="\{\{showRappel\}\}".*?</sc-if></div>)',
                lambda m: sc_if('showLinks', m.group(1)))
    a = tpl.index('<div class="split" style="align-items:start">') + len('<div class="split" style="align-items:start">')
    b = tpl.index('\n   <div style="display:flex;flex-direction:column;gap:20px">', a)
    left = tpl[a:b]
    assert left.lstrip().startswith('<div>') and left.rstrip().endswith('</div>'), 'colonne Aujourd’hui inattendue'
    tpl = tpl[:a] + sc_if('showAuj', left) + tpl[b:]

    # Carte du vendredi : heure du prochain vendredi, conseil, affichage.
    fri_time = '<p class="tnum" style="margin:8px 0 0;font-size:56px;font-weight:700;color:#C49A4A;line-height:1">12:30</p>'
    tpl = rep(tpl, fri_time, fri_time.replace('>12:30<', '>{{friTime}}<'))
    tpl = resub(tpl, r'<p style="margin:12px 0 0;color:#F3EAD8">Khutba suivie[^<]*</p>',
                lambda m: '<p style="margin:12px 0 0;color:#F3EAD8">{{friNote}}</p>')
    tpl = resub(tpl, r'(<div style="background:#0E4D3C;color:#fff;border-radius:22px;padding:30px">.*?\{\{friNote\}\}</p>\s*</div>)',
                lambda m: sc_if('showFri', m.group(1)))

    # Mois complet : titre, filtre Vendredis, PDF retiré, tableau rendu depuis la base.
    tpl = rep(tpl, '<h2 id="mois-t" class="h2" style="margin-top:8px">Novembre 2026</h2>',
              '<h2 id="mois-t" class="h2" style="margin-top:8px">{{monthTitle}}</h2>')
    tpl = resub(tpl, r'(<div class="seg" role="group" aria-label="Affichage">.*?</div>)', lambda m: sc_if('showFriFilter', m.group(1)))
    tpl = resub(tpl, r'<a class="btn btn-ghost" href="#">(?:(?!</a>).)*Télécharger le mois en PDF</a>', lambda m: '')
    a = tpl.index('aria-labelledby="mois-t"')
    tpl = tpl[:a] + resub(tpl[a:], r'<sc-raw-table class="t tnum" style="min-width:680px">.*?</sc-raw-table>',
                          lambda m: MONTH_PLACEHOLDER)

    # Ramadan, Aïd, Qibla.
    tpl = resub(tpl, r'(<div class="card">\s*<span style="color:#0E4D3C">(?:(?!</span>).)*</span>\s*<p class="h3" style="margin-top:14px">Ramadan</p>)\s*'
                     r'<p class="muted" style="margin:8px 0 0">Les horaires du Ramadan[^<]*</p>\s*</div>',
                lambda m: sc_if('showRam', m.group(1)
                                + '<p class="muted" style="margin:8px 0 0">{{ramIntro}}</p>'
                                + sc_if('hasRamToday', '<p style="margin:8px 0 0;font-weight:600;color:#0E4D3C">{{ramToday}}</p>', 'false')
                                + sc_if('hasRamTar', '<p style="margin:6px 0 0">{{ramTar}}</p>', 'false')
                                + '</div>'))
    tpl = resub(tpl, r'(<div class="card">\s*<span style="color:#0E4D3C">(?:(?!</span>).)*</span>\s*<p class="h3" style="margin-top:14px">Prières de l’Aïd</p>)\s*'
                     r'<p class="muted" style="margin:8px 0 0">Date selon l’annonce TCOM\. Lieu :</p>\s*'
                     r'<p style="margin:6px 0 0;font-size:20px;font-weight:700;color:#0E4D3C">15 rue Frontenac</p>\s*'
                     r'<p class="muted" style="margin:2px 0 0;font-size:15px">[^<]*</p>\s*'
                     r'<a class="btn btn-ghost" href="https://maps\.google\.com/\?q=15\+rue\+Frontenac\+Riviere-du-Loup"( style="margin-top:16px">(?:(?!</a>).)*</a>)\s*</div>',
                lambda m: sc_if('showAid', m.group(1)
                                + '<p class="muted" style="margin:8px 0 0">{{aidDates}} Lieu :</p>'
                                + '<p style="margin:6px 0 0;font-size:20px;font-weight:700;color:#0E4D3C;overflow-wrap:anywhere">{{aidLieu}}</p>'
                                + sc_if('hasAidHref', '<a class="btn btn-ghost" href="{{aidHref}}"' + m.group(2), 'true')
                                + '</div>'))
    tpl = resub(tpl, r'(<div class="card" style="display:flex;flex-direction:column">\s*<p class="h3">Qibla</p>.*?</svg>\s*<p style="margin:0">.*?</p>\s*</div>\s*</div>)',
                lambda m: sc_if('showQibla', m.group(1)))
    tpl = rep(tpl, 'aria-label="Boussole : la Qibla à 61,6 degrés du nord vrai"', 'aria-label="Boussole : la Qibla à {{qDeg}} degrés du nord vrai"')
    tpl = rep(tpl, '<g class="needle">', '<g transform="rotate({{qRot}} 60 60)"><g class="needle">')
    tpl = resub(tpl, r'(<g transform="rotate\(\{\{qRot\}\} 60 60\)"><g class="needle">.*?</g>)', lambda m: m.group(1) + '</g>')
    tpl = rep(tpl, '<strong>61,6°</strong> depuis le nord vrai ; la Kaaba est à <strong>9 619 km</strong>.</p>',
              '<strong>{{qDeg}}°</strong> depuis le nord vrai ; la Kaaba est à <strong>9 619 km</strong>.</p>'
              + sc_if('hasQRepere', '<p class="muted" style="margin:0;font-size:15px">Sur place : {{qRepere}}</p>', 'false'))
    # Aiguille : l'animation part de -90° et s'arrête sur 0°, le groupe parent porte l'angle réel.
    tpl = rep(tpl, '@keyframes needle{from{transform:rotate(-30deg)}to{transform:rotate(61.6deg)}}',
              '@keyframes needle{from{transform:rotate(-90deg)}to{transform:rotate(0deg)}}')
    tpl = rep(tpl, '.needle{transform:rotate(61.6deg) !important}', '.needle{transform:rotate(0deg) !important}')
    tpl = resub(tpl, r'(<section class="sand" style="border-top:1px solid #E4D9C0">\s*<div class="wrap sec g3">.*?</section>)',
                lambda m: sc_if('showSand', m.group(1)))
    return tpl


# ---------------------------------------------------------------------------
# 3. Chargement des données et tableau du mois
# ---------------------------------------------------------------------------

LIVE_SCRIPT = r'''<script id="ascil-prayer-live">
(function () {
  var P = window.__ascilPrayer = window.__ascilPrayer || {};
  var isHoraires = /(^|\/)(M-|T-)?Horaires\.dc(\.html)?$/.test(location.pathname);
  function getJ(u) {
    return fetch(u, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  var DAYS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
  var MONTHS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juill.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  var MONTHS_LONG = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  function cell(v, muted) {
    return v ? '<td>' + esc(v) + '</td>' : '<td class="muted">—</td>';
  }
  function monthHtml() {
    if (P.failed || !P.days || !P.days.length) {
      return '<p class="muted" style="margin:0;padding:18px 16px">Les horaires du mois sont momentanément indisponibles. ' +
        'Réessayez dans quelques minutes, ou consultez l’affiche à la mosquée.</p>';
    }
    var D = P.defaults || {}, H = P.horaires || {}, S = P.season || {}, R = H.ramadan || {};
    var hasRam = R.on !== false && S.mode === 'ramadan' && S.from && S.to;
    var first = P.days[0].date, last = P.days[P.days.length - 1].date;
    var ramCols = hasRam && S.from <= last && S.to >= first;
    var suhoor = ramCols && R.suhoor !== false, iftar = ramCols && R.iftar !== false;
    var ym = P.month || first.slice(0, 7);
    var title = MONTHS_LONG[parseInt(ym.slice(5, 7), 10) - 1] + ' ' + ym.slice(0, 4);
    var h = ['<table class="t tnum" style="min-width:680px"><caption style="position:absolute;left:-9999px">Horaires de ' + esc(title) + '</caption>',
      '<thead style="position:sticky;top:0"><tr><th scope="col">Jour</th><th scope="col">Fajr</th><th scope="col">Lever</th>',
      '<th scope="col">Dohr</th><th scope="col">Asr</th><th scope="col">Maghreb</th><th scope="col">Icha</th>',
      suhoor ? '<th scope="col">Suhoor (fin)</th>' : '', iftar ? '<th scope="col">Iftar</th>' : '', '</tr></thead><tbody>'];
    P.days.forEach(function (d) {
      var dt = new Date(d.date + 'T12:00:00Z'), wd = dt.getUTCDay();
      var isFri = wd === 5, isToday = d.date === P.date;
      var label = DAYS[wd] + ' ' + dt.getUTCDate() + ' ' + MONTHS[dt.getUTCMonth()];
      var fajr = d.fajr || D.fajr || '', isha = d.isha || D.isha || D.icha || '', maghreb = d.maghreb || D.maghreb || '';
      var bg = isToday ? '#F6E7C4' : (isFri ? '#F7F2E4' : '#fff');
      var row = '<tr class="' + (isFri ? '' : 'nf') + '" style="background:' + bg + '"' + (isToday ? ' aria-current="date"' : '') + '>';
      row += '<td style="white-space:nowrap;font-weight:' + (isFri || isToday ? 700 : 400) + '">' + esc(label) +
        (isToday ? ' <span class="pill" style="background:#C49A4A;color:#1E2B26;padding:2px 8px;font-size:11px">AUJOURD’HUI</span>' : '') + '</td>';
      row += cell(fajr) + cell(d.lever || D.lever);
      if (isFri) {
        var j = d.jumuha || D.jumuha || D.jumua || '';
        row += j ? '<td><strong>' + esc(j) + '</strong> <span style="font-size:12px;font-weight:700;color:#7A5A1E">JUMU’A</span></td>' : cell(d.dohr || D.dohr);
      } else {
        row += cell(d.dohr || D.dohr);
      }
      row += cell(d.asr || D.asr) + cell(maghreb) + cell(isha);
      var inRam = ramCols && d.date >= S.from && d.date <= S.to;
      if (suhoor) row += inRam ? cell(fajr) : '<td class="muted">—</td>';
      if (iftar) row += inRam ? cell(maghreb) : '<td class="muted">—</td>';
      h.push(row + '</tr>');
    });
    h.push('</tbody></table>');
    return h.join('');
  }
  var html = null;
  function renderMonth() {
    if (!isHoraires || html === null) return;
    var el = document.getElementById('ascil-month');
    if (!el || el.getAttribute('data-done') === '1') return;
    el.innerHTML = html;
    el.setAttribute('data-done', '1');
  }
  Promise.all([
    getJ('/api/prayer-times'),
    isHoraires ? getJ('/api/settings/horaires') : null,
    isHoraires ? getJ('/api/settings/season') : null
  ]).then(function (r) {
    var pt = r[0];
    if (pt && pt.ok) {
      P.today = pt.today || pt.day;
      P.date = (P.today && P.today.date) || pt.date;
      P.month = pt.month;
      P.days = pt.days || [];
      P.defaults = pt.defaults || {};
    } else {
      P.failed = true;
    }
    if (r[1] && r[1].ok) P.horaires = r[1].settings;
    if (r[2] && r[2].ok) P.season = r[2].settings;
    try { window.dispatchEvent(new Event('ascil:prayer')); } catch (e) {}
    if (isHoraires) {
      html = monthHtml();
      renderMonth();
      new MutationObserver(renderMonth).observe(document.documentElement, { childList: true, subtree: true });
    }
  });
})();
</script>
'''


def wire(name):
    path = ROOT / name
    s, i, j, tpl = load(path)
    tpl = patch_logic(tpl)
    tpl = patch_markup(tpl)
    tpl = re.sub(r'<script id="ascil-prayer-live">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + LIVE_SCRIPT + tpl[k:]
    save(path, s, i, j, tpl)
    print(name, ': heures de prière reliées à la base')


if __name__ == '__main__':
    for p in PAGES:
        wire(p)

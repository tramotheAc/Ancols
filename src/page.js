/* ===========================================================================
   Diagnostic des trames ANCOLS - logique de la page.

   Les donnees arrivent dans <script id="donnees" type="application/json">,
   injectees par scripts/04_assembler.py depuis donnees/analyse.json. Rien
   n'est stocke : la page se recalcule a chaque ouverture.
   =========================================================================== */
(function () {
'use strict';
const D = JSON.parse(document.getElementById('donnees').textContent);
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const FILES = D.files, FD = Object.fromEntries(FILES.map(f => [f.code, f]));
const PIV = D.pivots, PD = Object.fromEntries(PIV.map(p => [p.id, p]));
const FAMS = D.families, FAMIDX = Object.fromEntries(FAMS.map((f, i) => [f[0], i]));
// Huit familles, huit series de la charte choisies pour rester distinctes cote a cote.
const FAMSERIE = { ID: 6, LOC: 8, CAR: 1, ENE: 10, OCC: 2, LOY: 9, TRV: 4, DEV: 5 };
const fam = id => `--fam: var(--serie-${FAMSERIE[id]})`;
const famLabel = id => (FAMS.find(f => f[0] === id) || [, ''])[1];
const KIND = { R: 'Recueil', Q: 'Questionnaire', A: 'Tableau agrégé' };
const DOM = { GP: 'Patrimoine', GL: 'Gestion locative' };
const EFF = { S: 1, M: 2, L: 3, XL: 4 };
const EFFLAB = { S: 'Faible', M: 'Moyenne', L: 'Forte', XL: 'Très forte' };
const CRIT = { 1: ['Bloquant', 'rouge'], 2: ['Majeur', 'ambre'], 3: ['Utile', ''] };
const NIV = { 1: ['Critique', 'rouge'], 2: ['Important', 'ambre'], 3: ['À surveiller', ''] };
const THEMES = Object.fromEntries(D.themes.map(t => [t.id, t]));
const VAGUES = [
  ['Vague 0', 'Socle référentiel', 'Tables groupe / bâtiment / lot / RPLS, nombre de logements réconcilié.'],
  ['Vague 1', 'Extractions ERP locatives', 'Gros volumes à lancer tôt : CALEOL, quittancement, charges, SLS, réclamations.'],
  ['Vague 2', 'Patrimoine technique, développement, ventes', 'Données multi-services, nombreuses saisies hors SI.'],
  ['Vague 3', 'Consolidations et agrégats', 'Comptages qui s\'appuient sur les vagues précédentes.'],
  ['Vague 4', 'Questionnaires', 'Rédigés une fois les chiffres stabilisés.'],
];
const ordreTrames = [...FILES.filter(f => f.dom === 'GP'), ...FILES.filter(f => f.dom === 'GL')];
const voisins = c => { const out = []; for (const k in D.prox) { const [a, b] = k.split('|'); if (a === c) out.push([b, D.prox[k]]); else if (b === c) out.push([a, D.prox[k]]); } return out.sort((x, y) => y[1].length - x[1].length); };
const tramesDe = p => [...Object.keys(p.files), ...p.qfiles];
const passerelle = p => { const fs = tramesDe(p); return fs.some(c => FD[c].dom === 'GP') && fs.some(c => FD[c].dom === 'GL'); };
const charge = e => `<span class="charge" title="Charge ${EFFLAB[e].toLowerCase()}">${[1, 2, 3, 4].map(i => `<i class="${i <= EFF[e] ? 'on' : ''}" style="height:${4 + i * 3}px"></i>`).join('')}</span>`;
const codeTrame = c => `<button type="button" class="code-trame" data-trame="${c}" title="${esc(FD[c].title)}">${c}</button>`;
const jetonPivot = id => `<span class="jeton"><i class="puce" style="${fam(PD[id].fam)}"></i>${esc(PD[id].label)}</span>`;
const jetonCrit = n => `<span class="jeton ${CRIT[n][1]}">${CRIT[n][0]}</span>`;

/* ---------------------------------------------------- infobulle, toast, copie */
const bulle = $('#infobulle');
function placer(ev) { const r = bulle.getBoundingClientRect(); bulle.style.left = Math.min(ev.clientX + 14, innerWidth - r.width - 8) + 'px'; bulle.style.top = Math.min(ev.clientY + 14, innerHeight - r.height - 8) + 'px'; }
document.addEventListener('pointerover', e => { const t = e.target.closest('[data-bulle]'); if (t) { bulle.innerHTML = t.dataset.bulle; bulle.classList.add('on'); placer(e); } });
document.addEventListener('pointermove', e => { if (e.target.closest('[data-bulle]')) placer(e); });
document.addEventListener('pointerout', e => { const t = e.target.closest('[data-bulle]'); if (t && !t.contains(e.relatedTarget)) bulle.classList.remove('on'); });
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('on'); setTimeout(() => t.classList.remove('on'), 1800); }
function copier(texte, secours) {
  const repli = () => { secours.innerHTML = ''; const ta = document.createElement('textarea'); ta.className = 'secours'; ta.setAttribute('aria-label', 'CSV à copier'); ta.value = texte; secours.appendChild(ta); ta.focus(); ta.select(); toast('Texte sélectionné : Ctrl+C pour copier'); };
  try { navigator.clipboard.writeText(texte).then(() => toast('Copié dans le presse-papiers'), repli); } catch (e) { repli(); }
}
const csv = lignes => lignes.map(l => l.map(v => { v = String(v ?? ''); return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(';')).join('\n');

/* --------------------------------------------------------------- navigation */
const vues = [...document.querySelectorAll('.vue')];
const rail = $('#rail');
function aller(id, garderDefilement) {
  if (!document.getElementById('vue-' + id)) id = 'synthese';
  const v = document.getElementById('vue-' + id);
  vues.forEach(x => x.classList.toggle('actif', x === v));
  document.querySelectorAll('.nav button[data-vue]').forEach(b => b.setAttribute('aria-current', b.dataset.vue === id));
  $('#entete-surtitre').textContent = v.dataset.surtitre || '';
  $('#entete-titre').textContent = v.dataset.titre || '';
  $('#entete-texte').textContent = v.dataset.texte || '';
  rail.classList.remove('ouvert'); $('#bascule-nav').setAttribute('aria-expanded', 'false');
  try { history.replaceState(null, '', '#' + id); } catch (e) { }
  if (!garderDefilement) window.scrollTo({ top: 0 });
  if (id === 'cartographie') dessinerCarto();
}
document.querySelectorAll('.nav button[data-vue]').forEach(b => b.addEventListener('click', () => aller(b.dataset.vue)));
$('#bascule-nav').addEventListener('click', () => { const o = rail.classList.toggle('ouvert'); $('#bascule-nav').setAttribute('aria-expanded', o); });
document.addEventListener('click', e => {
  const t = e.target.closest('[data-trame]'); if (t) { e.preventDefault(); fermerTiroir(); afficherFiche(t.dataset.trame); aller('fiches'); return; }
  const c = e.target.closest('[data-controle]'); if (c) { e.preventDefault(); fermerTiroir(); filtreC = { type: '', crit: '', theme: '', file: '', seul: c.dataset.controle }; synchroFiltresC(); listerControles(); aller('controles'); return; }
  const th = e.target.closest('[data-theme-controle]'); if (th) { e.preventDefault(); filtreC = { type: '', crit: '', theme: th.dataset.themeControle, file: '', seul: '' }; synchroFiltresC(); listerControles(); aller('controles'); return; }
});

/* ------------------------------------------------------------------- tiroir */
const tiroir = $('#tiroir'), voile = $('#voile');
function ouvrirTiroir(surtitre, titre, texte, html) {
  $('#tiroir-surtitre').textContent = surtitre; $('#tiroir-titre').textContent = titre; $('#tiroir-texte').textContent = texte;
  $('#tiroir-corps').innerHTML = html; tiroir.classList.add('ouvert'); tiroir.setAttribute('aria-hidden', 'false'); voile.classList.add('visible'); $('#tiroir-fermer').focus();
}
function fermerTiroir() { tiroir.classList.remove('ouvert'); tiroir.setAttribute('aria-hidden', 'true'); voile.classList.remove('visible'); }
$('#tiroir-fermer').addEventListener('click', fermerTiroir); voile.addEventListener('click', fermerTiroir);
document.addEventListener('keydown', e => { if (e.key === 'Escape') fermerTiroir(); });

/* ================================================================= SYNTHESE */
(function () {
  const nR = FILES.filter(f => f.kind === 'R').length, nQ = FILES.filter(f => f.kind === 'Q').length, nA = FILES.filter(f => f.kind === 'A').length;
  const partagees = PIV.filter(p => p.nfiles >= 2).length, ponts = PIV.filter(passerelle).length;
  const tuiles = [[FILES.length, 'Trames', `${nR} recueils · ${nA} agrégats · ${nQ} questionnaires`], [D.fields.length, 'Colonnes', 'à renseigner dans les recueils'],
    [partagees, 'Données partagées', 'par au moins deux trames'], [ponts, 'Passerelles', 'entre patrimoine et gestion locative'],
    [D.controls.length, 'Contrôles', 'de cohérence avant envoi'], [D.alerts.length, 'Vigilances', 'sur les modèles et les données']];
  $('#tuiles').innerHTML = tuiles.map(([v, l, n], i) => `<div class="tuile${i === 0 ? ' accent' : ''}"><span class="etiquette">${l}</span><span class="valeur">${v}</span><span class="note">${n}</span></div>`).join('');
  const g = PD.GRP, l = PD.LOT, cp = PD.CPT;
  const ecarts = D.fields.filter(f => f.def_status === 'name_or_col_mismatch').length;
  const nominatives = D.alerts.find(a => a.id === 'A15').files.length;
  const top = Object.entries(D.prox).sort((a, b) => b[1].length - a[1].length)[0];
  const C = [
    ['Trois clés font tenir l\'ensemble', `Le code groupe est demandé dans ${g.nfiles} trames, l'identifiant logement dans ${l.nfiles}, le compte locataire dans ${cp.nfiles}, sous des noms et des formats différents. Elles doivent venir d'une table de correspondance unique.`],
    ['Deux trames servent de socle', `L'état des lieux du patrimoine (11_30_02) et les loyers des logements (12_30_02) fixent le référentiel groupe / bâtiment / lot / RPLS. La paire la plus liée est ${top[0].replace('|', ' ↔ ')}, avec ${top[1].length} données communes.`],
    ['Ventes et attributions font le pont', `La vente HLM (11_30_06) reprend bail, loyer et ressources de la gestion locative ; la CALEOL (12_30_01) reprend DPE, financement et QPV du patrimoine. ${ponts} données circulent entre les deux domaines.`],
    ['Huit dates de référence', 'Date d\'extraction 2026, 01/01/2025, 31/12/2025, fin N-1, et des périodes de 1 à 5 ans : sans tableau de passage, les volumes de logements ne se réconcilient pas.'],
    ['Des modèles à lire avec prudence', `${ecarts} en-têtes diffèrent de leur définition (colonnes inversées dans la cartographie énergétique au logement, ordre différent dans les réclamations) et 3 trames n'ont pas de définitions. ${nominatives} trames contiennent des données nominatives ou de revenus.`],
  ];
  $('#constats').innerHTML = C.map(c => `<li><b>${c[0]}</b><p>${c[1]}</p></li>`).join('');
  const niveaux = ['XL', 'L', 'M', 'S']; const max = Math.max(...niveaux.map(e => FILES.filter(f => f.effort === e).length));
  $('#barres-charge').innerHTML = niveaux.map(e => {
    const gp = FILES.filter(f => f.effort === e && f.dom === 'GP'), gl = FILES.filter(f => f.effort === e && f.dom === 'GL');
    const noms = [...gp, ...gl].map(f => `<span class="tech">${f.code}</span> ${esc(f.short)}`).join('<br>');
    return `<div class="barre" data-bulle="${esc(`<b>Charge ${EFFLAB[e].toLowerCase()}</b><br>${noms}`)}"><span class="libelle">${charge(e)}<span>${EFFLAB[e]}</span></span><span class="piste double">${gp.length ? `<span class="remplissage" style="width:${gp.length / max * 100}%;--fam:var(--accent)"></span>` : ''}${gl.length ? `<span class="remplissage" style="width:${gl.length / max * 100}%;--fam:var(--rampe-1)"></span>` : ''}</span><span class="nombre">${gp.length + gl.length}</span></div>`;
  }).join('');
  const tp = PIV.filter(p => p.id !== 'ORG').sort((a, b) => b.nfiles - a.nfiles).slice(0, 10); const mx = tp[0].nfiles;
  $('#barres-pivots').innerHTML = tp.map(p => `<div class="barre large" data-bulle="${esc(`<b>${esc(p.label)}</b><br><span class="tech">${tramesDe(p).join(', ')}</span>`)}"><span class="libelle"><i class="puce" style="${fam(p.fam)}"></i><span>${esc(p.label)}</span></span><span class="piste"><span class="remplissage" style="width:${p.nfiles / mx * 100}%;${fam(p.fam)}"></span></span><span class="nombre">${p.nfiles}</span></div>`).join('');
  const REFS = [
    ['Table groupe immobilier', 'Code, nom, adresse, commune, INSEE, EPCI, QPV, zonages, copropriété', ['GRP', 'GRP_NOM', 'COMMUNE', 'INSEE', 'QPV']],
    ['Table lot / RPLS / bâtiment', 'Identifiant lot, RPLS, groupe, bâtiment, typologie, surfaces, financement, conventionnement, DPE', ['LOT', 'RPLS', 'BAT', 'TYPO', 'SHAB', 'DPE']],
    ['Table commune × zonages', 'A/B/C, 1/2/3 et p/i/r/d pour chaque code INSEE', ['ZABC', 'Z123', 'ZGEO']],
    ['Passage financement initial → CUS', 'PLA, HLMO, ILN… vers PLAI, PLUS, PLS, PLI', ['FINI', 'FCUS']],
    ['Passage typologie ERP → T1…T7', 'Libellés de type de lot du quittancement', ['TYPO']],
    ['Référentiel des marchés', 'Référence, titulaire, nature, périmètre', ['MARCHE', 'TITU']],
    ['Comptes locataires', 'Compte, lot, titulaire, dates d\'entrée et de sortie', ['CPT', 'BAIL', 'SORTIE']],
    ['Tableau de passage des volumes', 'Parc au 01/01/2025 → mouvements → 31/12/2025 → date d\'extraction', ['NBLGT', 'MOUV']],
  ];
  $('#referentiels').innerHTML = REFS.map(r => `<div class="referentiel"><b>${r[0]}</b><span>${r[1]}</span><span>Utilisée par ${new Set(r[2].flatMap(id => PD[id] ? tramesDe(PD[id]) : [])).size} trames</span></div>`).join('');
  $('#pied-date').textContent = 'Analyse du 21/10/2026';
})();

/* ============================================================ CARTOGRAPHIE */
let seuil = 3, selCarto = null;
document.querySelectorAll('[data-seuil]').forEach(b => b.addEventListener('click', () => {
  seuil = +b.dataset.seuil; document.querySelectorAll('[data-seuil]').forEach(x => x.setAttribute('aria-pressed', x === b)); selCarto = null; dessinerCarto();
}));
$('#carto-q').addEventListener('change', () => { selCarto = null; dessinerCarto(); });
$('#carto-reset').addEventListener('click', () => { selCarto = null; focaliser(null); });
function dessinerCarto() {
  const svg = $('#carto-svg'); const avecQ = $('#carto-q').checked;
  const garder = c => avecQ || FD[c].kind !== 'Q';
  const piv = PIV.filter(p => p.id !== 'ORG').map(p => ({ ...p, fs: tramesDe(p).filter(garder) })).filter(p => p.fs.length >= seuil)
    .sort((a, b) => FAMIDX[a.fam] - FAMIDX[b.fam] || b.fs.length - a.fs.length);
  const gp = FILES.filter(f => f.dom === 'GP' && garder(f.code)), gl = FILES.filter(f => f.dom === 'GL' && garder(f.code));
  const W = 1180, pas = 17, ecart = 28, haut = 24;
  let y = haut, der = null; const pos = {}, debut = {};
  piv.forEach(p => { if (p.fam !== der) { y += der ? ecart : 24; der = p.fam; debut[p.fam] = y; } pos[p.id] = y; y += pas; });
  const H = Math.max(y + 10, 520);
  const repartir = arr => { const s = (H - haut - 20) / arr.length; return Object.fromEntries(arr.map((f, i) => [f.code, haut + 10 + s * (i + .5)])); };
  const yg = repartir(gp), yd = repartir(gl);
  const xG = 250, xD = W - 250, xP = W / 2 - 128, xP2 = W / 2 + 128;
  let s = '';
  piv.forEach(p => p.fs.forEach(c => {
    const py = pos[p.id];
    if (FD[c].dom === 'GP') { const fy = yg[c]; s += `<path class="lien" style="${fam(p.fam)}" data-t="${c}" data-p="${p.id}" d="M${xG + 8},${fy} C${(xG + xP) / 2},${fy} ${(xG + xP) / 2},${py} ${xP - 6},${py}"/>`; }
    else { const fy = yd[c]; s += `<path class="lien" style="${fam(p.fam)}" data-t="${c}" data-p="${p.id}" d="M${xD - 8},${fy} C${(xD + xP2) / 2},${fy} ${(xD + xP2) / 2},${py} ${xP2 + 6},${py}"/>`; }
  }));
  Object.entries(debut).forEach(([f, yy]) => { s += `<text class="t-famille" x="${W / 2}" y="${yy - 13}" text-anchor="middle">${esc(famLabel(f))}</text>`; });
  piv.forEach(p => {
    const py = pos[p.id], lab = p.label.length > 38 ? p.label.slice(0, 36) + '…' : p.label;
    s += `<g class="noeud n-pivot" data-p="${p.id}"><rect x="${xP - 4}" y="${py - 7}" width="${xP2 - xP + 8}" height="14" fill="transparent"/><circle class="rond-famille" style="${fam(p.fam)}" cx="${xP - 4}" cy="${py}" r="3.2"/><circle class="rond-famille" style="${fam(p.fam)}" cx="${xP2 + 4}" cy="${py}" r="3.2"/><text class="t-pivot" x="${W / 2}" y="${py + 4}" text-anchor="middle">${esc(lab)}${passerelle(p) ? ' ⇄' : ''}</text></g>`;
  });
  const noeud = (f, yy, cote) => {
    const n = piv.filter(p => p.fs.includes(f.code)).length, x = cote === 'G' ? xG : xD, r = 4 + Math.sqrt(n) * 1.4;
    const tx = cote === 'G' ? x - r - 7 : x + r + 7, ancre = cote === 'G' ? 'end' : 'start';
    return `<g class="noeud n-trame" data-t="${f.code}"><rect x="${cote === 'G' ? x - 245 : x - 4}" y="${yy - 16}" width="250" height="30" fill="transparent"/><circle class="rond-trame${f.kind === 'Q' ? ' questionnaire' : ''}" cx="${x}" cy="${yy}" r="${r.toFixed(1)}"/><text class="t-trame" x="${tx}" y="${yy - 1}" text-anchor="${ancre}">${esc(f.short)}</text><text class="t-code" x="${tx}" y="${yy + 12}" text-anchor="${ancre}">${f.code} · ${KIND[f.kind].toLowerCase()} · ${n} données</text></g>`;
  };
  gp.forEach(f => s += noeud(f, yg[f.code], 'G')); gl.forEach(f => s += noeud(f, yd[f.code], 'D'));
  s += `<text class="t-famille" x="${xG}" y="12" text-anchor="end">Patrimoine (GP)</text><text class="t-famille" x="${xD}" y="12">Gestion locative (GL)</text>`;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.innerHTML = s;
  $('#carto-legende').innerHTML = FAMS.map(f => `<span><i class="pastille-legende" style="${fam(f[0])}"></i>${esc(f[1])}</span>`).join('') + '<span>⇄ passerelle patrimoine ↔ gestion locative</span><span><svg width="12" height="12" class="dessin" aria-hidden="true"><circle class="rond-trame" cx="6" cy="6" r="4.5"/></svg>recueil</span><span><svg width="12" height="12" class="dessin" aria-hidden="true"><circle class="rond-trame questionnaire" cx="6" cy="6" r="4.5"/></svg>questionnaire</span>';
  svg.querySelectorAll('.n-trame').forEach(g => { g.addEventListener('pointerenter', () => focaliser({ t: g.dataset.t })); g.addEventListener('click', () => { selCarto = { t: g.dataset.t }; focaliser(selCarto); }); });
  svg.querySelectorAll('.n-pivot').forEach(g => { g.addEventListener('pointerenter', () => focaliser({ p: g.dataset.p })); g.addEventListener('click', () => { selCarto = { p: g.dataset.p }; focaliser(selCarto); }); });
  svg.onpointerleave = () => focaliser(selCarto);
  focaliser(selCarto);
}
function focaliser(sel) {
  const svg = $('#carto-svg'), info = $('#carto-info');
  svg.querySelectorAll('.on').forEach(n => n.classList.remove('on'));
  if (!sel) { svg.classList.remove('focus'); info.innerHTML = '<b>Sélectionnez une trame ou une donnée.</b> Le diamètre d\'une trame croît avec le nombre de données partagées qu\'elle mobilise.'; return; }
  svg.classList.add('focus');
  if (sel.t) {
    const ps = new Set(); svg.querySelectorAll(`.lien[data-t="${sel.t}"]`).forEach(l => { l.classList.add('on'); ps.add(l.dataset.p); });
    svg.querySelectorAll(`.n-trame[data-t="${sel.t}"]`).forEach(n => n.classList.add('on'));
    ps.forEach(p => svg.querySelectorAll(`.n-pivot[data-p="${p}"]`).forEach(n => n.classList.add('on')));
    const f = FD[sel.t];
    info.innerHTML = `<b>${sel.t} · ${esc(f.title)}</b> mobilise ${ps.size} des données affichées. Trames les plus proches : ${voisins(sel.t).slice(0, 4).map(([c, v]) => `${c} ${esc(FD[c].short)} (${v.length})`).join(', ')}. <button type="button" class="lien-interne" data-trame="${sel.t}">Ouvrir la fiche</button>`;
  } else {
    const fs = new Set(); svg.querySelectorAll(`.lien[data-p="${sel.p}"]`).forEach(l => { l.classList.add('on'); fs.add(l.dataset.t); });
    svg.querySelectorAll(`.n-pivot[data-p="${sel.p}"]`).forEach(n => n.classList.add('on'));
    fs.forEach(c => svg.querySelectorAll(`.n-trame[data-t="${c}"]`).forEach(n => n.classList.add('on')));
    const p = PD[sel.p];
    info.innerHTML = `<b>${esc(p.label)}</b> · ${esc(p.desc)} Présente dans ${fs.size} trames. Colonnes : <span class="tech">${p.names.slice(0, 8).map(esc).join(', ')}${p.names.length > 8 ? '…' : ''}</span>`;
  }
}

/* carte de chaleur de proximite */
(function () {
  const codes = ordreTrames.map(f => f.code);
  const marche = v => v <= 2 ? 1 : v <= 5 ? 2 : v <= 9 ? 3 : v <= 14 ? 4 : 5;
  let h = '<thead><tr><th></th>' + codes.map(c => `<th class="cl"><div>${c} ${esc(FD[c].short)}</div></th>`).join('') + '</tr></thead><tbody>';
  codes.forEach(a => {
    h += `<tr><th class="r">${a} <span>${esc(FD[a].short)}</span></th>`;
    codes.forEach(b => {
      if (a === b) { h += '<td class="c diag"></td>'; return; }
      const k = D.prox[a + '|' + b] || D.prox[b + '|' + a] || [], v = k.length;
      h += `<td class="c${v ? ' n' + marche(v) : ''}" data-bulle="${esc(`<b>${a} ↔ ${b}</b><br>${v} données communes${v ? ' : ' + k.map(id => PD[id] ? esc(PD[id].label) : id).join(', ') : ''}`)}">${v || ''}</td>`;
    });
    h += '</tr>';
  });
  // la charte peint les en-tetes de tableau en bleu nuit : ici l'en-tete est fait de libelles verticaux, on garde la surface
  $('#prox').innerHTML = h.replace('<thead>', '<thead class="nu">') + '</tbody>';
  $('#prox-legende').innerHTML = [['1-2', 1], ['3-5', 2], ['6-9', 3], ['10-14', 4], ['15 et +', 5]].map(([l, n]) => `<span><i class="pastille-legende cle-n${n}"></i>${l}</span>`).join('');
})();

/* ================================================================ MATRICE */
$('#mx-fam').innerHTML = '<option value="">Toutes les familles</option>' + FAMS.map(f => `<option value="${f[0]}">${esc(f[1])}</option>`).join('');
let selMx = null;
function dessinerMatrice() {
  const fa = $('#mx-fam').value, q = $('#mx-q').value.trim().toLowerCase(), partage = $('#mx-partage').checked;
  const lignes = PIV.filter(p => (!fa || p.fam === fa) && (!partage || p.nfiles >= 2) && (!q || (p.label + ' ' + p.names.join(' ') + ' ' + p.desc).toLowerCase().includes(q)))
    .sort((a, b) => FAMIDX[a.fam] - FAMIDX[b.fam] || b.nfiles - a.nfiles);
  const nGP = FILES.filter(f => f.dom === 'GP').length;
  let h = '<thead><tr><th>Donnée pivot</th><th class="num">Trames</th>' + ordreTrames.map((f, i) => `<th class="cl${i === nGP ? ' sep' : ''}" title="${esc(f.title)}"><div>${f.code} ${esc(f.short)}</div></th>`).join('') + '</tr></thead><tbody>';
  let der = null;
  lignes.forEach(p => {
    if (p.fam !== der) { der = p.fam; h += `<tr class="famille"><td colspan="${ordreTrames.length + 2}"><span>${esc(famLabel(p.fam))}</span></td></tr>`; }
    h += `<tr data-p="${p.id}" class="${selMx === p.id ? 'choisi' : ''}"><td class="lab" title="${esc(p.desc)}"><i class="puce" style="${fam(p.fam)}"></i>${esc(p.label)}</td><td class="n">${p.nfiles}</td>`;
    ordreTrames.forEach((f, i) => {
      const n = p.files[f.code] || 0, qq = p.qfiles.includes(f.code);
      const marque = n ? `<span class="disque d${n === 1 ? 1 : n <= 3 ? 2 : 3}"></span>` : qq ? '<span class="anneau"></span>' : '';
      const b = n ? `<b>${f.code} ${esc(f.short)}</b><br>${esc(p.label)} : ${n} colonne${n > 1 ? 's' : ''}<br><span class="tech">${D.fields.filter(x => x.file === f.code && x.pivot === p.id).slice(0, 6).map(x => esc(x.name)).join('<br>')}</span>` : qq ? `<b>${f.code} ${esc(f.short)}</b><br>Abordée dans le questionnaire` : '';
      h += `<td class="c${i === nGP ? ' sep' : ''}"${b ? ` data-bulle="${esc(b)}"` : ''}>${marque}</td>`;
    });
    h += '</tr>';
  });
  $('#mx').innerHTML = h + '</tbody>';
}
['#mx-fam', '#mx-q', '#mx-partage'].forEach(s => $(s).addEventListener('input', dessinerMatrice));
$('#mx').addEventListener('click', e => { const tr = e.target.closest('tr[data-p]'); if (!tr || !e.target.closest('td.lab')) return; selMx = tr.dataset.p; dessinerMatrice(); detailPivot(selMx); });
function detailPivot(id) {
  const p = PD[id], champs = D.fields.filter(x => x.pivot === id), ctl = D.controls.filter(c => c.pivots.includes(id));
  ouvrirTiroir(famLabel(p.fam), p.label, p.desc, `
    <div class="cadre-table"><table><thead><tr><th>Trame</th><th>Onglet</th><th>Col.</th><th>Colonne</th><th>Format</th></tr></thead><tbody>${champs.map(x => `<tr title="${esc(x.definition)}"><td>${codeTrame(x.file)}</td><td>${esc(x.sheet)}</td><td class="tech">${x.col}</td><td class="tech">${esc(x.name)}</td><td>${esc(x.fmt)}</td></tr>`).join('')}</tbody></table></div>
    ${p.qfiles.length ? `<div class="bloc"><span class="etiquette-bloc">Abordée dans les questionnaires</span><div class="jetons">${p.qfiles.map(codeTrame).join('')}</div></div>` : ''}
    ${ctl.length ? `<div class="bloc"><span class="etiquette-bloc">Contrôles qui l'utilisent</span><div class="jetons">${ctl.map(c => `<button type="button" class="jeton ${CRIT[c.crit][1]}" data-controle="${c.id}">${c.id} · ${esc(c.title)}</button>`).join('')}</div></div>` : ''}`);
}
dessinerMatrice();

/* ================================================================== THEMES */
$('#themes').innerHTML = D.themes.map(t => {
  const ctl = D.controls.filter(c => c.theme === t.id), bloq = ctl.filter(c => c.crit === 1).length;
  const nal = D.alerts.filter(a => a.files.some(f => t.files.includes(f))).length;
  const pv = [...new Set(t.files.flatMap(c => FD[c].pivots))].filter(id => id !== 'ORG' && PD[id]);
  const alignees = pv.filter(id => t.files.filter(c => FD[c].pivots.includes(id)).length >= 2).sort((a, b) => PD[b].nfiles - PD[a].nfiles).slice(0, 6);
  return `<article class="carte"><header><h3>${esc(t.label)}</h3></header><div class="corps"><p>${esc(t.enjeu)}</p>
    <div class="bloc"><span class="etiquette-bloc">Trames</span><div class="jetons">${t.files.map(codeTrame).join('')}</div></div>
    <div class="bloc"><span class="etiquette-bloc">Données à garder alignées</span><div class="jetons">${alignees.map(jetonPivot).join('')}</div></div></div>
    <footer><button type="button" class="bouton second" data-theme-controle="${t.id}">${ctl.length} contrôle${ctl.length > 1 ? 's' : ''}${bloq ? ` · ${bloq} bloquant${bloq > 1 ? 's' : ''}` : ''}</button><span class="compte">${nal} vigilance${nal > 1 ? 's' : ''} liée${nal > 1 ? 's' : ''}</span></footer></article>`;
}).join('');

/* =============================================================== CONTROLES */
let filtreC = { type: '', crit: '', theme: '', file: '', seul: '' };
$('#c-type').innerHTML = '<option value="">Tous types</option>' + [...new Set(D.controls.map(c => c.typ))].map(t => `<option>${esc(t)}</option>`).join('');
$('#c-theme').innerHTML = '<option value="">Tous thèmes</option>' + D.themes.map(t => `<option value="${t.id}">${esc(t.label)}</option>`).join('');
$('#c-file').innerHTML = '<option value="">Toutes trames</option>' + FILES.map(f => `<option value="${f.code}">${f.code} ${esc(f.short)}</option>`).join('');
function synchroFiltresC() { $('#c-type').value = filtreC.type; $('#c-crit').value = filtreC.crit; $('#c-theme').value = filtreC.theme; $('#c-file').value = filtreC.file; }
function listerControles() {
  const L = D.controls.filter(c => (!filtreC.seul || c.id === filtreC.seul) && (!filtreC.type || c.typ === filtreC.type) && (!filtreC.crit || c.crit == filtreC.crit) && (!filtreC.theme || c.theme === filtreC.theme) && (!filtreC.file || c.files.includes(filtreC.file)));
  $('#c-compte').textContent = `${L.length} / ${D.controls.length} contrôles` + (filtreC.seul ? ' · ' + filtreC.seul : '');
  $('#ctl-liste').innerHTML = L.map(c => `<article class="regle n${c.crit}"><div class="lisere"></div><div class="contenu">
    <div class="tete"><span class="ident">${c.id}</span><h3>${esc(c.title)}</h3>${jetonCrit(c.crit)}<span class="jeton">${esc(c.typ)}</span><span class="jeton">${esc(THEMES[c.theme]?.label || '')}</span></div>
    <p>${esc(c.rule)}</p><p class="test"><b>Comment tester :</b> ${esc(c.test)}</p>
    <div class="jetons">${c.files.map(codeTrame).join('')}${c.pivots.map(jetonPivot).join('')}</div></div></article>`).join('') || '<div class="vide">Aucun contrôle pour ce filtre.</div>';
}
['type', 'crit', 'theme', 'file'].forEach(k => $('#c-' + k).addEventListener('change', e => { filtreC[k] = e.target.value; filtreC.seul = ''; listerControles(); }));
$('#c-reset').addEventListener('click', () => { filtreC = { type: '', crit: '', theme: '', file: '', seul: '' }; synchroFiltresC(); listerControles(); });
listerControles();

/* ================================================================= ALERTES */
(function () {
  const cats = [...new Set(D.alerts.map(a => a.cat))];
  $('#alertes').innerHTML = cats.map(cat => `<div class="liste groupe-alertes"><h3 class="titre-groupe">${esc(cat)}</h3>${D.alerts.filter(a => a.cat === cat).map(a => `<article class="regle n${a.lvl}"><div class="lisere"></div><div class="contenu">
    <div class="tete"><span class="ident">${a.id}</span><h3>${esc(a.title)}</h3><span class="jeton ${NIV[a.lvl][1]}">${NIV[a.lvl][0]}</span></div>
    <p>${esc(a.detail)}</p><p class="test"><b>Conduite à tenir :</b> ${esc(a.action)}</p><div class="jetons">${a.files.map(codeTrame).join('')}</div></div></article>`).join('')}</div>`).join('');
  const T = {
    '11_30_01': [['p', '2021-01-01', '2025-12-31', 'PCRC'], ['s', '2025-12-31', 'stock PCRC'], ['s', 'EXT', 'photo']],
    '11_30_02': [['p', '2021-01-01', '2025-12-31', 'cumuls 5 ans'], ['s', '2026-01-01', 'vacance'], ['s', 'EXT', 'photo']],
    '11_30_03': [['p', '2024-01-01', '2025-12-31', 'N-2, N-1'], ['s', 'EXT', 'photo']],
    '11_30_04': [['p', '2021-01-01', '2025-12-31', 'adaptation'], ['s', '2025-12-31', 'accessibilité']],
    '11_30_05': [['p', '2021-01-01', '2025-12-31', 'opérations'], ['s', '2025-12-31', 'fin N-1']],
    '11_30_06': [['p', '2021-01-01', '2025-12-31', 'ventes'], ['s', 'EXT', 'à date']],
    '11_30_07': [['p', '2021-01-01', '2025-12-31', 'livraisons et ventes']],
    '11_30_08': [['s', '2025-01-01', '01/01/2025']],
    '11_30_09': [['p', '2023-01-01', '2025-12-31', '3 dernières années']],
    '11_30_10': [['p', '2024-01-01', '2025-12-31', 'N-2, N-1']],
    '12_30_01': [['p', '2023-01-01', '2025-12-31', 'CALEOL N-3 à N-1']],
    '12_30_02': [['s', '2025-01-01', '01/01/2025']],
    '12_30_03': [['p', '2021-01-01', '2025-12-31', 'charges N-5 à N-1']],
    '12_30_04': [['p', '2024-01-01', '2025-12-31', 'enquêtes SLS']],
    '12_30_05': [['p', '2025-01-01', '2025-12-31', '12 mois'], ['s', '2025-12-31', 'soldes']],
    '12_30_06': [['p', '2021-01-01', '2025-12-31', 'réclamations']],
    '12_30_07': [['p', '2025-01-01', '2025-12-31', 'sorties 2025']],
    '12_30_08': [['p', '2023-01-01', '2025-12-31', '3 dernières années']],
    '12_30_09': [['p', '2021-01-01', '2025-12-31', 'période de contrôle']],
    '12_30_10': [['p', '2021-01-01', '2025-12-31', 'période de contrôle']],
    '12_30_11': [['p', '2023-01-01', '2025-12-31', 'N-3 à N-1']],
    '12_30_12': [['p', '2021-01-01', '2025-12-31', 'annuel'], ['s', 'EXT', 'N à date']],
  };
  const t0 = Date.parse('2021-01-01'), t1 = Date.parse('2027-01-01'), W = 1180, G = 250, Dr = W - 20, pas = 26, haut = 34, EXT = '2026-10-01';
  const x = d => G + (Date.parse(d === 'EXT' ? EXT : d) - t0) / (t1 - t0) * (Dr - G);
  const H = haut + ordreTrames.length * pas + 24;
  let s = `<rect class="periode-controlee" x="${x('2021-01-01')}" y="${haut - 8}" width="${x('2026-01-01') - x('2021-01-01')}" height="${H - haut + 2}"/>`;
  for (let a = 2021; a <= 2027; a++) { const xx = x(a + '-01-01'); s += `<line class="grille" x1="${xx}" x2="${xx}" y1="${haut - 8}" y2="${H - 6}"/>`; if (a < 2026) s += `<text class="t-axe" x="${xx + (x((a + 1) + '-01-01') - xx) / 2}" y="${haut - 14}" text-anchor="middle">${a}</text>`; }
  s += `<text class="t-axe" x="${x(EXT)}" y="${haut - 14}" text-anchor="middle">2026 · extraction</text><text class="t-petrole" x="${x('2021-01-01') + 4}" y="${H - 4}">période contrôlée</text>`;
  ordreTrames.forEach((f, i) => {
    const y = haut + i * pas + pas / 2;
    s += `<text class="t-code" x="8" y="${y + 4}">${f.code}</text><text class="t-axe" x="70" y="${y + 4}" style="fill:var(--encre)">${esc(f.short)}</text>`;
    (T[f.code] || []).forEach(seg => {
      if (seg[0] === 'p') { const a = x(seg[1]), b = x(seg[2]); s += `<rect class="periode${f.dom === 'GL' ? ' gl' : ''}" x="${a}" y="${y - 5}" width="${Math.max(b - a, 3)}" height="10" rx="3" data-bulle="${esc(`<b>${f.code} ${esc(f.short)}</b><br>${seg[3]} : ${seg[1].slice(0, 4)} → ${seg[2].slice(0, 4)}`)}"/>`; }
      else { const a = x(seg[1]); s += `<rect class="photo" x="${a - 6}" y="${y - 6}" width="12" height="12" transform="rotate(45 ${a} ${y})" data-bulle="${esc(`<b>${f.code} ${esc(f.short)}</b><br>Photo : ${seg[2]}${seg[1] === 'EXT' ? ' (date d\'extraction 2026)' : ' au ' + seg[1].split('-').reverse().join('/')}`)}"/>`; }
    });
  });
  const svg = $('#frise'); svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.innerHTML = s;
})();

/* ================================================================== FICHES */
(function () {
  let h = '';
  [['GP', 'Patrimoine'], ['GL', 'Gestion locative']].forEach(([d, l]) => { h += `<div class="nav-groupe">${l}</div>`; FILES.filter(f => f.dom === d).forEach(f => h += `<button type="button" data-fiche="${f.code}"><span class="tech">${f.code}</span><span>${esc(f.short)}</span>${charge(f.effort)}</button>`); });
  $('#liste-fiches').innerHTML = h;
  $('#liste-fiches').addEventListener('click', e => { const b = e.target.closest('button[data-fiche]'); if (b) { afficherFiche(b.dataset.fiche); if (innerWidth < 900) $('#fiche').scrollIntoView({ behavior: 'smooth' }); } });
})();
function afficherFiche(code) {
  const f = FD[code]; document.querySelectorAll('#liste-fiches button').forEach(b => b.setAttribute('aria-current', b.dataset.fiche === code));
  const champs = D.fields.filter(x => x.file === code);
  const onglets = [...new Set(champs.map(x => x.sheet))].map(s => [s, champs.filter(x => x.sheet === s).length]), omax = Math.max(1, ...onglets.map(o => o[1]));
  const ctl = D.controls.filter(c => c.files.includes(code)), al = D.alerts.filter(a => a.files.includes(code)), vs = voisins(code).slice(0, 8);
  const ecarts = champs.filter(x => x.def_status === 'name_or_col_mismatch');
  const pv = f.pivots.filter(id => PD[id]).sort((a, b) => FAMIDX[PD[a].fam] - FAMIDX[PD[b].fam]);
  $('#fiche').innerHTML = `<header><div><span class="surtitre">${f.code} · ${DOM[f.dom]} · ${KIND[f.kind]}</span><h2>${esc(f.title)}</h2></div>
    <div class="jetons"><span class="jeton taupe">${VAGUES[f.wave][0]} · ${VAGUES[f.wave][1]}</span>${f.personal ? '<span class="jeton rouge">Données nominatives</span>' : ''}</div></header>
   <div class="corps">
    <p class="doux" style="margin:0">${esc(f.enjeux)}</p>
    <dl class="paire"><dt>Maille</dt><dd>${esc(f.maille)}</dd><dt>Période</dt><dd>${esc(f.period)}</dd><dt>Format</dt><dd>${esc(f.fmt)}</dd><dt>Volumétrie</dt><dd>${esc(f.vol)}</dd>
     <dt>Charge estimée</dt><dd>${charge(f.effort)} ${EFFLAB[f.effort]}</dd><dt>Sources probables</dt><dd>${esc(f.sources)}</dd><dt>Hors SI / manuel</dt><dd>${esc(f.manual)}</dd>
     ${f.kind !== 'Q' ? `<dt>Colonnes</dt><dd>${f.nfields} dans ${f.nsheets} onglet${f.nsheets > 1 ? 's' : ''}${f.nmand ? ` · ${f.nmand} obligatoires (**)` : ''}${ecarts.length ? ` · <span class="jeton rouge">${ecarts.length} écart${ecarts.length > 1 ? 's' : ''} définition / recueil</span>` : ''}</dd>` : ''}</dl>
    ${onglets.length ? `<div class="bloc"><span class="etiquette-bloc">Onglets de recueil</span><div class="onglets-recueil">${onglets.map(([s, n]) => `<div class="onglet-recueil"><span>${esc(s)}</span><span class="tech doux" style="text-align:right">${n}</span><span class="remplissage" style="width:${n / omax * 100}%"></span></div>`).join('')}</div></div>` : ''}
    ${f.qsections ? `<div class="bloc"><span class="etiquette-bloc">Sections et données mobilisées</span>${f.qsections.map(q => `<div class="section-q"><b>${esc(q.s)}</b><div class="jetons">${q.p.filter(id => PD[id]).map(jetonPivot).join('')}</div><div class="jetons"><span class="compte">À rapprocher de</span>${q.f.map(codeTrame).join('')}</div></div>`).join('')}</div>` : ''}
    <div class="bloc"><span class="etiquette-bloc">Données pivots mobilisées (${pv.length})</span><div class="jetons">${pv.map(jetonPivot).join('')}</div></div>
    <div class="bloc"><span class="etiquette-bloc">Trames qui partagent le plus de données</span><div class="barres">${vs.map(([c, v]) => `<div class="barre large" data-bulle="${esc(v.map(id => PD[id] ? esc(PD[id].label) : id).join(', '))}"><span class="libelle">${codeTrame(c)}<span>${esc(FD[c].short)}</span></span><span class="piste"><span class="remplissage" style="width:${v.length / vs[0][1].length * 100}%"></span></span><span class="nombre">${v.length}</span></div>`).join('')}</div></div>
    <div class="bloc"><span class="etiquette-bloc">Contrôles de cohérence (${ctl.length})</span><div class="jetons">${ctl.map(c => `<button type="button" class="jeton ${CRIT[c.crit][1]}" data-controle="${c.id}">${c.id} · ${esc(c.title)}</button>`).join('') || '<span class="doux">Aucun</span>'}</div></div>
    <div class="bloc"><span class="etiquette-bloc">Points de vigilance (${al.length})</span><div class="liste">${al.map(a => `<div><span class="jeton ${NIV[a.lvl][1]}">${a.id}</span> ${esc(a.title)}</div>`).join('') || '<span class="doux">Aucun</span>'}</div></div>
   </div>`;
}
afficherFiche('11_30_02');

/* ============================================================ ORGANISATION */
(function () {
  $('#vagues').innerHTML = VAGUES.map((v, i) => `<div class="vague"><div class="tete-vague"><span class="surtitre">${v[0]}</span><b>${v[1]}</b><span>${v[2]}</span></div>${FILES.filter(f => f.wave === i).sort((a, b) => EFF[b.effort] - EFF[a.effort]).map(f => `<button type="button" class="carte-trame" data-trame="${f.code}"><span class="t">${esc(f.short)}</span><span class="m"><span class="tech">${f.code} · ${f.dom}</span>${charge(f.effort)}</span></button>`).join('')}</div>`).join('');
  const dep = f => voisins(f.code).filter(([c, v]) => FD[c].wave < f.wave && v.length >= 3).map(([c]) => c);
  const lignes = [...FILES].sort((a, b) => a.wave - b.wave || EFF[b.effort] - EFF[a.effort]);
  $('#orga-table').innerHTML = `<thead><tr><th>Vague</th><th>Trame</th><th>Type</th><th>Charge</th><th class="num">Colonnes</th><th>Maille</th><th>Dépend de</th><th>Données hors SI</th><th>Porteur</th><th>Échéance</th></tr></thead><tbody>${lignes.map(f => `<tr><td class="num">${f.wave}</td><td>${codeTrame(f.code)} ${esc(f.short)}</td><td>${KIND[f.kind]}</td><td style="white-space:nowrap">${charge(f.effort)} ${EFFLAB[f.effort]}</td><td class="num">${f.kind === 'Q' ? '—' : f.nfields}</td><td><span class="tronque">${esc(f.maille)}</span></td><td class="tech">${dep(f).join(', ') || '—'}</td><td><span class="tronque" title="${esc(f.manual)}">${esc(f.manual)}</span></td><td class="doux">à affecter</td><td class="doux">—</td></tr>`).join('')}</tbody>`;
  $('#orga-copier').addEventListener('click', () => copier(csv([['Vague', 'Code', 'Trame', 'Domaine', 'Type', 'Charge', 'Colonnes', 'Maille', 'Période', 'Dépend de', 'Données hors SI', 'Porteur', 'Échéance']].concat(lignes.map(f => [f.wave, f.code, f.title, DOM[f.dom], KIND[f.kind], EFFLAB[f.effort], f.kind === 'Q' ? '' : f.nfields, f.maille, f.period, dep(f).join(', '), f.manual, '', '']))), $('#orga-secours')));
})();

/* ============================================================== INVENTAIRE */
$('#inv-file').innerHTML = '<option value="">Toutes trames</option>' + FILES.filter(f => f.nfields).map(f => `<option value="${f.code}">${f.code} ${esc(f.short)}</option>`).join('');
$('#inv-fam').innerHTML = '<option value="">Toutes familles</option>' + FAMS.map(f => `<option value="${f[0]}">${esc(f[1])}</option>`).join('') + '<option value="_aucune">Sans donnée pivot</option>';
const STATUT = { ok: 'Conforme', nodef: 'Sans définition', name_or_col_mismatch: 'Écart', missing: 'Absente' };
let lignesInv = [];
function listerInventaire() {
  const q = $('#inv-q').value.trim().toLowerCase(), fi = $('#inv-file').value, fa = $('#inv-fam').value, st = $('#inv-st').value;
  lignesInv = D.fields.filter(x => (!fi || x.file === fi) && (!st || x.def_status === st) && (!fa || (fa === '_aucune' ? !x.pivot : (x.pivot && PD[x.pivot] && PD[x.pivot].fam === fa))) && (!q || (x.name + ' ' + x.definition + ' ' + x.sheet + ' ' + (x.pivot && PD[x.pivot] ? PD[x.pivot].label : '')).toLowerCase().includes(q)));
  $('#inv-compte').textContent = `${lignesInv.length} colonne${lignesInv.length > 1 ? 's' : ''} sur ${D.fields.length}`;
  $('#inv').innerHTML = `<thead><tr><th>Trame</th><th>Onglet</th><th>Col.</th><th>Champ</th><th>Donnée pivot</th><th>Définition ANCOLS</th><th>Format</th><th>Statut</th></tr></thead><tbody>${lignesInv.map(x => `<tr><td class="tech">${x.file}</td><td>${esc(x.sheet)}</td><td class="tech">${x.col}</td><td class="tech" style="word-break:break-word">${esc(x.name)}${x.mandatory ? ' <span class="jeton rouge" title="obligatoire">**</span>' : ''}</td><td>${x.pivot && PD[x.pivot] ? `<span style="display:inline-flex;gap:6px;align-items:center"><i class="puce" style="${fam(PD[x.pivot].fam)}"></i>${esc(PD[x.pivot].label)}</span>` : '<span class="doux">—</span>'}</td><td><span class="tronque" title="${esc(x.definition + (x.values ? ' — ' + x.values : ''))}">${esc(x.definition)}</span></td><td>${esc(x.fmt)}</td><td>${x.def_status === 'name_or_col_mismatch' ? `<span class="jeton ambre" title="Définition à cette lettre de colonne : ${esc(x.def_name_at_col || '')}">Écart</span>` : `<span class="jeton${x.def_status === 'ok' ? ' vert' : ''}">${STATUT[x.def_status] || x.def_status}</span>`}</td></tr>`).join('')}</tbody>`;
}
['#inv-q', '#inv-file', '#inv-fam', '#inv-st'].forEach(s => $(s).addEventListener('input', listerInventaire));
$('#inv-copier').addEventListener('click', () => copier(csv([['Trame', 'Onglet', 'Colonne', 'Champ', 'Obligatoire', 'Donnée pivot', 'Famille', 'Définition', 'Valeurs attendues', 'Format', 'Statut définition']].concat(lignesInv.map(x => [x.file, x.sheet, x.col, x.name, x.mandatory ? 'oui' : '', x.pivot && PD[x.pivot] ? PD[x.pivot].label : '', x.pivot && PD[x.pivot] ? famLabel(PD[x.pivot].fam) : '', x.definition, x.values, x.fmt, STATUT[x.def_status] || x.def_status]))), $('#inv-secours')));
listerInventaire();

/* ================================================================= ETAPE 2 */
(function () {
  const produits = [['Correspondance donnée pivot → champ source', `Pour chacune des ${PIV.length} données pivots : application, table, champ, règle de calcul éventuelle.`],
    ['Couverture du besoin', 'Données disponibles dans le SI, à calculer, ou à collecter manuellement, trame par trame.'],
    ['Contrôles exécutables', 'Les contrôles de cohérence traduits en requêtes ou en formules sur les champs sources.'],
    ['Plan de charge affiné', 'Charge réévaluée selon la disponibilité réelle des données.']];
  const questions = [['Format du dictionnaire', 'Idéalement : champ, table, application, définition métier, format, liste de valeurs, propriétaire.'],
    ['Clés et historisation', 'Le dictionnaire distingue-t-il identifiant lot interne et RPLS ? Les valeurs sont-elles historisées (photo au 01/01/2025, au 31/12/2025) ?'],
    ['Référentiels de valeurs', 'Listes de valeurs des financements, typologies, natures de lot, rubriques de quittancement et natures de charges.'],
    ['Applications hors ERP', 'Bases DPE, diagnostics, GMAO, CRM, outils de vente et d\'accession, tableaux de suivi internes.']];
  $('#etape2-produits').innerHTML = produits.map(c => `<li><b>${c[0]}</b><p>${c[1]}</p></li>`).join('');
  $('#etape2-questions').innerHTML = questions.map(c => `<li><b>${c[0]}</b><p>${c[1]}</p></li>`).join('');
  const cles = ['GRP', 'LOT', 'RPLS', 'BAT', 'CPT', 'MARCHE', 'OPE'];
  const rang = PIV.filter(p => p.id !== 'ORG').map(p => ({ p, r: cles.includes(p.id) ? 0 : passerelle(p) ? 1 : 2 })).sort((a, b) => a.r - b.r || b.p.nfiles - a.p.nfiles);
  const LIB = [['Clé de jointure', 'rouge'], ['Passerelle GP ↔ GL', 'petrole'], ['Spécifique', '']];
  $('#prio').innerHTML = `<thead><tr><th class="num">#</th><th>Donnée pivot</th><th>Famille</th><th>Priorité</th><th class="num">Trames</th><th class="num">Colonnes</th><th>Noms rencontrés</th><th>Champ source</th></tr></thead><tbody>${rang.map((o, i) => { const p = o.p, nc = Object.values(p.files).reduce((a, b) => a + b, 0); return `<tr><td class="num">${i + 1}</td><td><b>${esc(p.label)}</b></td><td><span style="display:inline-flex;gap:6px;align-items:center"><i class="puce" style="${fam(p.fam)}"></i>${esc(famLabel(p.fam))}</span></td><td><span class="jeton ${LIB[o.r][1]}">${LIB[o.r][0]}</span></td><td class="num">${p.nfiles}</td><td class="num">${nc}</td><td class="tech"><span class="tronque">${p.names.slice(0, 6).map(esc).join(', ')}${p.names.length > 6 ? ' …' : ''}</span></td><td class="doux">à compléter</td></tr>`; }).join('')}</tbody>`;
})();

/* -------------------------------------------------------------- demarrage */
let depart = 'synthese'; try { const h = location.hash.slice(1); if (h && document.getElementById('vue-' + h)) depart = h; } catch (e) { }
aller(depart, true);
addEventListener('resize', () => { if ($('#vue-cartographie').classList.contains('actif')) dessinerCarto(); });
})();

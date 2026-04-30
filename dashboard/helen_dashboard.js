/* HELEN OS Dashboard — NON_SOVEREIGN READ-ONLY
   Loads mock_state.json (or /api/state if served via helen_dashboard.py).
   Auto-refreshes every 30s. No sovereign writes. */

const STATE_URL   = './mock_state.json';
const API_URL     = '/api/state';
const REFRESH_MS  = 30000;

// ── state loading ─────────────────────────────────────────────────────────

async function loadState() {
  // Try live API first, fall back to mock
  for (const url of [API_URL, STATE_URL]) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (res.ok) return await res.json();
    } catch (_) { /* try next */ }
  }
  return null;
}

// ── render helpers ────────────────────────────────────────────────────────

function el(id) { return document.getElementById(id); }

function statusClass(s) {
  if (!s) return '';
  const v = s.toLowerCase();
  if (v === 'ok')      return 'd-ok';
  if (v === 'warn')    return 'd-warn';
  if (v === 'blocked') return 'd-blocked';
  return 'd-warn';
}

function globalStatusClass(s) {
  if (!s) return '';
  switch (s.toUpperCase()) {
    case 'BLOCKED':  return 'gs-blocked';
    case 'READY':    return 'gs-ready';
    case 'PROPOSAL': return 'gs-proposal';
    case 'SHIPPED':  return 'gs-shipped';
    default:         return 'gs-proposal';
  }
}

// ── banner ────────────────────────────────────────────────────────────────

function renderBanner(state) {
  const gs   = state.global_status || 'PROPOSAL';
  const gcls = globalStatusClass(gs);
  el('global-status').textContent  = gs;
  el('global-status').className    = `global-status ${gcls}`;
  el('clock').textContent          =
    new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC · auto-refresh 30s';
  el('authority-label').textContent = `${state.authority || 'NON_SOVEREIGN'} · ${state.canon || 'NO_SHIP'}`;
}

// ── center: 4-layer stack ─────────────────────────────────────────────────

function renderLayers(layers) {
  const stack = el('layer-stack');
  stack.innerHTML = layers.map(L => {
    const sov  = L.sovereign;
    const ccls = sov ? 'layer-card sovereign' : 'layer-card';
    const zcls = sov ? 'zone-badge zone-sov'  : 'zone-badge zone-ns';
    return `
<div class="${ccls}">
  <div class="layer-top">
    <div>
      <div class="layer-id">${L.id}</div>
      <div class="layer-name">${L.name}</div>
      <div class="layer-sub">${L.subtitle}</div>
    </div>
    <span class="${zcls}">${L.label}</span>
  </div>
  <div class="layer-desc">${L.description}</div>
  <div class="layer-note">${L.note}</div>
</div>`;
  }).join('');
}

// ── left: epoch3 + claim graph ────────────────────────────────────────────

function renderEpoch3(epoch3) {
  // phases
  const phaseMap = { DONE: 'dot-done', PENDING: 'dot-pending', IDLE: 'dot-idle' };
  el('epoch3-phases').innerHTML = epoch3.phases.map(p => `
<div class="phase-row">
  <span class="phase-id">${p.id}</span>
  <div class="phase-dot ${phaseMap[p.status] || 'dot-idle'}"></div>
  <span class="phase-name">${p.name}</span>
  <span class="phase-note">${p.note}</span>
</div>`).join('');

  // seed
  const seed = epoch3.seed || '—';
  el('epoch3-seed').innerHTML =
    `<div class="seed-label">deterministic seed</div>${seed}`;

  // claim graph
  el('claim-graph').innerHTML = epoch3.claim_graph.map(c => {
    const bcls = c.status === 'BOUND' ? 'bound' : 'unbound';
    const scls = c.status === 'BOUND' ? 's-bound' : 's-unbound';
    return `<div class="claim-row ${bcls}">
  <span class="claim-id">${c.id}</span>
  <span class="claim-text">${c.text}</span>
  <span class="claim-status ${scls}">${c.status}</span>
</div>`;
  }).join('');
}

// ── right: governance ─────────────────────────────────────────────────────

function renderGovernance(gov) {
  // pipeline
  el('governance-pipeline').innerHTML = gov.pipeline.map((s, i) => {
    const dcls = statusClass(s.status);
    const arrow = i < gov.pipeline.length - 1
      ? `<div class="pipe-arrow">↓</div>` : '';
    return `<div class="pipe-step">
  <div class="status-dot ${dcls}"></div>
  <span class="pipe-name">${s.step}</span>
  <span class="pipe-note">${s.note}</span>
</div>${arrow}`;
  }).join('');

  // obligations
  el('obligations').innerHTML = gov.obligations.map(o => {
    const ocls = o.status.toLowerCase();
    const scls = `s-${ocls}`;
    return `<div class="obl-row ${ocls}">
  <div class="obl-id">${o.id}</div>
  <div class="obl-text">${o.text}</div>
  <div class="obl-stat ${scls}">${o.status}</div>
</div>`;
  }).join('');

  // receipts
  el('receipts').innerHTML = gov.receipts.map(r => {
    const scls = `rs-${r.status.toLowerCase().split('_')[0]}`;
    return `<div class="receipt-row">
  <span class="receipt-id">${r.id}</span>
  <span class="receipt-schema">${r.schema}<br><span style="color:var(--muted);font-size:8px">${r.bound_to}</span></span>
  <span class="receipt-status ${scls}">${r.status}</span>
</div>`;
  }).join('');

  // verdict readiness
  const vr   = gov.verdict_readiness;
  const vblocked = vr.status === 'BLOCKED';
  const vcls = vblocked ? 'verdict-box blocked' : 'verdict-box ready';
  const missing = (vr.missing_obligations || []).concat(vr.missing_receipts || []);
  const missingHtml = missing.length
    ? `<div class="verdict-missing">Missing:<ul>${missing.map(m => `<li>${m}</li>`).join('')}</ul></div>` : '';
  el('verdict-readiness').innerHTML = `
<div class="${vcls}">
  <div class="verdict-title">${vr.status}</div>
  <div class="verdict-reason">${vr.reason}</div>
  ${missingHtml}
  <div style="font-size:8px;color:var(--muted2);margin-top:4px">
    CAN SHIP: ${vr.can_ship ? '✓ YES' : '✗ NO'}
  </div>
</div>`;
}

// ── bottom: ledger strip ──────────────────────────────────────────────────

function renderLedger(ledger) {
  el('l-count').textContent    = ledger.entry_count;
  el('l-seq').textContent      = ledger.last_seq;
  el('l-hash').textContent     = (ledger.cum_hash || '').slice(0, 24) + '…';
  el('l-chain').textContent    = ledger.chain_status;
  el('l-chain').className      = `ls-value ${ledger.chain_status === 'INTACT' ? 'intact' : 'broken'}`;
  el('l-replay').textContent   = ledger.replay_status;
  el('l-verdict').textContent  = ledger.last_reducer_verdict;
  el('l-verdict').className    = `ls-value ${ledger.last_reducer_verdict === 'PASS' ? 'pass' : ''}`;

  el('ledger-entries').innerHTML = (ledger.recent || []).map(e => {
    const halStr = e.hal ? `<span class="le-hal pass">HAL:${e.hal}</span>` : '';
    return `<div class="le-entry">
  <span class="le-seq">seq ${e.seq}</span>
  <span class="le-type">${e.type} · ${e.schema}</span>
  ${halStr}
</div>`;
  }).join('');
}

// ── avatar ────────────────────────────────────────────────────────────────

function renderAvatar() {
  el('avatar-block').innerHTML = `
<div class="helen-avatar">
  <svg width="52" height="60" viewBox="0 0 52 60" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- hair — copper -->
    <ellipse cx="26" cy="18" rx="20" ry="22" fill="#7a3a10" opacity=".9"/>
    <ellipse cx="26" cy="14" rx="16" ry="17" fill="#b87333" opacity=".8"/>
    <!-- face -->
    <ellipse cx="26" cy="28" rx="14" ry="17" fill="#d4b89a"/>
    <!-- eyes — blue-grey -->
    <ellipse cx="20" cy="26" rx="2.5" ry="2" fill="#5a7a9a"/>
    <ellipse cx="32" cy="26" rx="2.5" ry="2" fill="#5a7a9a"/>
    <!-- freckles -->
    <circle cx="22" cy="31" r=".7" fill="#a07050" opacity=".6"/>
    <circle cx="25" cy="30" r=".7" fill="#a07050" opacity=".6"/>
    <circle cx="30" cy="31" r=".7" fill="#a07050" opacity=".6"/>
    <!-- observer ring -->
    <circle cx="26" cy="28" r="21" stroke="#c8a84b" stroke-width=".5" stroke-dasharray="2 3" fill="none" opacity=".4"/>
  </svg>
</div>
<div class="avatar-label">HELEN</div>
<div class="avatar-caption">HELEN observes · REDUCER decides</div>`;
}

// ── main render ───────────────────────────────────────────────────────────

function render(state) {
  renderBanner(state);
  renderLayers(state.layers || []);
  renderEpoch3(state.epoch3 || { phases: [], claim_graph: [], seed: '' });
  renderGovernance(state.governance || { pipeline: [], obligations: [], receipts: [], verdict_readiness: {} });
  renderLedger(state.ledger || {});
  renderAvatar();
}

// ── boot ──────────────────────────────────────────────────────────────────

async function boot() {
  const state = await loadState();
  if (!state) {
    el('loading').textContent = 'ERROR — could not load state';
    return;
  }
  el('loading').classList.add('loading-hidden');
  render(state);
}

async function refresh() {
  const state = await loadState();
  if (state) render(state);
}

boot();
setInterval(refresh, REFRESH_MS);

/**
 * HELEN OS v2 — Focus Mode Prototype
 * authority: NON_SOVEREIGN · canon: NO_SHIP · lifecycle: EXPERIMENTAL_UI_PROTOTYPE
 *
 * No backend. No ledger mutation. No kernel contact.
 * Receipts are local in-memory only.
 */

'use strict';

// ── State ─────────────────────────────────────────────────────────────────────

const state = {
  mode: 'focus',        // 'focus' | 'witness'
  receipts: [],
  micActive: false,
  ledgerOpen: false,
  confirmPending: null, // { text, idx }
  seq: 0,
};

// ── Intent + Suggestions ──────────────────────────────────────────────────────

const INTENT = 'Understand the nature of consciousness';

const SUGGESTION_SETS = [
  [
    {
      icon: 'book',
      title: 'Explore related knowledge',
      desc: 'Open the Codex and deepen insight.',
      color: '#4f46e5',
    },
    {
      icon: 'graph',
      title: 'Map connections',
      desc: 'Visualize relationships and patterns.',
      color: '#d97706',
    },
    {
      icon: 'brain',
      title: 'Run a simulation',
      desc: 'Test hypotheses in the lab.',
      color: '#0891b2',
    },
  ],
  [
    {
      icon: 'search',
      title: 'Survey philosophical frameworks',
      desc: 'Chalmers, Dennett, Nagel — map their claims.',
      color: '#7c3aed',
    },
    {
      icon: 'data',
      title: 'Review neuroscience models',
      desc: 'Identify measurable correlates of consciousness.',
      color: '#059669',
    },
    {
      icon: 'draft',
      title: 'Draft a research brief',
      desc: 'Frameworks, open questions, working hypothesis.',
      color: '#c084fc',
    },
  ],
  [
    {
      icon: 'temple',
      title: 'Reflect in Temple Mode',
      desc: 'Journal freely — no governance, no claim.',
      color: '#a855f7',
    },
    {
      icon: 'oracle',
      title: 'Ask the Oracle',
      desc: 'Symbolic inquiry — hexagram classifier.',
      color: '#f59e0b',
    },
    {
      icon: 'receipt',
      title: 'Build a receipt',
      desc: 'Commit a confirmed finding to the ledger.',
      color: '#22c55e',
    },
  ],
];

let suggestionSetIdx = 0;

function getIcon(key) {
  const icons = {
    book: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
    graph: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
    brain: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9.5 2A2.5 2.5 0 0112 4.5v15a2.5 2.5 0 01-4.96-.46 2.5 2.5 0 01-1.07-4.81A3 3 0 015 10a3 3 0 013-3 2.5 2.5 0 011.5-5z"/><path d="M14.5 2A2.5 2.5 0 0012 4.5v15a2.5 2.5 0 004.96-.46 2.5 2.5 0 001.07-4.81A3 3 0 0019 10a3 3 0 00-3-3 2.5 2.5 0 00-1.5-5z"/></svg>',
    search: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    data: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    draft: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    temple: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    oracle: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    receipt: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 6 9 17 4 12"/></svg>',
  };
  return icons[key] || icons.book;
}

function renderSuggestions() {
  const container = document.getElementById('action-cards');
  const set = SUGGESTION_SETS[suggestionSetIdx];
  container.innerHTML = '';
  set.forEach((s, idx) => {
    const card = document.createElement('button');
    card.className = 'action-card';
    card.onclick = () => openConfirm(s.title, idx);
    card.innerHTML = `
      <div class="action-card-icon" style="background: ${s.color}22; color: ${s.color}">
        ${getIcon(s.icon)}
      </div>
      <div class="action-card-body">
        <div class="action-card-title">${s.title}</div>
        <div class="action-card-desc">${s.desc}</div>
      </div>
      <div class="action-card-arrow">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
    `;
    container.appendChild(card);
  });
}

function shuffleSuggestions() {
  suggestionSetIdx = (suggestionSetIdx + 1) % SUGGESTION_SETS.length;
  renderSuggestions();
  // Flash the panel
  const panel = document.querySelector('.suggests-panel');
  panel.style.opacity = '0.5';
  setTimeout(() => { panel.style.opacity = '1'; panel.style.transition = 'opacity 0.3s'; }, 50);
}

function closeSuggests() {
  document.getElementById('panel-right').style.opacity = '0';
  document.getElementById('panel-right').style.pointerEvents = 'none';
  setTimeout(() => {
    document.getElementById('panel-right').style.opacity = '1';
    document.getElementById('panel-right').style.pointerEvents = '';
  }, 3000);
}

// ── Mode toggle ───────────────────────────────────────────────────────────────

function setMode(mode) {
  state.mode = mode;
  document.getElementById('witness-overlay').classList.toggle('open', mode === 'witness');
  updateWitnessPanel();
}

function updateWitnessPanel() {
  document.getElementById('w-ledger-count').textContent = `${state.receipts.length} entries (in-memory)`;
  const chain = document.getElementById('witness-chain');
  if (state.receipts.length === 0) {
    chain.innerHTML = '<div class="chain-empty">No receipts in chain.</div>';
  } else {
    chain.innerHTML = state.receipts.map(r => `
      <div class="ledger-entry">
        <div class="le-seq">seq=${r.seq} · ${r.time}</div>
        <div class="le-action">${r.action}</div>
        <div class="le-meta">NON_SOVEREIGN · in-memory</div>
      </div>
    `).join('');
  }
}

// ── Ledger ────────────────────────────────────────────────────────────────────

function toggleLedger() {
  state.ledgerOpen = !state.ledgerOpen;
  document.getElementById('ledger-dropdown').classList.toggle('open', state.ledgerOpen);
  document.getElementById('ledger-chevron').classList.toggle('open', state.ledgerOpen);
  renderLedgerEntries();
}

function renderLedgerEntries() {
  const container = document.getElementById('ledger-entries');
  if (state.receipts.length === 0) {
    container.innerHTML = '<div class="ledger-empty">No entries. Confirm an action to append a receipt.</div>';
    return;
  }
  container.innerHTML = state.receipts.slice().reverse().map(r => `
    <div class="ledger-entry">
      <div class="le-seq">seq=${r.seq} · ${r.time} · ${r.hash}</div>
      <div class="le-action">${r.action}</div>
      <div class="le-meta">NON_SOVEREIGN · prototype · no mutation</div>
    </div>
  `).join('');
}

function appendReceipt(action) {
  state.seq++;
  const now = new Date();
  const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const hash = 'sim_' + Math.random().toString(36).substr(2, 8);
  const receipt = { seq: state.seq, action, time, hash };
  state.receipts.push(receipt);

  // Update receipt pill
  document.getElementById('receipt-status').textContent = action.substring(0, 28) + (action.length > 28 ? '…' : '');
  document.getElementById('receipt-status').style.color = '#22c55e';
  document.getElementById('receipt-time').textContent = time;

  // Flash
  const flash = document.getElementById('receipt-flash');
  flash.textContent = `◆ Receipt appended · seq=${state.seq}`;
  flash.classList.add('show');
  setTimeout(() => flash.classList.remove('show'), 2200);

  // Pulse orb
  const orb = document.querySelector('.orb-svg');
  orb.style.filter = 'drop-shadow(0 0 60px rgba(192,132,252,0.9)) drop-shadow(0 0 100px rgba(124,58,237,0.4))';
  setTimeout(() => { orb.style.filter = ''; }, 800);

  if (state.ledgerOpen) renderLedgerEntries();
  updateWitnessPanel();
}

// ── Confirmation ──────────────────────────────────────────────────────────────

function openConfirm(text, idx) {
  state.confirmPending = { text, idx };
  document.getElementById('confirm-action-text').textContent = text;
  document.getElementById('confirm-backdrop').classList.add('open');
  document.getElementById('confirmation-sheet').classList.add('open');
}

function cancelConfirm() {
  state.confirmPending = null;
  document.getElementById('confirm-backdrop').classList.remove('open');
  document.getElementById('confirmation-sheet').classList.remove('open');
}

function confirmAction() {
  if (!state.confirmPending) return;
  const action = state.confirmPending.text;
  cancelConfirm();
  appendReceipt(action);
}

// ── Module panels ─────────────────────────────────────────────────────────────

const MODULE_CONTENT = {
  amp: {
    title: 'HELEN AMP — Autonomous Model Processor',
    body: `
      <div style="display:flex; flex-direction:column; gap:14px;">
        <div style="padding:12px 14px; background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.2); border-radius:12px;">
          <div style="font-size:10px; font-weight:700; letter-spacing:0.12em; color:#c084fc; margin-bottom:6px;">ACTIVE PROVIDER</div>
          <div style="font-size:14px; color:#f0e8ff;">ollama · gemma3:1b</div>
          <div style="font-size:11px; color:#8b7aaa; margin-top:2px;">localhost:11434 · ~1ms latency</div>
        </div>
        <div style="padding:12px 14px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:12px;">
          <div style="font-size:11px; color:#8b7aaa; margin-bottom:4px;">Provider chain</div>
          <div style="font-size:12px; color:#f0e8ff;">ollama → gemini → heuristic</div>
        </div>
        <div style="font-size:11px; color:#504870; line-height:1.6;">
          AMP routes intent to the best available provider.<br>
          Always returns 3 concrete proposals.<br>
          Authority: NON_SOVEREIGN
        </div>
      </div>
    `,
  },
  files: {
    title: 'Files',
    body: `
      <div style="color:#8b7aaa; font-size:13px;">
        No files loaded in prototype session.<br><br>
        In live mode, this panel surfaces documents, artifacts, claim packets, and evidence windows within scope of the current intent.
      </div>
    `,
  },
  internet: {
    title: 'Internet',
    body: `
      <div style="color:#8b7aaa; font-size:13px;">
        No network access in prototype mode.<br><br>
        In live mode, HELEN uses bounded web retrieval to gather sources relevant to the current intent. Results are tagged with provenance and held as non-admitted evidence until confirmed.
      </div>
    `,
  },
  notes: {
    title: 'Notes',
    body: `
      <div style="display:flex; flex-direction:column; gap:10px;">
        ${['Consciousness notes — draft', 'Research questions', 'Session log 2026-04-27'].map(n => `
          <div style="padding:10px 12px; background:rgba(254,240,138,0.05); border:1px solid rgba(254,240,138,0.12); border-radius:10px; cursor:pointer; font-size:13px; color:#f0e8ff;">
            📄 ${n}
          </div>
        `).join('')}
        <div style="font-size:11px; color:#504870; margin-top:4px;">NON_SOVEREIGN · prototype · no write</div>
      </div>
    `,
  },
  calendar: {
    title: 'Calendar',
    body: `
      <div style="display:flex; flex-direction:column; gap:10px;">
        <div style="font-size:13px; color:#8b7aaa; margin-bottom:4px;">Mon May 18</div>
        ${['09:00 — Research session', '14:00 — Review findings', '17:00 — Knowledge compile'].map(e => `
          <div style="padding:10px 12px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:10px; font-size:12px; color:#f0e8ff;">
            ${e}
          </div>
        `).join('')}
      </div>
    `,
  },
  mail: {
    title: 'Mail — 2 unread',
    body: `
      <div style="display:flex; flex-direction:column; gap:10px;">
        ${[
          { from: 'Research Digest', sub: 'Consciousness studies — weekly' },
          { from: 'HELEN OS', sub: 'Your session receipt is ready' },
        ].map(m => `
          <div style="padding:12px 14px; background:rgba(255,255,255,0.03); border:1px solid rgba(59,130,246,0.15); border-radius:10px; cursor:pointer;">
            <div style="font-size:12px; font-weight:600; color:#f0e8ff; margin-bottom:3px;">${m.from}</div>
            <div style="font-size:11px; color:#8b7aaa;">${m.sub}</div>
          </div>
        `).join('')}
        <div style="font-size:11px; color:#504870;">NON_SOVEREIGN · no send in prototype</div>
      </div>
    `,
  },
  oracle: {
    title: 'Oracle — Hexagram Classifier',
    body: `
      <div style="display:flex; flex-direction:column; gap:14px;">
        <div style="padding:12px 14px; background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.2); border-radius:12px; text-align:center;">
          <div style="font-size:32px; margin-bottom:6px;">䷯</div>
          <div style="font-size:13px; color:#c084fc; font-weight:500;">Hexagram 48 — Jǐng</div>
          <div style="font-size:11px; color:#8b7aaa; margin-top:2px;">The Well · constant nourishment</div>
        </div>
        <div style="padding:12px 14px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:12px;">
          <div style="font-size:11px; color:#8b7aaa; margin-bottom:6px;">HELEN Mode mapping</div>
          <div style="font-size:12px; color:#f0e8ff;">Upper: Water (☵) → WITNESS</div>
          <div style="font-size:12px; color:#f0e8ff; margin-top:3px;">Lower: Wind (☴) → ORACLE</div>
          <div style="font-size:11px; color:#f59e0b; margin-top:6px;">⚡ Tension — requires_second_witness: true</div>
        </div>
        <div style="font-size:11px; color:#504870; line-height:1.6;">
          Clean the well before drawing water.<br>
          Do not decorate the source — purify it.<br>
          Authority: NON_SOVEREIGN
        </div>
      </div>
    `,
  },
  settings: {
    title: 'Settings',
    body: `
      <div style="display:flex; flex-direction:column; gap:12px;">
        ${[
          { label: 'Provider', val: 'ollama (gemma3:1b)' },
          { label: 'Mode', val: 'Focus Mode' },
          { label: 'Receipt', val: 'in-memory (prototype)' },
          { label: 'Authority', val: 'NON_SOVEREIGN' },
          { label: 'Canon', val: 'NO_SHIP' },
        ].map(s => `
          <div style="display:flex; justify-content:space-between; padding:10px 14px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:10px;">
            <span style="font-size:12px; color:#8b7aaa;">${s.label}</span>
            <span style="font-size:12px; color:#f0e8ff;">${s.val}</span>
          </div>
        `).join('')}
      </div>
    `,
  },
  new: {
    title: 'New Intent',
    body: `
      <div style="display:flex; flex-direction:column; gap:14px;">
        <input type="text" id="new-intent-input" placeholder="State your intent…"
          style="
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(124,58,237,0.3);
            border-radius: 12px;
            padding: 14px 16px;
            font-size: 15px;
            color: #f0e8ff;
            font-family: -apple-system, system-ui, sans-serif;
            outline: none;
            width: 100%;
          "
          onkeydown="if(event.key==='Enter') setNewIntent()"
        />
        <button onclick="setNewIntent()"
          style="
            background: linear-gradient(135deg, #5b21b6, #7c3aed);
            border: none; border-radius: 12px;
            color: white; font-size: 14px; font-weight: 600;
            padding: 13px; cursor: pointer; font-family: inherit;
          "
        >Set Intent ◆</button>
        <div style="font-size:11px; color:#504870;">Intent is non-sovereign. No ledger write until you confirm an action.</div>
      </div>
    `,
  },
};

function openModule(name) {
  const content = MODULE_CONTENT[name] || { title: name, body: '<p style="color:#8b7aaa">No content yet.</p>' };
  document.getElementById('module-panel-title').textContent = content.title;
  document.getElementById('module-panel-body').innerHTML = content.body;
  document.getElementById('module-backdrop').classList.add('open');
  document.getElementById('module-panel').classList.add('open');
}

function closeModule() {
  document.getElementById('module-backdrop').classList.remove('open');
  document.getElementById('module-panel').classList.remove('open');
}

function setNewIntent() {
  const input = document.getElementById('new-intent-input');
  if (!input || !input.value.trim()) return;
  document.getElementById('intent-text').textContent = input.value.trim();
  document.querySelector('.clarity-fill').style.width = '20%';
  closeModule();
}

// ── Mic ───────────────────────────────────────────────────────────────────────

function toggleMic() {
  state.micActive = !state.micActive;
  document.getElementById('mic-btn').classList.toggle('active', state.micActive);
  document.getElementById('voice-waveform').classList.toggle('active', state.micActive);
  if (state.micActive) {
    animateWaveform();
  }
}

function animateWaveform() {
  if (!state.micActive) return;
  const bars = document.querySelectorAll('.wv-bar');
  bars.forEach(bar => {
    const h = Math.floor(Math.random() * 24) + 4;
    bar.style.height = h + 'px';
  });
  requestAnimationFrame(() => setTimeout(animateWaveform, 120));
}

// ── Add mode toggle hint to page ──────────────────────────────────────────────

function addModeToggle() {
  const hint = document.createElement('div');
  hint.className = 'mode-toggle-hint';
  hint.innerHTML = `
    <button class="mode-tab active" id="tab-focus" onclick="switchTab('focus')">FOCUS</button>
    <button class="mode-tab" id="tab-witness" onclick="switchTab('witness')">WITNESS</button>
  `;
  document.body.appendChild(hint);
}

function switchTab(mode) {
  document.getElementById('tab-focus').classList.toggle('active', mode === 'focus');
  document.getElementById('tab-witness').classList.toggle('active', mode === 'witness');
  setMode(mode);
}

// ── Close ledger on outside click ─────────────────────────────────────────────

document.addEventListener('click', function(e) {
  if (state.ledgerOpen) {
    const dropdown = document.getElementById('ledger-dropdown');
    const pill = document.getElementById('receipt-pill');
    const btn = document.getElementById('ledger-btn');
    if (!dropdown.contains(e.target) && !pill.contains(e.target) && !btn.contains(e.target)) {
      state.ledgerOpen = false;
      dropdown.classList.remove('open');
      document.getElementById('ledger-chevron').classList.remove('open');
    }
  }
});

// ── Keyboard shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    cancelConfirm();
    closeModule();
    if (state.mode === 'witness') switchTab('focus');
  }
  if (e.key === 'w' && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    switchTab(state.mode === 'focus' ? 'witness' : 'focus');
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  renderSuggestions();
  addModeToggle();

  // Subtle waveform idle animation
  setInterval(() => {
    if (!state.micActive) {
      const bars = document.querySelectorAll('.wv-bar');
      bars.forEach(bar => {
        const h = Math.floor(Math.random() * 10) + 4;
        bar.style.height = h + 'px';
        bar.style.transition = 'height 0.8s ease';
      });
    }
  }, 900);

  console.log(
    '%cHELEN OS v2 — Focus Mode Prototype\n' +
    '%cauthority: NON_SOVEREIGN · canon: NO_SHIP\n' +
    'No ledger mutation. No kernel contact. Local in-memory only.',
    'font-size:14px; font-weight:bold; color:#c084fc',
    'font-size:11px; color:#8b7aaa'
  );
});

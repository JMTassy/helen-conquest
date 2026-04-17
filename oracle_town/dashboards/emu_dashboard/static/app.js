async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return await r.json();
}

function setCode(id, obj) {
  document.querySelector(id).innerHTML = `<code>${escapeHtml(JSON.stringify(obj, null, 2))}</code>`;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[c]));
}

function chip(text) {
  const span = document.createElement("span");
  span.className = "chip";
  span.textContent = text;
  return span;
}

function summarizeTri(tri) {
  const out = [];
  if (!tri) return out;
  if (tri.verdict) out.push(`verdict:${tri.verdict}`);
  const checks = tri.checks || tri.results || {};
  for (const [k, v] of Object.entries(checks)) {
    if (typeof v === "boolean") out.push(`${k}:${v ? "✓" : "✗"}`);
    else if (v && typeof v === "object" && "pass" in v) out.push(`${k}:${v.pass ? "✓" : "✗"}`);
  }
  return out.slice(0, 10);
}

function summarizeReceipt(rcpt) {
  const out = [];
  if (!rcpt) return out;
  if (rcpt.decision) out.push(`decision:${rcpt.decision}`);
  if (rcpt.receipt_id) out.push(`id:${rcpt.receipt_id}`);
  if (rcpt.policy_pack_hash) out.push(`policy:${rcpt.policy_pack_hash.slice(0, 16)}…`);
  if (rcpt.signature) out.push(`sig:${String(rcpt.signature).slice(0, 16)}…`);
  return out.slice(0, 8);
}

function renderChips(el, items) {
  el.innerHTML = "";
  items.forEach(t => el.appendChild(chip(t)));
}

async function loadStatus() {
  const s = await getJSON("/api/status");
  document.getElementById("statusChip").textContent = `status:${s.ok ? "ok" : "bad"}`;
  document.getElementById("pathsChip").textContent = `ledger:${s.ledger_root} tmp:${s.tmp_root}`;
}

async function loadLatest() {
  const latest = await getJSON("/api/latest");
  document.getElementById("latestMeta").textContent =
    latest.available ? `source:${latest.source} updated:${latest.updated_at}` : "no latest run found";

  document.getElementById("oneBet").textContent = latest.one_bet || "—";

  const tri = latest.tri_verdict || {};
  renderChips(document.getElementById("triSummary"), summarizeTri(tri));
  setCode("#triRaw", tri);

  const rcpt = latest.receipt || {};
  renderChips(document.getElementById("receiptSummary"), summarizeReceipt(rcpt));
  setCode("#receiptRaw", rcpt);

  setCode("#briefRaw", latest.brief || latest.insights || latest.brf || {});
}

function runItem(r) {
  const div = document.createElement("div");
  div.className = "item";
  div.innerHTML = `
    <div style="font-weight:700;">${escapeHtml(r.claim_id)}</div>
    <div class="muted">${escapeHtml(r.path)} — ${escapeHtml(r.mtime)}</div>
  `;
  div.onclick = async () => {
    const data = await getJSON(`/api/run/${encodeURIComponent(r.claim_id)}`);
    const meta = document.getElementById("selectedMeta");
    meta.innerHTML = "";
    meta.appendChild(chip(`claim_id:${data.claim_id}`));
    meta.appendChild(chip(`has_claim:${!!data.claim}`));
    meta.appendChild(chip(`has_tri:${!!data.tri_verdict}`));
    meta.appendChild(chip(`has_receipt:${!!data.receipt}`));
    meta.appendChild(chip(`dir:${data.path}`));
    setCode("#selectedRaw", data);
  };
  return div;
}

async function loadRuns() {
  const runs = await getJSON("/api/runs?limit=50");
  const list = document.getElementById("runsList");
  list.innerHTML = "";
  (runs.items || []).forEach(r => list.appendChild(runItem(r)));
}

async function main() {
  await loadStatus();
  await loadLatest();
  await loadRuns();

  // Optional live refresh (poll)
  setInterval(async () => {
    try {
      await loadLatest();
      await loadRuns();
    } catch (e) {
      // keep quiet; read-only dashboard should degrade gracefully
      console.warn(e);
    }
  }, 2500);
}

main().catch(console.error);

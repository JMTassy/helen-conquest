// HELEN UI — Receipt Console Client

async function refresh() {
  try {
    const r = await fetch("/api/state");
    const j = await r.json();

    // Update events
    const eventsBlock = document.getElementById("events");
    eventsBlock.textContent =
      j.eventsTail && j.eventsTail.length > 0
        ? j.eventsTail.join("\n")
        : "(no events yet)";

    // Update wisdom
    const wisdomBlock = document.getElementById("wisdom");
    wisdomBlock.textContent =
      j.wisdomTail && j.wisdomTail.length > 0
        ? j.wisdomTail.join("\n")
        : "(no wisdom yet)";

    // Update summary (L2 receipt)
    const summaryBlock = document.getElementById("summary");
    summaryBlock.textContent = j.summary
      ? JSON.stringify(j.summary, null, 2)
      : "(no summary yet — run not sealed)";

    // Update timestamp
    const now = new Date().toLocaleTimeString();
    document.getElementById("last-refresh").textContent = now;
  } catch (err) {
    console.error("Refresh failed:", err);
  }
}

// Seal run
document.getElementById("seal").onclick = async () => {
  const btn = document.getElementById("seal");
  btn.disabled = true;
  btn.textContent = "Sealing…";
  try {
    const r = await fetch("/api/seal", { method: "POST" });
    const j = await r.json();
    if (j.code === 0) {
      btn.textContent = "✅ Sealed";
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Seal run";
      }, 1500);
    } else {
      btn.textContent = "❌ Seal failed";
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Seal run";
      }, 2000);
    }
  } catch (err) {
    console.error("Seal failed:", err);
    btn.disabled = false;
    btn.textContent = "Seal run";
  }
  await refresh();
};

// Run K-τ lint
document.getElementById("ktau").onclick = async () => {
  const btn = document.getElementById("ktau");
  btn.disabled = true;
  btn.textContent = "Running K-τ…";
  try {
    const r = await fetch("/api/k_tau", { method: "POST" });
    const j = await r.json();
    if (j.code === 0) {
      btn.textContent = "✅ K-τ pass";
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Run K-τ";
      }, 1500);
    } else {
      btn.textContent = "⚠️  K-τ issues";
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Run K-τ";
      }, 2000);
    }
  } catch (err) {
    console.error("K-τ failed:", err);
    btn.disabled = false;
    btn.textContent = "Run K-τ";
  }
  await refresh();
};

// Manual refresh
document.getElementById("refresh").onclick = refresh;

// Add wisdom
document.getElementById("add").onclick = async () => {
  const lesson = document.getElementById("lesson").value.trim();
  const evidence = document.getElementById("evidence").value.trim();
  const feedback = document.getElementById("add-feedback");

  if (!lesson) {
    feedback.textContent = "❌ Lesson required";
    return;
  }

  const btn = document.getElementById("add");
  btn.disabled = true;
  btn.textContent = "Appending…";
  feedback.textContent = "";

  try {
    const r = await fetch("/api/add_wisdom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lesson, evidence }),
    });
    const j = await r.json();

    if (r.ok && j.code === 0) {
      feedback.textContent = "✅ Wisdom appended";
      document.getElementById("lesson").value = "";
      document.getElementById("evidence").value = "";
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Append to wisdom";
        feedback.textContent = "";
      }, 1500);
    } else {
      feedback.textContent = "❌ Failed to append wisdom";
      btn.disabled = false;
      btn.textContent = "Append to wisdom";
    }
  } catch (err) {
    console.error("Add wisdom failed:", err);
    feedback.textContent = "❌ Error appending wisdom";
    btn.disabled = false;
    btn.textContent = "Append to wisdom";
  }

  await refresh();
};

// Auto-refresh every 2 seconds
setInterval(refresh, 2000);

// Initial load
refresh();

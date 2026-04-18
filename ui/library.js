// HELEN Library — Knowledge Base Browser

const wisdomList = document.getElementById('wisdom-list');
const factsList = document.getElementById('facts-list');
const searchInput = document.getElementById('search-input');
const tabBtns = document.querySelectorAll('.tab-btn');

let allWisdom = [];
let allFacts = {};

// Load all wisdom on init
async function loadWisdom() {
  try {
    const r = await fetch('/api/library/wisdom');
    allWisdom = await r.json();
    renderWisdom(allWisdom);
  } catch (err) {
    console.error('Failed to load wisdom:', err);
    wisdomList.innerHTML = '<p class="loading">Error loading wisdom</p>';
  }
}

// Load all facts
async function loadFacts() {
  try {
    const r = await fetch('/api/library/facts');
    allFacts = await r.json();
    renderFacts(allFacts);
  } catch (err) {
    console.error('Failed to load facts:', err);
    factsList.innerHTML = '<p class="loading">Error loading facts</p>';
  }
}

function renderWisdom(entries) {
  if (entries.length === 0) {
    wisdomList.innerHTML = '<p class="loading">No wisdom entries found</p>';
    return;
  }

  wisdomList.innerHTML = entries.map(entry => `
    <div class="wisdom-entry ${entry.kind || 'lesson'}">
      <div class="entry-header">
        <span class="entry-kind ${entry.kind || 'lesson'}">${(entry.kind || 'lesson').toUpperCase()}</span>
        <span class="entry-date">${new Date(entry.t).toLocaleDateString()}</span>
      </div>
      <div class="entry-lesson">${entry.lesson}</div>
      ${entry.evidence ? `<div class="entry-evidence"><strong>Evidence:</strong> ${entry.evidence}</div>` : ''}
    </div>
  `).join('');
}

function renderFacts(facts) {
  const entries = Object.entries(facts);
  if (entries.length === 0) {
    factsList.innerHTML = '<p class="loading">No facts recorded</p>';
    return;
  }

  factsList.innerHTML = entries.map(([key, value]) => `
    <div class="fact-card">
      <div class="fact-key">${key}</div>
      <div class="fact-value">${String(value)}</div>
    </div>
  `).join('');
}

// Search functionality
searchInput.addEventListener('input', async (e) => {
  const query = e.target.value.trim();
  if (!query) {
    renderWisdom(allWisdom);
    return;
  }

  try {
    const r = await fetch(`/api/library/search?q=${encodeURIComponent(query)}`);
    const results = await r.json();
    renderWisdom(results);
  } catch (err) {
    console.error('Search failed:', err);
  }
});

// Tab switching
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));

    btn.classList.add('active');
    const tabId = btn.dataset.tab + '-tab';
    document.getElementById(tabId).classList.add('active');

    if (btn.dataset.tab === 'facts' && Object.keys(allFacts).length === 0) {
      loadFacts();
    }
  });
});

// Initial load
loadWisdom();

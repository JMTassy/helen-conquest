/**
 * UI Controller — Updates sidebar with live state from server
 *
 * Polls /api/ui/* endpoints and updates sidebar statistics,
 * claims list, receipts list, and gate status
 */

class UIController {
  constructor() {
    this.pollInterval = 2000; // 2 seconds
    this.polling = false;
  }

  start() {
    /**
     * Start polling loop and initial fetch
     */
    this.polling = true;
    this.fetchAndUpdateUI();

    // Set up polling interval
    setInterval(() => {
      if (this.polling) {
        this.fetchAndUpdateUI();
      }
    }, this.pollInterval);
  }

  stop() {
    this.polling = false;
  }

  async fetchAndUpdateUI() {
    try {
      // Fetch state from server
      const response = await fetch('/api/ui/claim-graph-state');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      // Update header stats
      this.updateStats(data);

      // Update claims list
      this.updateClaimsList(data.nodes);

      // Update gates status
      this.updateGatesStatus(data.gates);

      // Update last-updated timestamp
      this.updateTimestamp();

      // Update status indicator
      this.setStatusIndicator(true);
    } catch (error) {
      console.error('Failed to fetch UI state:', error);
      this.setStatusIndicator(false);
    }
  }

  updateStats(data) {
    /**
     * Update header statistics
     */
    document.getElementById('phase-value').textContent = data.phase || 'UNKNOWN';
    document.getElementById('claims-count').textContent = (data.nodes || []).length;
    document.getElementById('receipts-count').textContent = 'N/A';
  }

  updateClaimsList(nodes) {
    /**
     * Render claims in sidebar
     * Group by phase, show node kind and admissibility
     */

    const listElement = document.getElementById('claims-list');

    if (!nodes || nodes.length === 0) {
      listElement.innerHTML =
        '<div style="color: #aaaaaa; font-size: 11px">No active claims</div>';
      return;
    }

    // Group by phase
    const byPhase = {};
    nodes.forEach((node) => {
      const phase = node.phase || 'UNKNOWN';
      if (!byPhase[phase]) byPhase[phase] = [];
      byPhase[phase].push(node);
    });

    let html = '';
    Object.entries(byPhase).forEach(([phase, phaseNodes]) => {
      html += `<div style="color: #d4af37; font-size: 10px; margin-top: 8px; margin-bottom: 5px">${phase}</div>`;
      phaseNodes.forEach((node) => {
        const kindEmoji = this.getEmojiForKind(node.kind);
        const admissibilityColor =
          node.admissibility === 'QUARANTINED' ? '#ff6b6b' : '#16c784';

        html += `
          <div class="claim-item" title="${node.id}">
            <div class="claim-id">${kindEmoji} ${node.id.substring(0, 15)}</div>
            <div class="claim-kind">
              ${node.kind} · <span style="color: ${admissibilityColor}">${node.admissibility}</span>
            </div>
          </div>
        `;
      });
    });

    listElement.innerHTML = html;
  }

  updateGatesStatus(gates) {
    /**
     * Render gate status in sidebar
     * Show each gate name and pass/fail status
     */

    const statusElement = document.getElementById('gates-status');

    if (!gates || Object.keys(gates).length === 0) {
      statusElement.innerHTML =
        '<div style="color: #aaaaaa; font-size: 11px">No gate status available</div>';
      return;
    }

    let html = '';
    Object.entries(gates).forEach(([gate, status]) => {
      const color = status === 'PASS' ? '#16c784' : '#ff6b6b';
      const emoji = status === 'PASS' ? '✓' : '✗';

      html += `
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 11px">
          <span>${gate}</span>
          <span style="color: ${color}; font-weight: bold">${emoji} ${status}</span>
        </div>
      `;
    });

    statusElement.innerHTML = html;
  }

  updateTimestamp() {
    /**
     * Update "last updated" timestamp
     */
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    document.getElementById('last-updated').textContent = time;
  }

  setStatusIndicator(connected) {
    /**
     * Update status indicator (green dot + text)
     */
    const dot = document.querySelector('.status-dot');
    const text = document.getElementById('status-text');

    if (connected) {
      dot.style.background = '#16c784';
      text.textContent = 'Connected';
      text.style.color = '#16c784';
    } else {
      dot.style.background = '#ff6b6b';
      text.textContent = 'Disconnected';
      text.style.color = '#ff6b6b';
    }
  }

  getEmojiForKind(kind) {
    /**
     * Map node kind to emoji
     */
    const emojiMap = {
      claim: '🔵',
      evidence: '🟡',
      artifact: '🟣',
      receipt: '🟢',
      wild_text: '🔴'
    };
    return emojiMap[kind] || '❓';
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { UIController };
}

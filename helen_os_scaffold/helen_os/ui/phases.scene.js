/**
 * HELEN OS Phases Scene — Pixel-Art Governance Visualization
 *
 * Maps invisible governance state into visual metaphor:
 * - 5 zone backgrounds (EXPLORATION → TENSION → DRAFTING → EDITORIAL → TERMINATION)
 * - Claims move through zones as colored sprites
 * - Receipts appear as floating badges (fade after 5s)
 * - Polls server for state updates every 2s
 *
 * Part of Move 4: HELEN-Office-UI (Star-Office patterns + pixel-art aesthetics)
 * Integrates with /api/ui/claim-graph-state and /api/ui/receipts endpoints
 */

class PhasesScene extends Phaser.Scene {
  constructor() {
    super({ key: 'PhasesScene' });
    this.claims = []; // Active claims (nodes)
    this.receipts = []; // Recent receipts (badges)
    this.currentPhase = 'EXPLORATION';
    this.theme = 'pixel-cozy'; // Default theme
  }

  preload() {
    // Load theme assets
    this.loadThemeAssets(this.theme);
  }

  loadThemeAssets(themeName) {
    /**
     * Theme asset structure:
     * /assets/themes/{themeName}/
     *   ├── backgrounds/
     *   │   ├── exploration.png
     *   │   ├── tension.png
     *   │   ├── drafting.png
     *   │   ├── editorial.png
     *   │   └── termination.png
     *   ├── sprites/
     *   │   ├── claim.png (blue)
     *   │   ├── evidence.png (yellow)
     *   │   ├── artifact.png (purple)
     *   │   ├── receipt.png (green)
     *   │   └── wild_text.png (red, quarantined)
     *   └── badges/
     *       ├── receipt_pass.png
     *       ├── receipt_fail.png
     *       └── receipt_pending.png
     */

    const basePath = `../assets/themes/${themeName}`;

    // Preload background images
    const phases = [
      'exploration',
      'tension',
      'drafting',
      'editorial',
      'termination'
    ];
    phases.forEach((phase) => {
      this.load.image(
        `bg-${phase}`,
        `${basePath}/backgrounds/${phase}.png`
      );
    });

    // Preload sprite sheets
    const spriteTypes = ['claim', 'evidence', 'artifact', 'receipt', 'wild_text'];
    spriteTypes.forEach((type) => {
      this.load.image(
        `sprite-${type}`,
        `${basePath}/sprites/${type}.png`
      );
    });

    // Preload badge images
    const badgeTypes = ['receipt_pass', 'receipt_fail', 'receipt_pending'];
    badgeTypes.forEach((badge) => {
      this.load.image(
        `badge-${badge}`,
        `${basePath}/badges/${badge}.png`
      );
    });
  }

  create() {
    // Set up scene
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Draw 5 zones (horizontal strip layout)
    this.drawZones(width, height);

    // Set up polling loop (fetch state every 2 seconds)
    this.time.addEvent({
      delay: 2000,
      callback: this.fetchStateFromServer,
      callbackScope: this,
      loop: true
    });

    // Fetch initial state
    this.fetchStateFromServer();

    // Debug text
    this.debugText = this.add.text(10, 10, '', {
      font: '12px monospace',
      fill: '#ffffff'
    });
  }

  drawZones(width, height) {
    /**
     * Layout: 5 zones side-by-side
     * Each zone is (width/5) wide × full height tall
     *
     * Zone positions (left to right):
     * 0: EXPLORATION (0, 0)
     * 1: TENSION (width/5, 0)
     * 2: DRAFTING (2*width/5, 0)
     * 3: EDITORIAL (3*width/5, 0)
     * 4: TERMINATION (4*width/5, 0)
     */

    const phases = [
      'exploration',
      'tension',
      'drafting',
      'editorial',
      'termination'
    ];
    const zoneWidth = width / 5;

    phases.forEach((phase, index) => {
      const x = index * zoneWidth;

      // Background image (tiled to fill zone)
      const bg = this.add.image(x + zoneWidth / 2, height / 2, `bg-${phase}`);
      bg.setDisplaySize(zoneWidth, height);

      // Zone label (top-left corner of each zone)
      const label = this.add.text(x + 10, 10, phase.toUpperCase(), {
        font: 'bold 14px monospace',
        fill: '#ffffff',
        backgroundColor: '#000000aa',
        padding: { x: 5, y: 5 }
      });

      // Store zone reference for later positioning
      this.phaseZones = this.phaseZones || {};
      this.phaseZones[phase] = {
        x,
        y: 0,
        width: zoneWidth,
        height,
        label
      };
    });
  }

  async fetchStateFromServer() {
    /**
     * Poll /api/ui/claim-graph-state:
     * {
     *   "phase": "EXPLORATION" | "TENSION" | "DRAFTING" | "EDITORIAL" | "TERMINATION",
     *   "nodes": [
     *     {
     *       "id": "N-CLAIM-001",
     *       "kind": "claim" | "evidence" | "artifact" | "receipt" | "wild_text",
     *       "phase": "EXPLORATION",
     *       "admissibility": "ADMISSIBLE" | "QUARANTINED"
     *     },
     *     ...
     *   ],
     *   "gates": {
     *     "GATE_SCHEMA": "PASS" | "FAIL",
     *     "GATE_EVIDENCE": "PASS" | "FAIL",
     *     ...
     *   }
     * }
     */

    try {
      const response = await fetch('/api/ui/claim-graph-state');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      this.currentPhase = data.phase;

      // Update claims (render them in their zones)
      this.updateClaims(data.nodes);

      // Fetch and render receipts
      await this.fetchReceipts();

      // Update debug info
      this.updateDebugText(data);
    } catch (error) {
      console.error('Failed to fetch state:', error);
      this.debugText.setText(`Error: ${error.message}`);
    }
  }

  updateClaims(nodes) {
    /**
     * Remove old claim sprites and render new ones
     * Position claims within their phase zones (8 positions per zone to avoid overlap)
     *
     * Color by kind:
     * - claim → 🔵 blue
     * - evidence → 🟡 yellow
     * - artifact → 🟣 purple
     * - receipt → 🟢 green
     * - wild_text → 🔴 red (always QUARANTINED, bottom of zone)
     */

    // Clear old sprites
    if (this.claimSprites) {
      this.claimSprites.forEach((sprite) => sprite.destroy());
    }
    this.claimSprites = [];

    // Group nodes by phase
    const nodesByPhase = {};
    nodes.forEach((node) => {
      const phase = node.phase || 'EXPLORATION';
      if (!nodesByPhase[phase]) nodesByPhase[phase] = [];
      nodesByPhase[phase].push(node);
    });

    // Render each node in its zone
    Object.entries(nodesByPhase).forEach(([phase, phaseNodes]) => {
      const zone = this.phaseZones[phase];
      if (!zone) return;

      const spriteWidth = 32;
      const spriteHeight = 32;
      const positions = this.computeSpritePositions(
        zone,
        phaseNodes.length,
        spriteWidth,
        spriteHeight
      );

      phaseNodes.forEach((node, index) => {
        const pos = positions[index] || { x: zone.x + zone.width / 2, y: zone.y + 50 };

        // Create sprite
        const spriteKey = `sprite-${node.kind}`;
        const sprite = this.add.image(pos.x, pos.y, spriteKey);
        sprite.setDisplaySize(spriteWidth, spriteHeight);
        sprite.setInteractive();

        // Add tooltip showing node ID
        sprite.on('pointerover', () => {
          const tooltip = this.add.text(pos.x, pos.y - 40, node.id, {
            font: 'bold 10px monospace',
            fill: '#ffff00',
            backgroundColor: '#000000dd',
            padding: { x: 3, y: 3 }
          });
          sprite._tooltip = tooltip;
        });

        sprite.on('pointerout', () => {
          if (sprite._tooltip) sprite._tooltip.destroy();
        });

        // Tint based on admissibility
        if (node.admissibility === 'QUARANTINED') {
          sprite.setAlpha(0.6); // Dimmed for quarantined
        }

        this.claimSprites.push(sprite);
      });
    });
  }

  computeSpritePositions(zone, count, spriteWidth, spriteHeight) {
    /**
     * Position sprites in a grid within the zone (8 positions max per zone)
     * Layout: 4 cols × 2 rows (2 positions per row)
     *
     * Spacing: 10px margin from zone edges
     */

    const positions = [];
    const cols = 4;
    const rows = 2;
    const margin = 10;
    const colWidth = (zone.width - 2 * margin) / cols;
    const rowHeight = (zone.height - 2 * margin) / rows;

    for (let i = 0; i < Math.min(count, cols * rows); i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const x = zone.x + margin + col * colWidth + colWidth / 2;
      const y = zone.y + margin + row * rowHeight + rowHeight / 2;
      positions.push({ x, y });
    }

    return positions;
  }

  async fetchReceipts() {
    /**
     * Poll /api/ui/receipts:
     * {
     *   "receipts": [
     *     {
     *       "id": "RCPT-001",
     *       "verdict": "SHIP" | "ABORT",
     *       "gates": {
     *         "GATE_SCHEMA": "PASS",
     *         ...
     *       }
     *     },
     *     ...
     *   ]
     * }
     */

    try {
      const response = await fetch('/api/ui/receipts');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      this.renderReceipts(data.receipts);
    } catch (error) {
      console.error('Failed to fetch receipts:', error);
    }
  }

  renderReceipts(receipts) {
    /**
     * Show receipt badges at top-right of screen
     * Each badge shows verdict + gate summary
     * Fade out after 5 seconds
     */

    const x = this.cameras.main.width - 150;
    let y = 10;

    receipts.slice(0, 5).forEach((receipt) => {
      // Determine badge type
      const allPassed = Object.values(receipt.gates).every((v) => v === 'PASS');
      const badgeType = allPassed
        ? 'receipt_pass'
        : receipt.verdict === 'SHIP'
          ? 'receipt_pass'
          : 'receipt_fail';

      // Create badge
      const badge = this.add.image(x, y, `badge-${badgeType}`);
      badge.setDisplaySize(140, 40);
      badge.setInteractive();

      // Label with receipt ID
      const label = this.add.text(x - 60, y - 8, receipt.id, {
        font: 'bold 9px monospace',
        fill: '#000000'
      });

      // Fade out after 5s
      this.tweens.add({
        targets: [badge, label],
        alpha: 0,
        duration: 5000,
        onComplete: () => {
          badge.destroy();
          label.destroy();
        }
      });

      y += 50;
    });
  }

  updateDebugText(data) {
    const gateStatuses = Object.entries(data.gates)
      .map(([gate, status]) => `${gate}: ${status}`)
      .join(' | ');

    this.debugText.setText(
      `Phase: ${this.currentPhase} | Claims: ${data.nodes.length} | ${gateStatuses}`
    );
  }

  update() {
    // Animation loop (handled by Phaser tweens)
    // No additional per-frame logic needed
  }
}

/**
 * Initialize Phaser game
 */
const phasesConfig = {
  type: Phaser.AUTO,
  width: 1280,
  height: 720,
  parent: 'helen-game-container',
  scene: [PhasesScene],
  physics: {
    default: 'arcade',
    arcade: {
      debug: false
    }
  }
};

// Start game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const game = new Phaser.Game(phasesConfig);
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PhasesScene };
}

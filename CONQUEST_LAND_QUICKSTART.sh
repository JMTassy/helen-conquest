#!/bin/bash
# CONQUEST_LAND MVP — Quick Start (5 minutes to first compilation)

set -e

WORKDIR="$HOME/conquest-land-mv"
echo "🎯 CONQUEST_LAND MVP Setup"
echo "📁 Working directory: $WORKDIR"

# ===== STEP 1: Create workspace =====
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Root Cargo.toml
cat > Cargo.toml << 'EOF'
[workspace]
members = ["common", "server", "client"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
EOF

echo "✅ Workspace created"

# ===== STEP 2: Create members =====
cargo new --lib common
cargo new --bin server
cargo new --bin client

echo "✅ Members created"

# ===== STEP 3: Setup common/Cargo.toml =====
cat > common/Cargo.toml << 'EOF'
[package]
name = "conquest-common"
version.workspace = true
edition.workspace = true

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sha2 = "0.10"
hex = "0.4"

[dev-dependencies]
EOF

echo "✅ common/Cargo.toml configured"

# ===== STEP 4: Setup server/Cargo.toml =====
cat > server/Cargo.toml << 'EOF'
[package]
name = "conquest-server"
version.workspace = true
edition.workspace = true

[[bin]]
name = "conquest-server"
path = "src/main.rs"

[dependencies]
conquest-common = { path = "../common" }
tokio = { version = "1.0", features = ["full"] }
tokio-tungstenite = "0.21"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
log = "0.4"
env_logger = "0.11"
futures = "0.3"
EOF

echo "✅ server/Cargo.toml configured"

# ===== STEP 5: Setup client/Cargo.toml =====
cat > client/Cargo.toml << 'EOF'
[package]
name = "conquest-client"
version.workspace = true
edition.workspace = true

[lib]
crate-type = ["cdylib"]

[dependencies]
conquest-common = { path = "../common" }
wasm-bindgen = "0.2"
wasm-bindgen-futures = "0.4"
web-sys = { version = "0.3", features = [
    "Window", "Document", "HtmlCanvasElement",
    "WebGlRenderingContext",
] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[dev-dependencies]
wasm-bindgen-test = "0.3"
EOF

echo "✅ client/Cargo.toml configured"

# ===== STEP 6: Create stub src files =====
cat > common/src/lib.rs << 'EOF'
pub mod types;
pub mod rules;
pub mod event;
pub mod ledger;
pub mod state;

pub use types::*;
pub use rules::Rules;
pub use event::EventLog;
pub use ledger::Ledger;
EOF

cat > common/src/types.rs << 'EOF'
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PlayerId(pub u32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TileId(pub u32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TileOwner {
    Unclaimed,
    Player(PlayerId),
    Sealed(PlayerId),
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Tile {
    pub id: TileId,
    pub owner: TileOwner,
    pub pressure: u16,
    pub lock_tick: Option<u64>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct GameState {
    pub tick: u64,
    pub tiles: [Option<Tile>; 19],
    pub player_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Intent {
    Claim { player: PlayerId, tile: TileId },
    Lock { player: PlayerId, tile: TileId },
    Duel { claimer: PlayerId, defender: PlayerId, tile: TileId },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EventOutcome {
    Success(String),
    Failure(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameEvent {
    pub tick: u64,
    pub intent: Intent,
    pub outcome: EventOutcome,
    pub hash: String,
}
EOF

cat > common/src/rules.rs << 'EOF'
use crate::types::*;

pub struct Rules;

impl Rules {
    pub fn validate_claim(_state: &GameState, _player: PlayerId, _tile_id: TileId) -> Result<(), String> {
        Ok(())
    }

    pub fn validate_lock(_state: &GameState, _player: PlayerId, _tile_id: TileId) -> Result<(), String> {
        Ok(())
    }

    pub fn resolve_duel(_state: &GameState, claimer: PlayerId, _defender: PlayerId, _seed: u64) -> PlayerId {
        claimer
    }
}
EOF

cat > common/src/event.rs << 'EOF'
use crate::types::*;
use sha2::{Sha256, Digest};
use hex::encode;

pub struct EventLog {
    pub events: Vec<GameEvent>,
}

impl EventLog {
    pub fn new() -> Self {
        Self { events: Vec::new() }
    }

    pub fn append(&mut self, tick: u64, intent: Intent, outcome: EventOutcome) -> String {
        let hash = Self::compute_hash(tick, &intent, &outcome);
        self.events.push(GameEvent {
            tick,
            intent,
            outcome,
            hash: hash.clone(),
        });
        hash
    }

    fn compute_hash(tick: u64, intent: &Intent, outcome: &EventOutcome) -> String {
        let mut hasher = Sha256::new();
        hasher.update(tick.to_le_bytes());
        if let Ok(intent_json) = serde_json::to_string(intent) {
            hasher.update(intent_json);
        }
        if let Ok(outcome_json) = serde_json::to_string(outcome) {
            hasher.update(outcome_json);
        }
        encode(hasher.finalize())
    }

    pub fn verify(&self) -> bool {
        for event in &self.events {
            let expected_hash = Self::compute_hash(event.tick, &event.intent, &event.outcome);
            if event.hash != expected_hash {
                return false;
            }
        }
        true
    }
}
EOF

cat > common/src/ledger.rs << 'EOF'
use crate::event::EventLog;
use crate::types::*;
use std::collections::HashMap;

pub struct Ledger {
    events: EventLog,
    state_snapshots: HashMap<u64, GameState>,
}

impl Ledger {
    pub fn new() -> Self {
        Self {
            events: EventLog::new(),
            state_snapshots: HashMap::new(),
        }
    }

    pub fn record_action(&mut self, tick: u64, intent: Intent, state: &GameState) -> String {
        let outcome = EventOutcome::Success("OK".to_string());
        let hash = self.events.append(tick, intent, outcome);
        self.state_snapshots.insert(tick, state.clone());
        hash
    }

    pub fn events(&self) -> &[GameEvent] {
        &self.events.events
    }

    pub fn verify(&self) -> bool {
        self.events.verify()
    }
}
EOF

cat > common/src/state.rs << 'EOF'
use crate::types::*;

pub fn init_board() -> [Option<Tile>; 19] {
    let mut tiles = [None; 19];
    for i in 0..19 {
        tiles[i] = Some(Tile {
            id: TileId(i as u32),
            owner: TileOwner::Unclaimed,
            pressure: 0,
            lock_tick: None,
        });
    }
    tiles
}

pub fn initial_state(player_count: u32) -> GameState {
    GameState {
        tick: 0,
        tiles: init_board(),
        player_count,
    }
}
EOF

echo "✅ common/ stubs created"

cat > server/src/main.rs << 'EOF'
fn main() {
    println!("🎮 CONQUEST_LAND Server (MVP)");
    println!("Listening on ws://127.0.0.1:8080");
}
EOF

cat > client/src/lib.rs << 'EOF'
pub fn hello() {
    println!("🎮 CONQUEST_LAND Client (MVP)");
}
EOF

echo "✅ server/ and client/ stubs created"

# ===== STEP 7: Test compilation =====
echo ""
echo "🔨 Testing compilation..."
cargo check --all

echo ""
echo "✅ All modules compile successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Review: CONQUEST_LAND_MVP_IMPLEMENTATION_BLUEPRINT.md"
echo "  2. Fill in: common/src/rules.rs (full validation logic)"
echo "  3. Build server: cargo build -p conquest-server"
echo "  4. Build client: cargo build -p conquest-client"
echo ""
echo "📂 Directory: $WORKDIR"
echo "Done!"

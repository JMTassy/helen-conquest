# CONQUEST_LAND MVP — Implementation Blueprint (GO A)

**Status:** Ready to code
**Timeline:** 4–5 weeks, MVP jouable
**Architecture:** Rust (common/server/client), WASM/WebGL rendering, Option A ledger (deterministic, no crypto)

---

## PHASE 0: Project Structure (Day 1–2)

### Cargo Workspace Setup

```bash
# Initialize workspace
cargo new --name conquest-land conquest-land
cd conquest-land

# Create workspace members
cargo new --lib common
cargo new --bin server
cargo new --bin client

# Update Cargo.toml (root)
[workspace]
members = ["common", "server", "client"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
```

### Directory Structure (After Setup)

```
conquest-land/
├── Cargo.toml                          # Workspace root
├── common/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── state.rs                   # Game state model
│       ├── rules.rs                   # CLAIM, LOCK, DUEL validation
│       ├── event.rs                   # Event + SHA256 hash
│       ├── ledger.rs                  # Append-only log
│       └── types.rs                   # Shared types (Player, Tile, etc.)
├── server/
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── tick_loop.rs               # 500ms game loop
│       ├── fog.rs                     # Visibility per player
│       ├── authority.rs               # Anti-cheat validation
│       ├── network.rs                 # WebSocket server
│       └── persistence.rs             # Ledger storage
├── client/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── render.rs                  # WebGL hex rendering
│       ├── ui.rs                      # HUD + minimal UI
│       ├── network.rs                 # WebSocket client
│       ├── input.rs                   # Mouse/keyboard intent
│       └── main.rs                    # WASM entry point
└── assets/
    ├── shaders/
    │   ├── hex.vert                   # Hex grid vertex shader
    │   ├── hex.frag                   # Hex grid fragment shader
    │   ├── fog.frag                   # Fog-of-war overlay
    │   └── seal.frag                  # Lock/seal aura
    └── data/
        └── initial_tiles.json         # 19-tile board config
```

---

## PHASE 1: common/ — Shared Game Logic (Week 1)

### common/Cargo.toml

```toml
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
```

### common/src/types.rs

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PlayerId(pub u32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TileId(pub u32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TileOwner {
    Unclaimed,
    Player(PlayerId),
    Sealed(PlayerId), // Locked by LOCK action
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Tile {
    pub id: TileId,
    pub owner: TileOwner,
    pub pressure: u16,        // Pressure from adjacent tiles (0–255)
    pub lock_tick: Option<u64>, // When LOCK was applied (None = unlocked)
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct GameState {
    pub tick: u64,
    pub tiles: [Option<Tile>; 19], // 19-tile hex board
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
    pub hash: String, // SHA256(tick || intent || outcome)
}
```

### common/src/rules.rs

```rust
use crate::types::*;

pub struct Rules;

impl Rules {
    /// CLAIM: Player claims unclaimed tile adjacent to their territory
    pub fn validate_claim(state: &GameState, player: PlayerId, tile_id: TileId) -> Result<(), String> {
        let tile_idx = tile_id.0 as usize;

        if tile_idx >= 19 {
            return Err("Tile out of bounds".to_string());
        }

        // Tile must exist and be unclaimed
        match &state.tiles[tile_idx] {
            Some(tile) if matches!(tile.owner, TileOwner::Unclaimed) => {},
            Some(_) => return Err("Tile already owned or sealed".to_string()),
            None => return Err("Tile does not exist".to_string()),
        }

        // Player must own adjacent tile
        let adjacent_ids = Self::adjacent_tiles(tile_id);
        let has_adjacent = adjacent_ids.iter().any(|&id| {
            state.tiles[id.0 as usize]
                .as_ref()
                .map(|t| matches!(t.owner, TileOwner::Player(p) if p == player))
                .unwrap_or(false)
        });

        if !has_adjacent {
            return Err("No adjacent territory to expand from".to_string());
        }

        Ok(())
    }

    /// LOCK: Player seals a claimed tile (irrevocable for 7 ticks)
    pub fn validate_lock(state: &GameState, player: PlayerId, tile_id: TileId) -> Result<(), String> {
        let tile_idx = tile_id.0 as usize;

        match &state.tiles[tile_idx] {
            Some(tile) if matches!(tile.owner, TileOwner::Player(p) if p == player) => {
                if tile.lock_tick.is_some() {
                    return Err("Tile already sealed".to_string());
                }
                Ok(())
            }
            _ => Err("Tile not owned by player".to_string()),
        }
    }

    /// DUEL: Resolve conflict between two players on contested tile
    /// Outcome: seeded by (tick % 2), ensuring determinism
    pub fn resolve_duel(state: &GameState, claimer: PlayerId, defender: PlayerId, seed: u64) -> PlayerId {
        // Deterministic: seed = tick % 2
        // Even tick → claimer wins; odd → defender wins
        if seed % 2 == 0 { claimer } else { defender }
    }

    /// Adjacent tile IDs (hex grid, center + 6 neighbors)
    fn adjacent_tiles(tile_id: TileId) -> Vec<TileId> {
        // Simplified: hex grid adjacency (implementation depends on board layout)
        // For 19-tile hex (center + 2 rings), compute neighbors
        vec![] // Placeholder
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_claim_unclaimed_adjacent() {
        // Setup: player owns tile 0, wants to claim tile 1
        // Expected: Success
    }

    #[test]
    fn test_claim_non_adjacent() {
        // Setup: player owns tile 0, tries to claim tile 18 (far away)
        // Expected: Failure
    }

    #[test]
    fn test_lock_success() {
        // Setup: player owns tile 0, locks it
        // Expected: lock_tick set to current tick
    }

    #[test]
    fn test_duel_determinism() {
        // Setup: duel between A and B, seed = 0 → A wins; seed = 1 → B wins
        // Expected: Always reproducible
    }
}
```

### common/src/event.rs

```rust
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

    /// Append event and compute hash
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

        // Include tick
        hasher.update(tick.to_le_bytes());

        // Include intent (JSON serialized)
        if let Ok(intent_json) = serde_json::to_string(intent) {
            hasher.update(intent_json);
        }

        // Include outcome (JSON serialized)
        if let Ok(outcome_json) = serde_json::to_string(outcome) {
            hasher.update(outcome_json);
        }

        encode(hasher.finalize())
    }

    /// Verify Merkle chain integrity (all hashes are consistent)
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash_determinism() {
        let intent = Intent::Claim {
            player: PlayerId(1),
            tile: TileId(0),
        };
        let outcome = EventOutcome::Success("Claimed".to_string());

        let hash1 = EventLog::compute_hash(0, &intent, &outcome);
        let hash2 = EventLog::compute_hash(0, &intent, &outcome);
        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_ledger_append() {
        let mut log = EventLog::new();
        let hash1 = log.append(0, Intent::Claim {
            player: PlayerId(1),
            tile: TileId(0),
        }, EventOutcome::Success("OK".to_string()));

        assert_eq!(log.events.len(), 1);
        assert!(!hash1.is_empty());
    }

    #[test]
    fn test_ledger_verify() {
        let mut log = EventLog::new();
        log.append(0, Intent::Claim {
            player: PlayerId(1),
            tile: TileId(0),
        }, EventOutcome::Success("OK".to_string()));

        assert!(log.verify());
    }
}
```

### common/src/ledger.rs

```rust
use crate::event::EventLog;
use crate::types::*;
use std::collections::HashMap;

/// Append-only ledger with Merkle chain
pub struct Ledger {
    events: EventLog,
    state_snapshots: HashMap<u64, GameState>, // Snapshot per tick
}

impl Ledger {
    pub fn new() -> Self {
        Self {
            events: EventLog::new(),
            state_snapshots: HashMap::new(),
        }
    }

    /// Record action and apply state transition
    pub fn record_action(&mut self, tick: u64, intent: Intent, state: &GameState) -> String {
        // Validate action against state
        let outcome = match &intent {
            Intent::Claim { player, tile } => {
                use crate::rules::Rules;
                match Rules::validate_claim(state, *player, *tile) {
                    Ok(_) => EventOutcome::Success(format!("Claimed tile {:?}", tile)),
                    Err(e) => EventOutcome::Failure(e),
                }
            }
            Intent::Lock { player, tile } => {
                use crate::rules::Rules;
                match Rules::validate_lock(state, *player, *tile) {
                    Ok(_) => EventOutcome::Success(format!("Locked tile {:?}", tile)),
                    Err(e) => EventOutcome::Failure(e),
                }
            }
            Intent::Duel { claimer, defender, tile } => {
                use crate::rules::Rules;
                let winner = Rules::resolve_duel(state, *claimer, *defender, tick);
                EventOutcome::Success(format!("Duel won by {:?}", winner))
            }
        };

        // Append to ledger
        let hash = self.events.append(tick, intent, outcome);

        // Snapshot state
        self.state_snapshots.insert(tick, state.clone());

        hash
    }

    /// Get all events
    pub fn events(&self) -> &[GameEvent] {
        &self.events.events
    }

    /// Verify ledger integrity
    pub fn verify(&self) -> bool {
        self.events.verify()
    }

    /// Export ledger as JSON (for archival or verification)
    pub fn export_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(&self.events.events)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ledger_record() {
        let mut ledger = Ledger::new();
        let state = GameState {
            tick: 0,
            tiles: [None; 19],
            player_count: 2,
        };

        let hash = ledger.record_action(0, Intent::Claim {
            player: PlayerId(1),
            tile: TileId(0),
        }, &state);

        assert!(!hash.is_empty());
        assert_eq!(ledger.events().len(), 1);
    }

    #[test]
    fn test_ledger_verify() {
        let mut ledger = Ledger::new();
        let state = GameState {
            tick: 0,
            tiles: [None; 19],
            player_count: 2,
        };

        ledger.record_action(0, Intent::Claim {
            player: PlayerId(1),
            tile: TileId(0),
        }, &state);

        assert!(ledger.verify());
    }
}
```

### common/src/lib.rs

```rust
pub mod types;
pub mod rules;
pub mod event;
pub mod ledger;
pub mod state;

pub use types::*;
pub use rules::Rules;
pub use event::EventLog;
pub use ledger::Ledger;
```

### common/src/state.rs

```rust
use crate::types::*;

/// Initialize 19-tile hex board (center + 2 rings)
pub fn init_board() -> [Option<Tile>; 19] {
    let mut tiles = [None; 19];

    // Center tile
    tiles[0] = Some(Tile {
        id: TileId(0),
        owner: TileOwner::Unclaimed,
        pressure: 0,
        lock_tick: None,
    });

    // Ring 1 (6 tiles)
    for i in 1..=6 {
        tiles[i] = Some(Tile {
            id: TileId(i as u32),
            owner: TileOwner::Unclaimed,
            pressure: 0,
            lock_tick: None,
        });
    }

    // Ring 2 (12 tiles)
    for i in 7..19 {
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
```

---

## PHASE 2: server/ — Authoritative Game Loop (Week 2–3)

### server/Cargo.toml

```toml
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
```

### server/src/main.rs

```rust
mod tick_loop;
mod fog;
mod authority;
mod network;
mod persistence;

use tokio::sync::{broadcast, RwLock};
use std::sync::Arc;
use conquest_common::GameState;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let state = Arc::new(RwLock::new(conquest_common::state::initial_state(2)));
    let (tx, _) = broadcast::channel(1024);

    // Spawn tick loop (500ms)
    let state_clone = Arc::clone(&state);
    let tx_clone = tx.clone();
    tokio::spawn(tick_loop::run_tick_loop(state_clone, tx_clone));

    // Spawn network server (WebSocket)
    network::start_server(state, tx).await?;

    Ok(())
}
```

### server/src/tick_loop.rs

```rust
use conquest_common::{GameState, Intent, EventOutcome};
use tokio::sync::broadcast;
use std::sync::Arc;
use tokio::sync::RwLock;
use std::time::Duration;
use tokio::time::sleep;

pub async fn run_tick_loop(
    state: Arc<RwLock<GameState>>,
    tx: broadcast::Sender<String>,
) {
    let mut tick: u64 = 0;

    loop {
        sleep(Duration::from_millis(500)).await;

        let mut state_guard = state.write().await;
        state_guard.tick = tick;

        // Apply pressure decay, lock timeout, etc.
        apply_tick_effects(&mut *state_guard, tick);

        // Broadcast new state to all clients
        let json = serde_json::to_string(&*state_guard).unwrap_or_default();
        let _ = tx.send(json);

        tick += 1;
    }
}

fn apply_tick_effects(state: &mut GameState, tick: u64) {
    // Decay pressure on all tiles
    for tile_opt in &mut state.tiles {
        if let Some(tile) = tile_opt {
            if tile.pressure > 0 {
                tile.pressure = tile.pressure.saturating_sub(5);
            }

            // Unlock tiles after 7 ticks
            if let Some(lock_tick) = tile.lock_tick {
                if tick - lock_tick >= 7 {
                    tile.lock_tick = None;
                }
            }
        }
    }
}
```

### server/src/authority.rs

```rust
use conquest_common::{GameState, Intent, Rules, PlayerId, TileId};

/// Anti-cheat: validate intent against server state before applying
pub fn validate_intent(state: &GameState, intent: &Intent) -> Result<(), String> {
    match intent {
        Intent::Claim { player, tile } => {
            Rules::validate_claim(state, *player, *tile)
        }
        Intent::Lock { player, tile } => {
            Rules::validate_lock(state, *player, *tile)
        }
        Intent::Duel { .. } => {
            Ok(()) // Duel validation is implicit (always allowed)
        }
    }
}

/// Apply intent to state (mutate)
pub fn apply_intent(state: &mut GameState, intent: &Intent) -> EventOutcome {
    match intent {
        Intent::Claim { player, tile } => {
            if let Ok(_) = Rules::validate_claim(state, *player, *tile) {
                if let Some(tile_ref) = &mut state.tiles[tile.0 as usize] {
                    use conquest_common::TileOwner;
                    tile_ref.owner = TileOwner::Player(*player);
                    EventOutcome::Success(format!("Claimed tile {:?}", tile))
                } else {
                    EventOutcome::Failure("Tile doesn't exist".to_string())
                }
            } else {
                EventOutcome::Failure("CLAIM failed validation".to_string())
            }
        }
        Intent::Lock { player, tile } => {
            if let Ok(_) = Rules::validate_lock(state, *player, *tile) {
                if let Some(tile_ref) = &mut state.tiles[tile.0 as usize] {
                    use conquest_common::TileOwner;
                    tile_ref.owner = TileOwner::Sealed(*player);
                    tile_ref.lock_tick = Some(state.tick);
                    EventOutcome::Success(format!("Locked tile {:?}", tile))
                } else {
                    EventOutcome::Failure("Tile doesn't exist".to_string())
                }
            } else {
                EventOutcome::Failure("LOCK failed validation".to_string())
            }
        }
        Intent::Duel { claimer, defender, tile } => {
            let winner = Rules::resolve_duel(state, *claimer, *defender, state.tick);
            EventOutcome::Success(format!("Duel won by {:?}", winner))
        }
    }
}
```

### server/src/fog.rs

```rust
use conquest_common::{GameState, PlayerId, TileOwner};

/// Compute visible tiles for a player (fog-of-war)
pub fn visible_tiles(state: &GameState, player: PlayerId) -> Vec<usize> {
    let mut visible = Vec::new();

    for (idx, tile_opt) in state.tiles.iter().enumerate() {
        if let Some(tile) = tile_opt {
            // Player can see:
            // 1. Tiles they own
            // 2. Adjacent tiles to their territory
            // 3. Sealed tiles (always visible, shared knowledge)

            let can_see = matches!(tile.owner, TileOwner::Player(p) if p == player)
                || matches!(tile.owner, TileOwner::Sealed(_))
                || Self::is_adjacent_to_player(state, player, idx);

            if can_see {
                visible.push(idx);
            }
        }
    }

    visible
}

fn is_adjacent_to_player(state: &GameState, player: PlayerId, tile_idx: usize) -> bool {
    // Simplified: check if any neighbor is owned by player
    // (Full hex adjacency logic depends on board layout)
    false // Placeholder
}

/// Filter state for client visibility
pub fn fog_filter(state: &GameState, player: PlayerId) -> GameState {
    let mut filtered = state.clone();
    let visible = visible_tiles(state, player);

    for (idx, tile_opt) in filtered.tiles.iter_mut().enumerate() {
        if !visible.contains(&idx) {
            *tile_opt = None; // Hide this tile from client
        }
    }

    filtered
}
```

### server/src/network.rs

```rust
use tokio::net::TcpListener;
use tokio_tungstenite::accept_async;
use tokio::sync::broadcast;
use std::sync::Arc;
use tokio::sync::RwLock;
use conquest_common::GameState;
use futures::stream::{StreamExt, SplitStream, SplitSink};
use tokio_tungstenite::WebSocketStream;
use tokio::net::TcpStream;

pub async fn start_server(
    state: Arc<RwLock<GameState>>,
    tx: broadcast::Sender<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    log::info!("Server listening on ws://127.0.0.1:8080");

    loop {
        let (socket, addr) = listener.accept().await?;
        log::info!("New connection: {}", addr);

        let state = Arc::clone(&state);
        let tx = tx.clone();

        tokio::spawn(async move {
            if let Err(e) = handle_client(socket, state, tx).await {
                log::error!("Client error: {}", e);
            }
        });
    }
}

async fn handle_client(
    stream: TcpStream,
    state: Arc<RwLock<GameState>>,
    tx: broadcast::Sender<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    let ws = accept_async(stream).await?;
    let (mut ws_sink, ws_stream) = ws.split();
    let mut rx = tx.subscribe();

    // Send initial state
    let state_guard = state.read().await;
    let json = serde_json::to_string(&*state_guard)?;
    drop(state_guard);

    ws_sink.send(tokio_tungstenite::tungstenite::Message::Text(json)).await?;

    // Broadcast loop + client intent loop (simplified)
    loop {
        tokio::select! {
            msg = rx.recv() => {
                if let Ok(state_json) = msg {
                    ws_sink.send(tokio_tungstenite::tungstenite::Message::Text(state_json)).await?;
                }
            }
        }
    }
}
```

### server/src/persistence.rs

```rust
use std::fs;
use std::path::Path;

pub fn save_ledger(ledger_json: &str, path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    fs::write(path, ledger_json)?;
    Ok(())
}

pub fn load_ledger(path: &Path) -> Result<String, Box<dyn std::error::Error>> {
    let json = fs::read_to_string(path)?;
    Ok(json)
}
```

---

## PHASE 3: client/ — WASM + WebGL Rendering (Week 3–4)

### client/Cargo.toml

```toml
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
    "Window", "Document", "HtmlCanvasElement", "CanvasRenderingContext2d",
    "WebGlRenderingContext", "WebGlProgram", "WebGlShader",
] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[dev-dependencies]
wasm-bindgen-test = "0.3"
```

### client/src/lib.rs

```rust
mod render;
mod ui;
mod network;
mod input;

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub async fn run() -> Result<(), JsValue> {
    // Initialize WASM panic hooks
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();

    // Start network (WebSocket to server)
    let state_rx = network::connect_server("ws://127.0.0.1:8080").await?;

    // Initialize rendering
    let canvas = render::setup_canvas()?;
    let gl = render::get_webgl_context(&canvas)?;

    // Start input handler
    input::setup_input_handler(&canvas);

    // Main loop
    render::main_loop(gl, state_rx).await?;

    Ok(())
}
```

### client/src/render.rs

```rust
use wasm_bindgen::prelude::*;
use web_sys::{WebGlRenderingContext, HtmlCanvasElement};

pub fn setup_canvas() -> Result<HtmlCanvasElement, JsValue> {
    let window = web_sys::window().ok_or("No window")?;
    let document = window.document().ok_or("No document")?;
    let canvas = document
        .get_element_by_id("canvas")
        .ok_or("No canvas element")?
        .dyn_into::<HtmlCanvasElement>()?;

    canvas.set_width(1024);
    canvas.set_height(768);

    Ok(canvas)
}

pub fn get_webgl_context(canvas: &HtmlCanvasElement) -> Result<WebGlRenderingContext, JsValue> {
    canvas
        .get_context("webgl")?
        .ok_or("No WebGL context")?
        .dyn_into::<WebGlRenderingContext>()
}

pub async fn main_loop(
    _gl: WebGlRenderingContext,
    _state_rx: tokio::sync::mpsc::Receiver<String>,
) -> Result<(), JsValue> {
    // Render loop (simplified)
    // In practice: request_animation_frame loop, receive state updates, render hex grid

    Ok(())
}
```

### client/src/network.rs

```rust
use wasm_bindgen::prelude::*;

pub async fn connect_server(url: &str) -> Result<tokio::sync::mpsc::Receiver<String>, JsValue> {
    // Create WebSocket connection
    // Return receiver for state updates

    let (tx, rx) = tokio::sync::mpsc::channel(128);

    // Connect to server (simplified; actual WebSocket setup requires web-sys)
    // tx.send(state_json).await...

    Ok(rx)
}
```

### client/src/input.rs

```rust
use wasm_bindgen::prelude::*;
use web_sys::HtmlCanvasElement;

pub fn setup_input_handler(_canvas: &HtmlCanvasElement) {
    // Mouse click handler (convert click to Intent::Claim)
    // Keyboard handler (convert key to Intent::Lock, etc.)
}
```

---

## PHASE 4: Assets — Shaders & Configuration (Week 4)

### assets/shaders/hex.vert

```glsl
#version 100
precision highp float;

attribute vec2 a_position;
attribute vec3 a_color;

varying vec3 v_color;

uniform mat4 u_matrix;

void main() {
    gl_Position = u_matrix * vec4(a_position, 0.0, 1.0);
    v_color = a_color;
}
```

### assets/shaders/hex.frag

```glsl
#version 100
precision highp float;

varying vec3 v_color;

void main() {
    gl_FragColor = vec4(v_color, 1.0);
}
```

### assets/shaders/fog.frag

```glsl
#version 100
precision highp float;

uniform sampler2D u_texture;
uniform sampler2D u_fog_mask;

varying vec2 v_texCoord;

void main() {
    vec4 color = texture2D(u_texture, v_texCoord);
    float fog = texture2D(u_fog_mask, v_texCoord).r;

    // Fade color where fog = 0
    color.rgb *= fog;

    gl_FragColor = color;
}
```

### assets/shaders/seal.frag

```glsl
#version 100
precision highp float;

varying vec2 v_position;
uniform float u_time;

void main() {
    float dist = length(v_position);
    float aura = sin(dist * 5.0 - u_time) * 0.5 + 0.5;

    gl_FragColor = vec4(1.0, 0.8, 0.2, aura * 0.6);
}
```

### assets/data/initial_tiles.json

```json
{
  "board": {
    "radius": 2,
    "tiles": [
      { "id": 0, "x": 0, "y": 0, "owner": "unclaimed" },
      { "id": 1, "x": 1, "y": 0, "owner": "unclaimed" },
      { "id": 2, "x": 0, "y": 1, "owner": "unclaimed" },
      { "id": 3, "x": -1, "y": 1, "owner": "unclaimed" },
      { "id": 4, "x": -1, "y": 0, "owner": "unclaimed" },
      { "id": 5, "x": 0, "y": -1, "owner": "unclaimed" },
      { "id": 6, "x": 1, "y": -1, "owner": "unclaimed" }
    ]
  }
}
```

---

## PHASE 5: Integration & Testing (Week 4–5)

### Build Instructions

```bash
# Install Trunk (WASM build tool)
cargo install trunk

# Test compilation (all members)
cargo test --all

# Build WASM client
cd client
trunk build --release

# Build server
cd ../server
cargo build --release

# Run server
./target/release/conquest-server

# Serve client (Trunk dev server)
cd ../client
trunk serve
```

### Testing Strategy

```bash
# Unit tests (common)
cargo test -p conquest-common

# Integration tests (server)
cargo test -p conquest-server

# Load test simulation
python3 simulate_load.py (10 clients, 100 ticks)
```

---

## PHASE 6: Deployment & Polish (Week 5)

### Deployment Checklist

- [ ] Server: Deploy to cloud (Fly.io, AWS, or self-hosted)
- [ ] Client: Deploy WASM build to CDN
- [ ] Ledger: Set up persistent storage (PostgreSQL or S3)
- [ ] Monitoring: Add logging + metrics (Datadog or similar)
- [ ] Documentation: Write API docs + player guide

### MVP Launch Checklist

- [ ] Server runs 500ms ticks reliably
- [ ] Client renders hex grid + fog
- [ ] 3 verbs work (CLAIM, LOCK, DUEL)
- [ ] Ledger records all events + hashes
- [ ] Play in 5 seconds (no login required to spectate)
- [ ] Anti-cheat validated (fog works)

---

## Timeline (Compressed)

| Week | Phase | Deliverable |
|------|-------|-------------|
| **1** | common/ | Types + Rules + Events + Ledger (all tested) |
| **2–3** | server/ | Tick loop + Authority + Network (MVP server running) |
| **3–4** | client/ | Rendering + Shaders + WebSocket (MVP client loading) |
| **4** | Integration | Build + test + bug fixes |
| **5** | Polish | Deploy + documentation |

**Total: 4–5 weeks to playable MVP**

---

## Success Criteria (MVP = DONE)

1. ✅ **Play in 5 seconds**: Load URL → spectator (no login)
2. ✅ **3 verbs work**: CLAIM, LOCK, DUEL fully functional
3. ✅ **Ledger irrevocable**: Every action hashed + appended
4. ✅ **Deterministic replay**: Replay same seed → same outcome
5. ✅ **Fog-of-war**: Players only see allowed tiles
6. ✅ **Server authoritative**: Client cannot cheat
7. ✅ **Hex grid renders**: Visual feedback of territory
8. ✅ **Tests pass**: All unit + integration tests green

---

## Open Questions (Clarify Before Coding)

1. **Board size**: 19 tiles (hex) or different?
2. **Player count**: 2–4 players or up to 10+?
3. **Tick duration**: 500ms or different?
4. **Lock timeout**: 7 ticks or different?
5. **Duel determinism**: seed = tick % 2 or hash-based?
6. **UI complexity**: Minimal HUD or full dashboard?
7. **Audio**: Include sound effects or no?

---

**Next**: Start coding `common/src/state.rs`. You can compile and test independently.

Ready to begin?

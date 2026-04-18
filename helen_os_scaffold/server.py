from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path

# HELEN OS Imports
from helen_os.cli import _get_helen, _load_config, _get_memory
from helen_os.soul import HELEN_SYSTEM_PROMPT
from helen_os.api.do_next import DoNextService, DoNextRequest, DoNextResponse, ErrorResponse

# Channel C bridge — non-sovereign, fail-safe (import may be absent in minimal installs)
try:
    from helen_star_bridge import get_bridge as _get_bridge
    _BRIDGE_ENABLED = True
except ImportError:
    _BRIDGE_ENABLED = False
    def _get_bridge():  # type: ignore[misc]
        return None

# Initialize /do_next service (singleton)
_do_next_service = DoNextService()

app = FastAPI(title="HELEN OS API Bridge")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    location: str = "San Francisco"
    district: str = "oracle_town"
    street: str = "marketing"

class ChatResponse(BaseModel):
    response: str
    hal_telemetry: Optional[Dict[str, Any]] = None

@app.get("/api/status")
async def get_status():
    helen = _get_helen()
    return {
        "location": helen.location,
        "district": helen.current_district,
        "street": helen.current_street,
        "status": "online"
    }

@app.get("/api/history")
async def get_history(limit: int = 20):
    memory = _get_memory()
    history = memory.get_history()
    return history[-limit:]

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    bridge = _get_bridge() if _BRIDGE_ENABLED else None
    try:
        helen = _get_helen()
        helen.location = req.location
        helen.current_district = req.district
        helen.current_street = req.street

        # ── Channel C: signal turn start (non-sovereign, fail-safe) ──
        if bridge:
            bridge.on_turn_start(req.message)

        # HELEN.speak() returns a formatted string with [HER] + [HAL] headers
        output = helen.speak(req.message)

        # ── Channel C: signal turn end (non-sovereign, fail-safe) ──
        if bridge:
            bridge.on_turn_end(output)
            bridge.write_session_memo(output)

        return ChatResponse(response=output)
    except Exception as e:
        if bridge:
            bridge.update_state("error", f"Exception: {str(e)[:80]}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/update")
async def update_knowledge(fact: Dict[str, Any]):
    """
    Update the knowledge base (MemoryKernel) with new facts.
    Expects: {"key": "...", "value": "...", "actor": "...", "status": "..."}
    """
    try:
        memory = _get_memory()
        entry = memory.add_fact(
            key=fact.get("key", "manual_update"),
            value=fact.get("value", ""),
            actor=fact.get("actor", "system"),
            status=fact.get("status", "OBSERVED")
        )
        return {"status": "success", "entry": entry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ───────────────────────────────────────────────────────────────
# UI API Endpoints (Move 4: HELEN-Office-UI)
# ───────────────────────────────────────────────────────────────

@app.get("/api/ui/claim-graph-state")
async def get_claim_graph_state():
    """
    Poll endpoint for Phaser UI scene.
    Returns current governance state: phase, active nodes, gate status.

    Response:
    {
        "phase": "EXPLORATION" | "TENSION" | "DRAFTING" | "EDITORIAL" | "TERMINATION",
        "nodes": [
            {
                "id": "N-CLAIM-001",
                "kind": "claim" | "evidence" | "artifact" | "receipt" | "wild_text",
                "phase": "EXPLORATION",
                "admissibility": "ADMISSIBLE" | "QUARANTINED",
                "tier": 1 | 2 | 3
            },
            ...
        ],
        "gates": {
            "GATE_SCHEMA": "PASS" | "FAIL",
            "GATE_EVIDENCE": "PASS" | "FAIL",
            "GATE_AUTHORITY": "PASS" | "FAIL",
            "GATE_DETERMINISM": "PASS" | "FAIL",
            "GATE_APPEND_ONLY": "PASS" | "FAIL"
        }
    }
    """
    try:
        helen = _get_helen()
        memory = _get_memory()

        # Get current phase from HELEN (stored in state)
        current_phase = getattr(helen, 'current_phase', 'EXPLORATION')

        # Get active claims from governance state (placeholder for now)
        # In full implementation, this would query the CLAIM_GRAPH_V1 and GovernanceVM
        nodes = []
        gates = {
            "GATE_SCHEMA": "PASS",
            "GATE_EVIDENCE": "PASS",
            "GATE_AUTHORITY": "PASS",
            "GATE_DETERMINISM": "PASS",
            "GATE_APPEND_ONLY": "PASS"
        }

        return {
            "phase": current_phase,
            "nodes": nodes,
            "gates": gates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ui/receipts")
async def get_recent_receipts(limit: int = 10):
    """
    Poll endpoint for receipt badges in UI.
    Returns recent receipts for display as floating badges.

    Response:
    {
        "receipts": [
            {
                "id": "RCPT-001",
                "verdict": "SHIP" | "ABORT",
                "gates": {
                    "GATE_SCHEMA": "PASS",
                    ...
                },
                "timestamp": "2026-03-09T12:34:56Z"
            },
            ...
        ]
    }
    """
    try:
        # Placeholder: In full implementation, query ledger for recent receipts
        receipts = []

        return {
            "receipts": receipts[:limit]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ui/theme/{theme_name}")
async def get_theme_config(theme_name: str):
    """
    Get theme configuration for UI rendering.
    Supports: pixel-cozy, governance-formal, digital-minimal

    Response: Theme configuration object from themes.config.json
    """
    try:
        # Load theme config
        config_path = Path(__file__).parent / "helen_os" / "ui" / "themes.config.json"

        if not config_path.exists():
            raise HTTPException(status_code=404, detail="Theme config not found")

        with open(config_path) as f:
            config = json.load(f)

        if theme_name not in config["themes"]:
            raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")

        return config["themes"][theme_name]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ───────────────────────────────────────────────────────────────
# FROZEN KERNEL BOUNDARY: /do_next Endpoint
# ───────────────────────────────────────────────────────────────

@app.post("/do_next", response_model=DoNextResponse)
async def do_next(req: DoNextRequest):
    """
    Execute one bounded action through the frozen 7-phase lifecycle
    (API_CONTRACT_DO_NEXT_V1, SESSION_PERSISTENCE_SEMANTICS_V1, LIFECYCLE_INVARIANTS_V1).

    Request: DoNextRequest with session_id, user_input, mode, model, and optional params
    Response: DoNextResponse with reply, receipt_id, run_id, epoch, continuity
    Status codes: 200 (success), 400 (validation/audit block), 401 (unauthorized), 500 (server error)
    """
    try:
        # Execute through 7-phase lifecycle
        response = _do_next_service.execute(req)
        return response
    except ValueError as e:
        # 400 Bad Request (validation or audit block)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 500 Server Error
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def _startup():
    """Register HELEN agent roster in Star-Office on server boot."""
    if _BRIDGE_ENABLED:
        bridge = _get_bridge()
        bridge.register_agents()
        bridge.update_state("idle", "HELEN OS online")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

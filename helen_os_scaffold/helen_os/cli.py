"""
HELEN OS — Command Line Interface
MVP v0.2: lazy loading, non-fatal seal warning, stub fallback, seed world support.

Entry point: helen_os.cli:main  (defined in pyproject.toml)
"""

import click
import yaml
import os
from typing import Optional

# ─── Lazy singletons ──────────────────────────────────────────────────────────
# Nothing is instantiated at module load time.
# Each accessor builds the singleton on first call.

_config: Optional[dict] = None
_kernel  = None
_memory  = None
_adapter = None
_helen   = None


def _load_config() -> dict:
    global _config
    if _config is None:
        config_path = os.path.join(os.getcwd(), "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                _config = yaml.safe_load(f) or {}
        else:
            _config = {}
    return _config


def _get_kernel():
    global _kernel
    if _kernel is None:
        from .kernel import GovernanceVM
        cfg = _load_config()
        _kernel = GovernanceVM(
            ledger_path=cfg.get("storage", {}).get("ledger_path", "storage/ledger.ndjson")
        )
    return _kernel


def _get_memory():
    global _memory
    if _memory is None:
        from .memory import MemoryKernel
        cfg = _load_config()
        _memory = MemoryKernel(
            db_path=cfg.get("storage", {}).get("memory_db_path", "memory/helen.db"),
            ndjson_path=cfg.get("storage", {}).get("memory_ndjson_path", "memory/memory.ndjson")
        )
    return _memory


def _get_adapter():
    global _adapter
    if _adapter is None:
        from .adapters import get_adapter
        _adapter = get_adapter(_load_config())
    return _adapter


def _get_helen():
    global _helen
    if _helen is None:
        from .helen import HELEN
        _helen = HELEN(_get_kernel(), _get_memory(), _get_adapter())
    return _helen


# ─── Boot check (non-fatal) ────────────────────────────────────────────────────

def _boot_check() -> bool:
    """
    Verify SEAL_V2 environment hash.
    Returns True if OK or no seal exists.
    Prints a warning (never exits) if seal is stale.
    """
    try:
        kernel = _get_kernel()
        ok = kernel.verify_environment(os.getcwd())
        if not ok:
            click.echo(
                "⚠️  SEAL_V2 WARNING: Environment hash mismatch. "
                "Code has changed since last seal. "
                "Run 'helen seal-v2' to re-pin. Continuing in unsealed mode."
            )
        return ok
    except Exception as e:
        click.echo(f"⚠️  Boot check error (non-fatal): {e}")
        return False


# ─── CLI root ─────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.2.0", prog_name="HELEN OS")
def main():
    """HELEN OS — Cognitive OS and Governance Kernel. Append-only. Forever."""
    _boot_check()   # warn-only, never exits


# ─── helen talk ───────────────────────────────────────────────────────────────

@main.command()
@click.argument("message", required=False)
@click.option("--ledger", default=None, help="Override ledger path (use ':memory:' for ephemeral)")
@click.option("--reply", is_flag=True, default=False,
              help="Call LLM adapter and print HELEN's reply after the receipt.")
@click.option("--no-receipt", "no_receipt", is_flag=True, default=False,
              help="Suppress receipt output. Useful with --reply for clean text output.")
@click.option("--hal", is_flag=True, default=False,
              help="Two-channel mode. Requires --reply. Prompts LLM in [HER]/[HAL] format, "
                   "validates T-TWO-1–T-TWO-5, prints HALVerdict JSON. "
                   "BLOCK appends BLOCK_RECEIPT_V1 only; PASS/WARN append normal receipt.")
def talk(message, ledger, reply, no_receipt, hal):
    """Kernel-only receipt chain. Add --reply for LLM responses, --hal for two-channel enforcement."""
    from .kernel import GovernanceVM

    if ledger and ledger == ":memory:":
        kern = GovernanceVM(ledger_path=":memory:")
    elif ledger:
        kern = GovernanceVM(ledger_path=ledger)
    else:
        kern = _get_kernel()

    def _llm_reply(prompt: str) -> str:
        """Call the LLM adapter. Returns reply text or an error string."""
        try:
            adapter = _get_adapter()
            return adapter.generate(prompt, [])
        except Exception as exc:
            hint = (
                "\n💡 Tip: start Ollama with `ollama serve`"
                " or set adapter.type: openai in config.yaml"
            )
            return f"⚠️  LLM adapter error: {exc}{hint}"

    def _hal_reply(user_message: str, receipt_cum_hash: str) -> None:
        """
        Two-channel enforcement: call LLM with [HER]/[HAL] prompt, parse + validate.
        Prints HER block, then HALVerdict JSON. BLOCK appends BLOCK_RECEIPT_V1 to ledger.
        """
        from .meta.two_block_parser import parse_two_block, build_hal_prompt, TwoBlockParseError
        prompt = build_hal_prompt(user_message)
        raw    = _llm_reply(prompt)

        click.echo("\n" + "─" * 60)
        try:
            tb = parse_two_block(raw)
        except TwoBlockParseError as exc:
            click.echo(f"⚠️  [HAL] two-block parse error ({exc.violation_code}): {exc}")
            click.echo(f"   Raw output: {raw[:200]!r}...")
            # Fail-closed: append a BLOCK receipt for parse failure
            kern.propose({
                "type": "BLOCK_RECEIPT_V1",
                "reason": f"two_block_parse_error:{exc.violation_code}",
                "cum_hash_ref": receipt_cum_hash[:16],
            })
            click.echo("   → BLOCK_RECEIPT_V1 appended (parse failure).")
            return

        click.echo(f"[HER] kind={tb.her.output_type.value}")
        click.echo(f"  {tb.her.content}")
        click.echo()
        click.echo("[HAL]")
        click.echo(tb.hal.to_json())
        if not tb.binding_verified:
            click.echo("  ⚠️  Binding not verified (COMPUTE_ME placeholder in certificates).")

        # Channel A policy
        if tb.hal.verdict.value == "BLOCK":
            kern.propose({
                "type":         "BLOCK_RECEIPT_V1",
                "audited_hash": tb.her_block_hash[:16],
                "fixes":        tb.hal.required_fixes[:3],
            })
            click.echo("  → BLOCK_RECEIPT_V1 appended to ledger (no decision objects).")
        else:
            verdict_label = tb.hal.verdict.value
            kern.propose({
                "type":         "HAL_VERDICT_RECEIPT_V1",
                "verdict":      verdict_label,
                "audited_hash": tb.her_block_hash[:16],
            })
            click.echo(f"  → HAL_VERDICT_RECEIPT_V1 ({verdict_label}) appended.")
        click.echo("─" * 60 + "\n")

    if message:
        receipt = kern.propose({"type": "user_query", "text": message})
        if not no_receipt:
            click.echo(f"\n📝 Receipt: {receipt.id}")
            click.echo(f"💾 cum_hash: {receipt.cum_hash[:32]}...")
            click.echo(f"⏱️  {receipt.timestamp}\n")
        if hal and reply:
            _hal_reply(message, receipt.cum_hash)
        elif hal and not reply:
            click.echo("⚠️  --hal requires --reply. Add --reply to enable LLM two-channel mode.")
        elif reply:
            click.echo(_llm_reply(message))
        return

    # ── Interactive REPL ──────────────────────────────────────────────────────
    if hal:
        mode_label = "two-channel HER/HAL"
    elif reply:
        mode_label = "receipt + LLM"
    else:
        mode_label = "receipt-only"

    click.echo("\n" + "=" * 60)
    click.echo(f"🧠 HELEN OS — Governance Kernel ({mode_label} mode)")
    click.echo("=" * 60)
    click.echo(f"Ledger: {kern.ledger_path}")
    click.echo(f"Domain: HELEN_CUM_V1::")
    if hal:
        click.echo("Mode:   [HER]/[HAL] two-block enforcement active")
        if not reply:
            click.echo("⚠️  --hal requires --reply for LLM calls.")
    elif reply:
        click.echo("LLM:    adapter active (receipts + HELEN replies)")
    click.echo("Type 'exit' or 'quit' to end.\n")

    seq = 1
    while True:
        try:
            user_input = click.prompt("You")
            if user_input.lower() in ["exit", "quit"]:
                click.echo("\n✅ Session closed.\n")
                break

            receipt = kern.propose({"type": "user_query", "text": user_input, "seq": seq})
            seq += 1
            if not no_receipt:
                click.echo(f"\n  📝 {receipt.id}")
                click.echo(f"  💾 {receipt.cum_hash[:32]}...")
            if hal and reply:
                _hal_reply(user_input, receipt.cum_hash)
            elif reply:
                click.echo(f"\nHELEN: {_llm_reply(user_input)}")
            click.echo()

        except (PermissionError, EOFError) as e:
            click.echo(f"\n🔴 {e}\n")
            break
        except KeyboardInterrupt:
            click.echo("\n\n✅ Session interrupted.\n")
            break


# ─── helen chat ───────────────────────────────────────────────────────────────

@main.command()
@click.option("--location", default="San Francisco")
@click.option("--district", default="oracle_town")
@click.option("--street", default="marketing")
@click.argument("message", required=False)
def chat(location, district, street, message):
    """Full pipeline: HELEN + LLM adapter + agent stack."""
    helen = _get_helen()
    helen.location = location
    helen.current_district = district
    helen.current_street = street

    if message:
        click.echo(helen.speak(message))
        return

    click.echo(f"\n🌐 HELEN OS Chat  [district:{district} | street:{street}]")
    click.echo("Type 'exit' to quit.\n")
    while True:
        try:
            user_input = click.prompt("You")
            if user_input.lower() in ["exit", "quit"]:
                break
            click.echo(f"\n{helen.speak(user_input)}\n")
        except KeyboardInterrupt:
            break


# ─── helen run ────────────────────────────────────────────────────────────────

@main.command()
@click.argument("task_desc")
@click.option("--location", default="San Francisco")
@click.option("--district", default="oracle_town")
@click.option("--street", default="marketing")
def run(task_desc, location, district, street):
    """Run a task through Planner→Worker→Critic→Archivist."""
    helen = _get_helen()
    helen.location = location
    helen.current_district = district
    helen.current_street = street

    click.echo(f"\n🌀 Task: {task_desc}\n")
    results = helen.run_task(task_desc)

    if results.get("status") == "idempotent_hit":
        click.echo(f"♻️  Idempotent hit: {results['message']}")
        return

    verdict = results.get("hal_telemetry", results.get("hal_verdict", {}))
    v_label = verdict.get("verdict", "UNKNOWN")
    emoji = "🟢" if v_label != "BLOCK" else "🔴"

    click.echo(f"📜 Plan:   {results['plan']}")
    click.echo(f"{emoji} HAL:    {v_label}")
    if v_label == "BLOCK":
        click.echo(f"   Reasons: {', '.join(verdict.get('reasons', []))}")
    else:
        r = results["receipt"]
        click.echo(f"📝 Receipt: {r.id}")
        click.echo(f"💾 Hash:    {r.cum_hash[:32]}...")
        click.echo(f"\n{results['artifact'][:300]}...")


# ─── helen seal / seal-v2 ─────────────────────────────────────────────────────

@main.command()
def seal():
    """Seal the sovereign ledger (v1 — no env pinning)."""
    try:
        receipt = _get_kernel().propose({"type": "SEAL", "content": "Ledger closed by user."})
        click.echo(f"✅ Ledger SEALED. Receipt: {receipt.id}")
        click.echo(f"   Final cum_hash: {receipt.cum_hash}")
    except PermissionError as e:
        click.echo(f"🔴 {e}")


@main.command("seal-v2")
def seal_v2():
    """Seal the sovereign ledger (v2 — with environment hash pinning)."""
    try:
        from .tools.boot_verify import BootVerifier
        verifier = BootVerifier(os.getcwd())
        env_hash = verifier.compute_env_bundle_hash()
        payload = {
            "type": "SEAL_V2",
            "content": "Ledger closed with environment pinning.",
            "env_hash": env_hash,
            "monitored_files": verifier.monitored_files,
        }
        receipt = _get_kernel().propose(payload)
        click.echo(f"🛡️  Ledger SEALED (V2). Receipt: {receipt.id}")
        click.echo(f"   Pinned env_hash: {env_hash}")
        click.echo(f"   Final cum_hash:  {receipt.cum_hash}")
    except PermissionError as e:
        click.echo(f"🔴 {e}")


# ─── helen mem ────────────────────────────────────────────────────────────────

@main.group()
def mem():
    """Memory Kernel operations."""
    pass


@mem.command(name="add")
@click.argument("type")
@click.argument("content")
def mem_add(type, content):
    """Add an observed fact to memory (non-sovereign)."""
    _get_memory().add_fact(key=f"cli_{type}", value=content, actor="system", status="OBSERVED")
    click.echo(f"✅ Fact added (key=cli_{type}).")


@mem.command(name="search")
@click.argument("query")
def mem_search(query):
    """Search facts in memory."""
    results = _get_memory().search_facts(query)
    if not results:
        click.echo("No matches found.")
        return
    for r in results:
        click.echo(f"[{r['timestamp']}] {r['content']}")


# ─── helen seed ───────────────────────────────────────────────────────────────

@main.group()
def seed():
    """Seed World operations. CONQUEST LAND and other simulation worlds."""
    pass


@seed.command(name="list")
def seed_list():
    """List registered seed worlds."""
    from .seeds.loader import SeedWorldLoader
    worlds = SeedWorldLoader.list_worlds()
    if not worlds:
        click.echo("No seed worlds registered.")
        return
    for w in worlds:
        click.echo(f"  {w['id']:20s}  {w['version']:8s}  {w['description']}")


@seed.command(name="run")
@click.argument("world_id")
@click.option("--ticks", default=10, help="Number of simulation ticks.")
@click.option("--seed-value", default=42, help="World PRF seed.")
@click.option("--output", default=None, help="Output NDJSON path for receipts.")
@click.option("--live-kernel", is_flag=True, default=False,
              help="Propose into sovereign ledger (requires unsealed ledger).")
def seed_run(world_id, ticks, seed_value, output, live_kernel):
    """Run a seed world simulation (ephemeral :memory: kernel by default).

    Seed worlds are non-sovereign simulations. By default they use an
    ephemeral :memory: kernel so they never touch the sealed sovereign ledger.
    Pass --live-kernel to propose into the real sovereign ledger (requires unsealed).
    """
    from .seeds.loader import SeedWorldLoader
    from .kernel import GovernanceVM

    if live_kernel:
        kernel = _get_kernel()
        click.echo(f"⚠️  Live kernel mode — proposals enter sovereign ledger.")
    else:
        # Ephemeral simulation kernel — never touches the sovereign ledger
        kernel = GovernanceVM(ledger_path=":memory:")

    click.echo(f"\n🌱 Loading seed world: {world_id} (seed={seed_value}, ticks={ticks})")
    try:
        world = SeedWorldLoader.load(world_id, kernel=kernel, world_seed=seed_value)
    except KeyError:
        click.echo(f"🔴 Unknown world: {world_id}. Run 'helen seed list' to see available worlds.")
        return

    receipts = []
    for t in range(ticks):
        tick_receipts = world.tick(t)
        receipts.extend(tick_receipts)
        if tick_receipts:
            click.echo(f"  t={t:03d}  +{len(tick_receipts)} receipt(s)")

    click.echo(f"\n✅ Simulation complete. {len(receipts)} total receipt(s) emitted.")

    if output:
        import json
        os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
        with open(output, "w") as f:
            for r in receipts:
                f.write(json.dumps(r) + "\n")
        click.echo(f"📄 Receipts written to {output}")


# ─── helen self-model ─────────────────────────────────────────────────────────

@main.group("self-model")
def self_model():
    """EPOCH1 self-model: introspect and verify kernel capability contract."""
    pass


@self_model.command(name="run")
@click.option("--save", default=None, help="Save finalized artifact to path.")
def self_model_run(save):
    """Run S1/S2/S3 tests and produce META_SELF_MODEL_V1 verdict."""
    from .meta.self_model import run_self_model_tests, EPOCH1_INSCRIPTION
    from .kernel import GovernanceVM

    kernel = _get_kernel()
    click.echo(f"\n🧠 Running EPOCH1 self-model tests...")
    click.echo(f"   {EPOCH1_INSCRIPTION}\n")

    model = run_self_model_tests(
        kernel=kernel,
        kernel_factory=lambda: GovernanceVM(ledger_path=":memory:"),
        cwd=os.getcwd(),
    )

    for t in model.tests:
        icon = "✅" if t.passed else "❌"
        click.echo(f"  {icon} {t.id}: {t.name}")

    click.echo()
    verdict_icon = "✅" if model.verdict == "PASS" else "❌"
    click.echo(f"{verdict_icon} VERDICT: {model.verdict}")
    click.echo(f"   Inscription: {model.inscription}")

    if save:
        sha = model.save(save)
        click.echo(f"\n📄 Saved: {save}")
        click.echo(f"   SHA256: {sha}")


@self_model.command(name="show")
@click.argument("path", default="artifacts/META_SELF_MODEL_V1_EPOCH1.json")
def self_model_show(path):
    """Show a saved META_SELF_MODEL_V1 artifact and verify it."""
    from .meta.self_model import SelfModel
    try:
        model = SelfModel.load(path)
        valid, errors = model.verify()
        click.echo(f"\n📋 {path}")
        click.echo(f"   Epoch:    {model.epoch}")
        click.echo(f"   Verdict:  {model.verdict}")
        click.echo(f"   Valid:    {'✅' if valid else '❌'}")
        if errors:
            for e in errors:
                click.echo(f"   ⚠️  {e}")
    except FileNotFoundError:
        click.echo(f"🔴 Not found: {path}. Run 'helen self-model run --save {path}' first.")


# ─── helen epoch ──────────────────────────────────────────────────────────────

@main.group()
def epoch():
    """EPOCH management — mark, verify, and show epoch anchors."""
    pass


@epoch.command(name="mark")
@click.option("--epoch-name", default="EPOCH1", help="Epoch identifier.")
@click.option("--out", default="artifacts/EPOCH_MARK_V1_EPOCH1.json",
              help="Output artifact path.")
@click.option("--files", default=None, multiple=True,
              help="Extra files to hash into the mark (path:alias pairs).")
def epoch_mark(epoch_name, out, files):
    """
    Inscribe an EPOCH_MARK_V1 anchor with content-addressed hashes + receipt.

    Pattern A (watertight):
      1. Hash all content files → content_hashes flat map.
      2. manifest_sha256 = SHA256(canonical_json(content_hashes))  [root-of-roots].
      3. Build mark dict (no artifact_sha256 yet).
      4. artifact_sha256 = SHA256(canonical_json(mark_WITHOUT_field))  [Pattern A].
      5. Embed artifact_sha256 + scheme into mark.

    Any auditor can verify by: strip field → canonical_json → SHA256 → compare.
    """
    import hashlib, json
    from pathlib import Path
    from datetime import datetime, timezone
    from .kernel import GovernanceVM
    from .meta.canonical import (
        embed_artifact_sha256,
        compute_manifest_sha256,
    )

    def sha256f(path):
        p = Path(path)
        return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else f"MISSING:{path}"

    click.echo(f"\n🔖 Building {epoch_name} mark (Pattern A — canonical SHA256)...")

    # Standard EPOCH1 files (always included)
    standard_modules = {
        "meta_self_model":    "helen_os/meta/self_model.py",
        "meta_wild_policy":   "helen_os/meta/wild_policy.py",
        "meta_transmutation": "helen_os/meta/transmutation.py",
        "meta_canonical":     "helen_os/meta/canonical.py",
        "seeds_conquest_land":"helen_os/seeds/worlds/conquest_land.py",
        "seeds_wild_town":    "helen_os/seeds/worlds/wild_town.py",
    }
    standard_tests = {
        "EPOCH1_S1":    "tests/test_epoch1_s1_fail_closed.py",
        "EPOCH1_S2":    "tests/test_epoch1_s2_introspection.py",
        "EPOCH1_S3":    "tests/test_epoch1_s3_loop_receipt.py",
        "WILD_T1":      "tests/test_wild_town_t1_no_ship.py",
        "WILD_T2":      "tests/test_wild_town_t2_transmutation.py",
        "WILD_T3":      "tests/test_wild_town_t3_hal_boundary.py",
        "CANONICAL_C":  "tests/test_canonical_sha256.py",
    }
    standard_artifacts = {
        "META_SELF_MODEL_V1_EPOCH1": "artifacts/META_SELF_MODEL_V1_EPOCH1.json",
        "META_SELF_MODEL_V1_LIVE":   "artifacts/META_SELF_MODEL_V1_LIVE.json",
    }

    # Parse extra files
    extra = {}
    for fspec in (files or []):
        if ":" in fspec:
            path, alias = fspec.split(":", 1)
        else:
            path = fspec
            alias = Path(fspec).stem
        extra[alias] = fspec

    # Build content hash maps (structured: path + sha256)
    module_hashes   = {k: {"path": v, "sha256": sha256f(v)} for k, v in standard_modules.items()}
    module_hashes.update({k: {"path": v, "sha256": sha256f(v)} for k, v in extra.items()})
    test_hashes     = {k: {"path": v, "sha256": sha256f(v)} for k, v in standard_tests.items()}
    artifact_hashes = {k: {"path": v, "sha256": sha256f(v)} for k, v in standard_artifacts.items()}

    # Build flat content_hashes map: alias → sha256  (for manifest_sha256)
    content_hashes: dict = {}
    for alias, entry in {**module_hashes, **test_hashes, **artifact_hashes}.items():
        content_hashes[alias] = entry["sha256"]

    # manifest_sha256 = SHA256(canonical_json(content_hashes))  — root-of-roots
    manifest_sha = compute_manifest_sha256(content_hashes)
    total_files = len(content_hashes)

    # Emit canonical epoch receipt via :memory: kernel
    km = GovernanceVM(ledger_path=":memory:")
    receipt = km.propose({
        "type": "EPOCH_MARK_V1",
        "epoch": epoch_name,
        "name": "SELF_MODEL_ONLINE",
        "file_count": total_files,
        "manifest_sha256": manifest_sha,
    })

    # Build mark dict — NO artifact_sha256 or artifact_sha256_scheme yet.
    # embed_artifact_sha256 adds both fields AFTER hashing, so strip/re-hash works cleanly.
    mark = {
        "type": "EPOCH_MARK_V1",
        "epoch": epoch_name,
        "name": "SELF_MODEL_ONLINE",
        "inscription": (
            f"{epoch_name}: SELF_MODEL_ONLINE — invariants introspectable + enforced; "
            "agent loop mediated by receipts; sealing defines mutation boundary."
        ),
        "wild_town_inscription": (
            "ORACLE CREATIVE WILD TOWN: creativity allowed + execution impossible by construction. "
            "Ledger stores blocks, not wild ideas. HELEN observes the boundary — never commanded."
        ),
        "artifacts": artifact_hashes,
        "modules": module_hashes,
        "tests": test_hashes,
        "content_hashes": content_hashes,
        "manifest_sha256": manifest_sha,
        "manifest_sha256_scheme": "SHA256(canonical_json(content_hashes))",
        "epoch_receipt": {
            "receipt_id": receipt.id,
            "payload_hash": receipt.payload_hash,
            "cum_hash": receipt.cum_hash,
            "timestamp": receipt.timestamp,
            "kernel_mode": ":memory: (ephemeral — canonical epoch anchor)",
            "receipt_role": "canonical_epoch_anchor",
        },
        "verdict": "PASS",
        "marked_at": datetime.now(timezone.utc).isoformat(),
        "hash_law": "CWL_CANONICAL_V1",
    }

    # Pattern A: embed_artifact_sha256 — hash WITHOUT field, then embed
    mark_sealed = embed_artifact_sha256(mark)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(mark_sealed, indent=2))

    click.echo(f"\n📌 {epoch_name} mark inscribed (Pattern A — watertight).")
    click.echo(f"   Receipt:           {receipt.id}")
    click.echo(f"   Receipt hash:      {receipt.cum_hash[:32]}...")
    click.echo(f"   manifest_sha256:   {manifest_sha[:32]}...")
    click.echo(f"   artifact_sha256:   {mark_sealed['artifact_sha256'][:32]}...")
    click.echo(f"   Files hashed:      {total_files} ({len(module_hashes)} modules, "
               f"{len(test_hashes)} tests, {len(artifact_hashes)} artifacts)")
    click.echo(f"\n💾 Saved → {out}")
    click.echo(f"\n🔖 Inscription:\n   {mark['inscription']}")


@epoch.command(name="status")
@click.option("--mark-path", default="artifacts/EPOCH_MARK_V1_EPOCH1.json",
              help="Path to the EPOCH_MARK_V1 artifact.")
def epoch_status(mark_path):
    """
    Show and verify an EPOCH_MARK_V1 anchor artifact.

    Three-layer verification:
      1. Content hashes — re-hash each file, compare to stored sha256.
      2. manifest_sha256 — SHA256(canonical_json(content_hashes)).
      3. artifact_sha256 — Pattern A: strip field, canonical_json, SHA256, compare.
    """
    import hashlib, json
    from pathlib import Path
    from .meta.canonical import verify_artifact_sha256, verify_manifest_sha256

    p = Path(mark_path)
    if not p.exists():
        click.echo(f"🔴 Not found: {mark_path}. Run 'helen epoch mark' first.")
        return

    mark = json.loads(p.read_text())

    # ── Layer 1: Re-hash each content file ───────────────────────────────────
    missing = []
    mismatch = []
    ok_count = 0

    all_entries = {}
    all_entries.update(mark.get("modules", {}))
    all_entries.update(mark.get("tests", {}))
    all_entries.update(mark.get("artifacts", {}))

    for name, entry in all_entries.items():
        path = entry.get("path", "")
        expected = entry.get("sha256", "")
        fp = Path(path)
        if not fp.exists():
            missing.append(path)
        else:
            actual = hashlib.sha256(fp.read_bytes()).hexdigest()
            if actual != expected:
                mismatch.append(f"{path}: actual={actual[:8]}... ≠ stored={expected[:8]}...")
            else:
                ok_count += 1

    # ── Layer 2: manifest_sha256 verification ─────────────────────────────────
    content_hashes = mark.get("content_hashes", {})
    stored_manifest = mark.get("manifest_sha256", "")
    if content_hashes and stored_manifest:
        manifest_valid, manifest_reason = verify_manifest_sha256(stored_manifest, content_hashes)
    else:
        manifest_valid, manifest_reason = False, "content_hashes or manifest_sha256 missing (old format)"

    # ── Layer 3: artifact_sha256 Pattern A verification ───────────────────────
    if mark.get("artifact_sha256"):
        artifact_valid, artifact_reason = verify_artifact_sha256(mark)
    else:
        artifact_valid, artifact_reason = False, "artifact_sha256 field missing"

    # ── Output ────────────────────────────────────────────────────────────────
    click.echo(f"\n🔖 EPOCH MARK: {mark_path}")
    click.echo(f"   Epoch:         {mark.get('epoch', '?')}")
    click.echo(f"   Name:          {mark.get('name', '?')}")
    click.echo(f"   Verdict:       {mark.get('verdict', '?')}")
    click.echo(f"   Marked at:     {mark.get('marked_at', '?')}")
    click.echo(f"   Receipt:       {mark.get('epoch_receipt', {}).get('receipt_id', '?')}")
    click.echo(f"   Hash law:      {mark.get('hash_law', 'CWL_TRACE_V1 (legacy)')}")
    click.echo(f"   Files OK:      {ok_count}/{len(all_entries)}")

    # manifest_sha256 status
    m_icon = "✅" if manifest_valid else "🔴"
    click.echo(f"   manifest_sha256: {m_icon} {manifest_reason[:60]}")

    # artifact_sha256 status
    a_icon = "✅" if artifact_valid else "🔴"
    click.echo(f"   artifact_sha256: {a_icon} {artifact_reason[:60]}")

    if missing:
        click.echo(f"\n⚠️  Missing files ({len(missing)}):")
        for m in missing:
            click.echo(f"   🔴 {m}")
    if mismatch:
        click.echo(f"\n⚠️  Hash mismatches ({len(mismatch)}) — files changed since mark:")
        for m in mismatch:
            click.echo(f"   ⚡ {m}")

    all_ok = (not missing and not mismatch and manifest_valid and artifact_valid)
    if all_ok:
        click.echo(f"\n✅ All {ok_count} content hashes verified — manifest verified — "
                   f"artifact_sha256 verified (Pattern A). Epoch mark is watertight.")
    else:
        click.echo(f"\n⚠️  Epoch mark has issues. Re-run 'helen epoch mark' to rebuild.")

    click.echo(f"\n📜 {mark.get('inscription', '')}")


# ─── helen epoch learn ────────────────────────────────────────────────────────

@epoch.group(name="learn")
def epoch_learn():
    """EPOCH2 learning loop — Conquest Land invariant discovery."""
    pass


@epoch_learn.command(name="run")
@click.option("--seed", default=42, help="World PRF seed (default: 42).")
@click.option("--ticks", default=20, help="Number of sim ticks (default: 20).")
@click.option("--out", default="artifacts/EPOCH2_RUN_V1.json",
              help="Output artifact path.")
@click.option("--no-save", is_flag=True, default=False,
              help="Dry-run: print results without saving artifact.")
def epoch_learn_run(seed, ticks, out, no_save):
    """
    Run the EPOCH2 canonical learning loop (Steps A–E + Town Birth).

    Executes:
      A. Three pre-written hypotheses (H1, H2, H3)
      B. Deterministic CONQUEST LAND sim (seed, ticks)
      C. Extract 5 instrumented metrics
      D. Sigma gate across seed set [42, 7, 99]
      E. Inscribe LAW_V1 entries for passing hypotheses
      +  TOWN_BIRTH_PREDICATE_V1 evaluated for all 10 factions

    All computation is non-sovereign (:memory: kernel) unless --out is used.
    Artifact written with Pattern A canonical SHA256.
    """
    import json
    from pathlib import Path
    from .epoch2.run_epoch2 import run_epoch2_canonical
    from .meta.canonical import embed_artifact_sha256

    click.echo(f"\n🧪 EPOCH2 LEARNING LOOP — seed={seed}, ticks={ticks}")
    click.echo("=" * 60)
    click.echo("  Step A: Hypotheses (H1, H2, H3)")
    click.echo("  Step B: CONQUEST LAND sim")
    click.echo("  Step C: Extract 5 metrics")
    click.echo("  Step D: Sigma gate [42, 7, 99]")
    click.echo("  Step E: Inscribe LAW_V1 for passing hypotheses")
    click.echo("  +       TOWN_BIRTH_PREDICATE_V1 (all 10 factions)")
    click.echo("=" * 60)

    result = run_epoch2_canonical(seed=seed, ticks=ticks, ledger_path=":memory:")

    # ── Metrics summary ───────────────────────────────────────────────────────
    m = result.metrics
    click.echo(f"\n📊 METRICS (seed={seed}, ticks={ticks})")
    click.echo(f"   admissibility_rate:     {m.admissibility_rate:.4f}")
    click.echo(f"   dispute_heat:           {m.dispute_heat:.4f}")
    click.echo(f"   closure_success:        {'✅ True' if m.closure_success else '❌ False'}")
    click.echo(f"   sovereignty_drift_index:{m.sovereignty_drift_index:.4f}")
    click.echo(f"   witness_integrity:      {m.witness_integrity}")

    # ── Sigma gate + laws ─────────────────────────────────────────────────────
    click.echo(f"\n⚖️  SIGMA GATE + LAWS")
    for sg in result.sigma_results:
        verdict_icon = "✅" if sg["verdict"] == "PASS" else "❌"
        click.echo(f"   {verdict_icon} {sg['metric_name']:28s}  threshold={sg['threshold']}  "
                   f"{sg['verdict']}")
        for seed_str, val in sg["metric_values"].items():
            click.echo(f"       seed={seed_str}: {val:.6f}")

    click.echo(f"\n   Laws inscribed: {len(result.laws_inscribed)}/3")
    for law in result.laws_inscribed:
        click.echo(f"   📜 {law['metric']:28s}: {law['law_text'][:60]}...")

    # ── Town birth ────────────────────────────────────────────────────────────
    eligible = [tb for tb in result.town_birth_results if tb.get("eligible")]
    click.echo(f"\n🏛️  TOWN BIRTH PREDICATE (10 factions)")
    click.echo(f"   Eligible: {len(eligible)}/10 (expected: 0 in v0.1.0 world)")
    for tb in result.town_birth_results:
        e_icon = "✅" if tb.get("eligible") else "○"
        click.echo(f"   {e_icon} {tb['faction_id']}: receipts={tb['receipt_count']}, "
                   f"treaty={tb['treaty_signature']}, closure={tb['closure_proof']}")

    # ── Final stats ───────────────────────────────────────────────────────────
    click.echo(f"\n🔐 KERNEL")
    click.echo(f"   cum_hash:       {result.kernel_cum_hash[:32]}...")
    click.echo(f"   receipts count: {result.run_receipts_count}")
    click.echo(f"   run_at:         {result.run_at}")

    if no_save:
        click.echo(f"\n  (--no-save: artifact not written)")
        return

    # ── Write artifact (Pattern A) ────────────────────────────────────────────
    artifact = result.to_artifact()
    artifact_sealed = embed_artifact_sha256(artifact)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(artifact_sealed, indent=2))

    click.echo(f"\n💾 Saved → {out}")
    click.echo(f"   artifact_sha256: {artifact_sealed['artifact_sha256'][:32]}...")
    click.echo(f"\n✅ EPOCH2 complete — {len(result.laws_inscribed)} laws inscribed, "
               f"closure_success={result.metrics.closure_success}")


@epoch_learn.command(name="status")
@click.option("--path", default="artifacts/EPOCH2_RUN_V1.json",
              help="Path to EPOCH2_RUN_V1 artifact.")
def epoch_learn_status(path):
    """
    Show and verify an EPOCH2_RUN_V1 artifact.

    Verifies artifact_sha256 Pattern A (strip → canonical_json → SHA256 → compare).
    """
    import json
    from pathlib import Path
    from .meta.canonical import verify_artifact_sha256

    p = Path(path)
    if not p.exists():
        click.echo(f"🔴 Not found: {path}. Run 'helen epoch learn run' first.")
        return

    artifact = json.loads(p.read_text())

    # Pattern A verification
    if artifact.get("artifact_sha256"):
        art_valid, art_reason = verify_artifact_sha256(artifact)
    else:
        art_valid, art_reason = False, "artifact_sha256 field missing"

    art_icon = "✅" if art_valid else "🔴"

    click.echo(f"\n🧪 EPOCH2 RUN ARTIFACT: {path}")
    click.echo(f"   Type:              {artifact.get('type', '?')}")
    click.echo(f"   Seed:              {artifact.get('seed', '?')}")
    click.echo(f"   Ticks:             {artifact.get('ticks', '?')}")
    click.echo(f"   Run at:            {artifact.get('run_at', '?')}")
    click.echo(f"   artifact_sha256:   {art_icon} {art_reason[:60]}")

    # Metrics
    m = artifact.get("metrics", {})
    click.echo(f"\n📊 METRICS")
    click.echo(f"   admissibility_rate:     {m.get('admissibility_rate', '?'):.4f}" if isinstance(m.get('admissibility_rate'), float) else f"   admissibility_rate:     {m.get('admissibility_rate', '?')}")
    click.echo(f"   closure_success:        {'✅ True' if m.get('closure_success') else '❌ False'}")
    click.echo(f"   sovereignty_drift_index:{m.get('sovereignty_drift_index', '?')}")
    click.echo(f"   dispute_heat:           {m.get('dispute_heat', '?')}")

    # Laws
    laws = artifact.get("laws_inscribed", [])
    click.echo(f"\n📜 LAWS INSCRIBED: {len(laws)}/3")
    for law in laws:
        click.echo(f"   ✅ {law.get('metric', '?'):28s}: {law.get('law_text', '')[:60]}...")

    # Sigma results
    sigmas = artifact.get("sigma_results", [])
    click.echo(f"\n⚖️  SIGMA RESULTS")
    for sg in sigmas:
        v_icon = "✅" if sg.get("verdict") == "PASS" else "❌"
        click.echo(f"   {v_icon} {sg.get('metric_name', '?'):28s}  threshold={sg.get('threshold', '?')}  {sg.get('verdict', '?')}")

    # Town birth summary
    town_births = artifact.get("town_birth_results", [])
    eligible_count = sum(1 for tb in town_births if tb.get("eligible"))
    click.echo(f"\n🏛️  TOWN BIRTH: {eligible_count}/{len(town_births)} eligible")

    # Kernel
    click.echo(f"\n🔐 kernel_cum_hash: {artifact.get('kernel_cum_hash', '?')[:32]}...")
    click.echo(f"   receipts_count:  {artifact.get('run_receipts_count', '?')}")

    if art_valid:
        click.echo(f"\n✅ EPOCH2 artifact integrity verified (Pattern A).")
    else:
        click.echo(f"\n⚠️  Integrity issue: {art_reason}")


# ─── helen airi ───────────────────────────────────────────────────────────────

@main.group()
def airi():
    """AIRI avatar integration."""
    pass


@airi.command(name="connect")
@click.option("--uri", default="ws://localhost:6121/ws")
@click.option("--log-level", default="INFO")
def airi_connect(uri, log_level):
    """Connect HELEN to AIRI avatar runtime (firewall-grade bridge)."""
    import asyncio
    from .integrations.airi_bridge import main as bridge_main
    from .router import set_helen_instance
    set_helen_instance(_get_helen())
    click.echo(f"🔌 Connecting to AIRI at {uri}")
    try:
        asyncio.run(bridge_main(airi_uri=uri, log_level=log_level))
    except KeyboardInterrupt:
        click.echo("\n🛑 AIRI bridge stopped.")


# ─── helen status ─────────────────────────────────────────────────────────────

@main.command()
def status():
    """Show current HELEN OS kernel status and configuration."""
    cfg = _load_config()
    kernel = _get_kernel()
    adapter_type = cfg.get("adapter", {}).get("type", "ollama")

    click.echo("\n" + "=" * 60)
    click.echo("🧠 HELEN OS — Status")
    click.echo("=" * 60)
    click.echo(f"  Adapter:      {adapter_type}")
    click.echo(f"  Ledger:       {kernel.ledger_path}")
    click.echo(f"  Cum hash:     {kernel.cum_hash[:32]}...")
    click.echo(f"  Sealed:       {kernel.sealed}")
    click.echo(f"  Env pinned:   {bool(kernel.pinned_env_hash)}")
    if kernel.pinned_env_hash:
        click.echo(f"  Pinned hash:  {kernel.pinned_env_hash[:32]}...")
    seal_ok = kernel.verify_environment(os.getcwd())
    click.echo(f"  Seal check:   {'✅ PASS' if seal_ok else '⚠️  MISMATCH (run seal-v2)'}")
    click.echo("=" * 60 + "\n")


if __name__ == "__main__":
    main()

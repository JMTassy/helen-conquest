# Oracle Town Map (Mermaid)

## Town Structure (System Dependencies)

```mermaid
graph TD
    A["🧱 CITY WALL<br/>Fail-Closed K1"] -->|guards| B["🚪 TOWN GATE<br/>town-check.sh"]

    B -->|checks| C["DOCS DISTRICT<br/>generator.py<br/>CLAUDE_MD indices"]
    B -->|validates| D["GOVERNANCE DISTRICT<br/>policy.json<br/>Mayor RSM<br/>K0-K7 Invariants"]
    B -->|verifies| E["COURT OF EVIDENCE<br/>extract-emulation-evidence.py<br/>5 Breakthroughs"]

    C -->|fresh?| F["✅ Indices Current<br/>or ❌ Stale"]
    D -->|quorum?| G["✅ Policy Valid<br/>or ❌ Soft Language"]
    E -->|evidence?| H["✅ 5/5 Pass<br/>or ❌ Missing"]

    F -->|pass| I["🟢 GATE GREEN"]
    G -->|pass| I
    H -->|pass when TOWN_EVIDENCE=1| I

    I -->|if all pass| J["Generate TOWN_ASCII.generated.txt"]
    I -->|decision ready?| K["📜 DECISION LEDGER<br/>run: runA/runB/runC<br/>policy_hash<br/>decision_digest"]

    K -->|cite| L["🗂 ARCHIVE DISTRICT<br/>runs/runA_*<br/>runs/runB_*<br/>runs/runC_*"]
    K -->|determinism?| M["🔄 REPLAY GROUNDS<br/>replay.py<br/>30 iterations<br/>K5 verified"]

    L -->|store| N["📋 DECISION RECORDS<br/>decision_record.json<br/>briefcase.json<br/>ledger.json<br/>hashes.json"]

    M -->|same digest?| O["✅ K5 Stable<br/>or ❌ Drift Detected"]

    style A fill:#8B4513
    style B fill:#FFD700
    style C fill:#87CEEB
    style D fill:#90EE90
    style E fill:#DDA0DD
    style I fill:#32CD32
    style K fill:#FF6347
    style J fill:#FFB6C1
    style O fill:#32CD32
```

## Daily Workflow

```mermaid
graph LR
    Start["👤 You"] -->|submit claim| Claim["Claim"]
    Claim -->|validate schema| Intake["Intake Guard"]
    Intake -->|parse obligations| Compiler["Claim Compiler"]
    Compiler -->|analyze| Districts["4 Districts<br/>Legal / Tech<br/>Business / Social"]
    Districts -->|score| TownHall["Town Hall<br/>QI-INT v2"]
    TownHall -->|check invariants| Mayor["Mayor RSM<br/>Pure Function"]
    Mayor -->|K0-K7 verification| Decision{"Decision"}
    Decision -->|NO_SHIP| NoShip["❌ NO_SHIP<br/>blocking_reasons"]
    Decision -->|SHIP| Ship["✅ SHIP<br/>receipts signed"]
    NoShip -->|record| Ledger["📜 Append-Only Ledger<br/>decision_record.json<br/>policy_hash pinned"]
    Ship -->|record| Ledger
    Ledger -->|hash| Digest["decision_digest<br/>K5 Stable"]

    style Intake fill:#FFE4B5
    style Mayor fill:#90EE90
    style NoShip fill:#FF6B6B
    style Ship fill:#90EE90
    style Ledger fill:#FF6347
    style Digest fill:#32CD32
```

## Gate Execution (town-check.sh)

```mermaid
sequenceDiagram
    participant User
    participant Gate as town-check.sh
    participant Gen as generate_claude_index.py
    participant Syntax as py_compile
    participant Evidence as extract-emulation-evidence.py
    participant ASCII as generate_town_ascii.py

    User->>Gate: bash scripts/town-check.sh
    Gate->>Gen: Regenerate indices
    Gen-->>Gate: indices.txt written
    Gate->>Gate: Check working-tree diffs
    alt Diffs found
        Gate-->>User: ❌ RED - Indices stale
    else No diffs
        Gate->>Syntax: Validate Python
        alt Syntax error
            Syntax-->>Gate: ERROR
            Gate-->>User: ❌ RED - Syntax error
        else Valid
            alt TOWN_EVIDENCE=1
                Gate->>Evidence: Validate 5 breakthroughs
                Evidence->>Evidence: K3, K4, K5, K7 checks
                alt Evidence fails
                    Evidence-->>Gate: exit 1
                    Gate-->>User: ❌ RED - Evidence invalid
                else Evidence passes
                    Evidence-->>Gate: exit 0 ✅ 5/5
                end
            end
            Gate->>ASCII: Generate TOWN_ASCII.generated.txt
            ASCII-->>Gate: town.txt generated
            Gate-->>User: 🟢 GREEN + ASCII town
        end
    end
```

## Knowledge Base (Bibliothèque) Integration

```mermaid
graph TD
    A["📚 External Knowledge<br/>Math Proofs<br/>Old Code<br/>Research<br/>Data<br/>Logs<br/>Policy"] -->|submit| B["Bibliothèque Intake Gate<br/>scripts/bibliotheque_intake.py"]

    B -->|validate| C{"Format OK?<br/>Security OK?<br/>Structure OK?"}
    C -->|fail| D["❌ REJECTED<br/>WARN or ERROR"]
    C -->|pass| E["✅ ACCEPTED<br/>Hashed SHA256"]

    E -->|store| F["oracle_town/memory/bibliotheque/<br/>type/id/<br/>├ original.*<br/>├ parsed.json<br/>├ digest.sha256<br/>└ metadata.json"]

    F -->|cite in| G["decision_record.json<br/>referenced_knowledge[]"]
    G -->|pin in| H["policy_hash<br/>K7 Policy Pinning"]
    H -->|replay test| I["replay.py<br/>K5 Determinism<br/>30 iterations"]
    I -->|verify| J["decision_digest stable<br/>✅ No drift"]

    style B fill:#DDA0DD
    style E fill:#90EE90
    style J fill:#32CD32
```

## Evidence System (Machine-Validated)

```mermaid
graph TD
    A["🏛 Oracle Town Emulation Evidence"] -->|validates| B["Extract Emulation Evidence<br/>scripts/extract-emulation-evidence.py"]

    B -->|check K3| C["K3 Quorum Breakthrough<br/>decision_record.json<br/>blocking_reasons = missing classes"]
    B -->|check K4| D["K4 Revocation Breakthrough<br/>public_keys.json<br/>Key-2025-12-legal-old revoked"]
    B -->|check K5| E["K5 Determinism Breakthrough<br/>hashes.json<br/>decision_digest stable"]
    B -->|check K7| F["K7 Policy Pinning Breakthrough<br/>policy.json structure<br/>policy_hash recorded"]
    B -->|check reproducibility| G["Reproducibility Breakthrough<br/>All runs replayable<br/>Audit trail complete"]

    C -->|pass/fail| H{"All 5/5<br/>Pass?"}
    D -->|pass/fail| H
    E -->|pass/fail| H
    F -->|pass/fail| H
    G -->|pass/fail| H

    H -->|fail| I["❌ Evidence Invalid<br/>exit 1"]
    H -->|pass| J["✅ All Evidence Valid<br/>exit 0"]

    style J fill:#32CD32
    style I fill:#FF6B6B
```

## Month 1 Iteration Plan

```mermaid
graph LR
    Week1["Week 1<br/>Governance Hardening<br/>Add Privacy District<br/>K3 Quorum Demo"]
    Week2["Week 2<br/>Knowledge Integration<br/>Submit Math Proofs<br/>Submit Old Code<br/>Bibliothèque Intake"]
    Week3["Week 3<br/>Emergence Patterns<br/>Track E1, E4, E5<br/>Instrument Failures<br/>New Rules"]
    Week4["Week 4<br/>Month 1 Summary<br/>Evidence Valid?<br/>Patterns Emerged?<br/>Month 2 Ready"]

    Week1 -->|day 5| Week2
    Week2 -->|day 10| Week3
    Week3 -->|day 15| Week4
    Week4 -->|day 20| Next["Month 2<br/>Larger Governance<br/>Multi-Run Synthesis"]

    style Week1 fill:#FFE4B5
    style Week2 fill:#87CEEB
    style Week3 fill:#DDA0DD
    style Week4 fill:#90EE90
    style Next fill:#FFD700
```

## Reading Navigation

| Goal | Start Here |
|------|-----------|
| **Quick start (5 min)** | QUICK_START_AUTONOMOUS.md |
| **System overview (10 min)** | AUTONOMOUS_MODE_ACTIVATED.md |
| **Full verification** | SYSTEM_READINESS_CHECKLIST.md |
| **Evidence explained** | ORACLE_TOWN_EMULATION_EVIDENCE.md |
| **Month 1 walkthrough** | SCENARIO_NEW_DISTRICT.md |
| **Knowledge base protocol** | oracle_town/memory/BIBLIOTHEQUE_INTAKE.md |
| **Town visual** | TOWN_ASCII.generated.txt (auto-generated) |
| **This session** | SESSION_SUMMARY.md |

## Town Metaphor Explained

- **CITY WALL (K1)** — Fail-closed boundary; no entry without proof
- **TOWN GATE (town-check.sh)** — Guards entrance; verifies indices, syntax, optionally evidence
- **DOCS DISTRICT** — CLAUDE.md, indices, documentation freshness
- **GOVERNANCE DISTRICT** — Policy, Mayor RSM, K0-K7 invariants, quorum rules
- **COURT OF EVIDENCE** — Evidence validators, breakthrough checks, no silent drift
- **DECISION LEDGER** — All decisions recorded, hashed, immutable
- **ARCHIVE DISTRICT** — Historical runs (runA, runB, runC), patterns
- **REPLAY GROUNDS** — Determinism verification, K5 testing, digest stability
- **BIBLIOTHÈQUE** — Knowledge base, external knowledge integration, hashing

All connected through the **gate** which runs automatically and generates the **ASCII town visualization** showing current state.


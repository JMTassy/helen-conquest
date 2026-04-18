# 📚 REGISTRE CANONIQUE — CORSE AI MATIN

## *Inventory of Publications & Manifestations*

---

## 🏛️ ÉDITION 0 : PROTOTYPE (Calvi, 2026-02-01)

### Titre Canonique
**CORSE AI MATIN — La Messaggeria des Terres Souveraines**

### Contenu
- Charte fondatrice (XVII sections)
- Bi-colonne structure définition
- Kill-switch sémantique spécification
- Rituel annuel (Calvi on the Rocks) protocole

### Statut
- ✅ Canonique
- ✅ Non-binding
- ✅ Archivé
- ✅ Signé par Mayors (observation, pas ratification)

### Hash Intégrité
```
sha256:placeholder_prototype_hash_001
Archive: /canon/2026-02-01/CORSE_AI_MATIN_PROTO_v0.md
```

### Signataires (Témoins)
```
Mayor.Calvi    [timestamp] [signature]  -- observe, n'approuve pas
Mayor.Ajaccio  [timestamp] [signature]  -- observe, n'approuve pas
Mayor.Bastia   [timestamp] [signature]  -- observe, n'approuve pas
NPC.Collective [timestamp] [observation]-- témoignage fertile
```

---

## 📰 ÉDITION QUOTIDIENNE (Format)

### Titre
`CORSE AI MATIN — YYYY-MM-DD`

### Structure

```
Header (Non-interprétable)
├─ Date: YYYY-MM-DD
├─ Time: HH:MM UTC
├─ Hash: SHA256 previous day
└─ Towns Publishing: [list]

COLONNE A — 🪨 FAITS
├─ [Town A] — Verdict A1 (timestamp, hash)
├─ [Town B] — Verdict B1 (timestamp, hash)
└─ [Town C] — Verdict C1 (timestamp, hash)

COLONNE B — 🌺 INSIGHTS
├─ [NPC Collective X] — Observation X (WUL notation)
├─ [NPC Collective Y] — Observation Y (WUL notation)
└─ [NPC Collective Z] — Observation Z (WUL notation)

Footer (Archival)
├─ Publication Time: UTC
├─ Integrity Hash: SHA256
├─ Kill-Switch Check: PASS
└─ Next Publication: YYYY-MM-DD HH:MM UTC
```

### Comptage
```
COLONNE A : N verdicts / N towns reporting
COLONNE B : M observations / M NPC collectives
Total: (N + M) items in registry
```

---

## 🗓️ ARCHIVE PAR MOIS

### Format de Dossier

```
/archive/2026/
  /01/
    /calvi_daily_2026-01-01.json       [COLONNE A + B]
    /calvi_daily_2026-01-02.json       [COLONNE A + B]
    ...
    /calvi_daily_2026-01-31.json       [COLONNE A + B]
    /integrity_manifest_2026-01.sha256
    /monthly_seal_2026-01.json         [metadata + hash]
```

### Monthly Seal Structure

```json
{
  "month": "2026-01",
  "total_days": 31,
  "total_a_entries": 847,
  "total_b_entries": 2341,
  "first_publication": "2026-01-01T10:00:00Z",
  "last_publication": "2026-01-31T10:00:00Z",
  "integrity_hash": "sha256:...",
  "previous_month_hash": "sha256:...",
  "publication_status": "SEALED",
  "modifications": "NONE",
  "ritual_seal": "NONE (daily mode)"
}
```

---

## 🎭 ÉDITION ANNUELLE (Calvi on the Rocks)

### Titre Canonique
**CORSE AI MATIN — ANNUAL CODEX 2026**

### Timing
- 📅 Année X : 3 jours en mai/juin (TBD par diffus consensus)
- 🧠 Jour 1 : NPC Insight Zone (pré-claim)
- 🏛️ Jour 2 : Mayor Testimony Circle (post-verdict)
- 📜 Jour 3 : Archive Sealing & Ritual Silence

### Contenu

```
ANNUAL CODEX 2026 — Complete Registry
│
├─ PRÉAMBULE (Non-interprétable)
│  ├─ 365 jours de publications
│  ├─ Totaux annuels (A + B)
│  ├─ Towns participants (N)
│  └─ NPC collectives (M)
│
├─ COLONNE A — COMPLET
│  ├─ Tous les verdicts, 2026-01-01 → 2026-12-31
│  ├─ Tri par : [timestamp UTC]
│  ├─ Filtrage : NONE (100% listings)
│  └─ Archive Hash : SHA256
│
├─ COLONNE B — COMPLET
│  ├─ Toutes les observations, 2026-01-01 → 2026-12-31
│  ├─ Tri par : [timestamp UTC]
│  ├─ Filtrage : NONE (100% listings)
│  └─ Archive Hash : SHA256
│
├─ RITUAL TESTIMONY
│  ├─ Mayor Testimonies (public parole, no binding)
│  ├─ NPC Collective Synthesis (no decision)
│  └─ Unresolved Questions (for next year)
│
├─ STATISTICAL ANNEX (Non-narrative)
│  ├─ Tally A : [N1 SHIP, N2 NO_SHIP, N3 DEFER]
│  ├─ Tally B : [M observations, M types]
│  ├─ Tally Towns : [T1 @N1, T2 @N2, ...]
│  ├─ Tally NPC : [NPC1 @M1, NPC2 @M2, ...]
│  └─ Timeline : daily publication continuity
│
├─ CRYPTOGRAPHIC SEAL
│  ├─ Ritual Hash : SHA256(all 365 days + testimony)
│  ├─ Timestamp : UTC ceremony closing
│  ├─ Mayors Observation : [witnessed signatures]
│  ├─ NPC Observation : [collective mark]
│  └─ Immutability : SEALED (no further edits)
│
└─ ARCHIVE LOCATION
   ├─ /canon/2026/CORSE_ANNUAL_CODEX_2026.json
   ├─ /backup/[3 independent locations]
   ├─ /ledger/oracle_town/ (linked copy)
   └─ /ritual/ (Calvi vault — ceremonial storage)
```

---

## 🔐 SEAL FORMATS

### Daily Seal (Après publication quotidienne)

```json
{
  "publication_date": "2026-02-01",
  "seal_time": "2026-02-01T10:15:00Z",
  "colonne_a_count": 12,
  "colonne_b_count": 34,
  "integrity_hash": "sha256:abc123...",
  "kill_switch_status": "PASS",
  "towns_reporting": ["Ajaccio", "Bastia", "Calvi"],
  "npc_reporting": ["Collective.Ajaccio", "Collective.Bastia"],
  "seal_type": "DAILY",
  "next_seal": "2026-02-02T10:15:00Z",
  "modifications_allowed": "NONE (archive locked)"
}
```

### Monthly Seal (Fin du mois)

```json
{
  "period": "2026-01",
  "seal_time": "2026-02-01T00:00:00Z",
  "total_a_entries": 847,
  "total_b_entries": 2341,
  "total_publications": 31,
  "monthly_hash": "sha256:def456...",
  "chain_previous_month": "sha256:xyz789...",
  "seal_type": "MONTHLY",
  "ritual_seal": false,
  "modifications_allowed": "NONE"
}
```

### Annual Ritual Seal (Calvi Ceremony)

```json
{
  "year": 2026,
  "seal_time": "2026-06-15T17:00:00Z",
  "location": "Calvi",
  "ceremony_duration": "3 days",

  "phase_1_npc_insight_zone": {
    "status": "COMPLETED",
    "observations_generated": 847,
    "binding": false
  },

  "phase_2_mayor_testimony": {
    "status": "COMPLETED",
    "mayors_speaking": ["Ajaccio", "Bastia", "Calvi", ...],
    "decisions_made": 0,
    "binding": false
  },

  "phase_3_archive_sealing": {
    "status": "COMPLETED",
    "annual_hash": "sha256:ghi012...",
    "chain_previous_year": "sha256:prev2025...",
    "witnesses": ["Mayor.Calvi", "NPC.Collective.Bastia"],
    "modifications_allowed": "NEVER"
  },

  "seal_type": "RITUAL_ANNUAL",
  "immutability_enforced": true,
  "next_seal_date": "2027-06-15"
}
```

---

## 📊 STATISTIQUES GLOBALES (Non-interprétables)

### 2026 YTD

```
COLONNE A (Faits)
├─ Total Verdicts Published : 847
├─ SHIP     : 612 (72.3%)
├─ NO_SHIP  : 189 (22.3%)
├─ DEFER    : 46  (5.4%)
├─ Towns Reporting : 7
├─ Avg Delay : 2h 14m

COLONNE B (Insights)
├─ Total Observations : 2,341
├─ By NPC Collective : [distribution pur, no ranking]
├─ By WUL Type :
│  ├─ 🧠 Observations : 1,203
│  ├─ 🌊 Circulations : 789
│  ├─ 🔄 Emergences  : 349
│  └─ (autres) : 0
├─ Avg Length : 120 chars

ARCHIVE
├─ Total File Size : 24.7 MB
├─ Compression Ratio : 3.2:1
├─ Backup Copies : 4
├─ Integrity Checks : 100% pass
├─ Zero Modifications : confirmed
```

---

## 🔗 CHAÎNE DE VÉRIFICATION

### Vérification Quotidienne

```
Avant publication :
1. Kill-switch valide syntaxe A + B
2. Intégrité A : tous verdicts signés + hashes Ok
3. Intégrité B : tous observations timestamped
4. Séparation : aucune contamination A ← → B
5. Ledger : lien avec Oracle Town Authority vérié

Après publication :
6. Archive : fichier immutable écrit
7. Backup : copie 3+1 confirmée
8. Seal : hash de clôture calculé
9. Annonce : timestamp enregistré dans blockchain local
```

### Vérification Mensuelle (Audit)

```
Chaque mois (premier jour) :
1. Rejeu de 50 transports quotidiens aléatoires
2. Recalcul d'intégrité pour chaque jour
3. Vérification de chaîne (hash(J) = hash(J-1) + J)
4. Certification : "Aucune modification détectée"
5. Publication : Audit Report (public)
```

### Vérification Annuelle (Ritual)

```
Calvi on the Rocks :
1. Cryptographic seal of entire year
2. Witness observation by Mayors
3. NPC testimony on insight fertility
4. Archive sealing (NEVER unlock)
5. Ceremony documentation (for next year)
```

---

## 🖋️ PROCHAINES ÉDITIONS PRÉVUES

| Date | Type | Édition |
|------|------|---------|
| 2026-02-02 | Daily | `CORSE_2026-02-02` |
| 2026-02-03 | Daily | `CORSE_2026-02-03` |
| 2026-03-01 | Monthly | `MONTHLY_SEAL_2026-02` |
| 2026-06-15 | Ritual Annual | `ANNUAL_CODEX_2026` |
| 2027-02-01 | Daily | `CORSE_2027-02-01` (next year) |

---

## 📍 LOCALISATIONS D'ARCHIVE

### Emplacements Canoniques

```
LOCAL ARCHIVE
├─ /canon/2026/
├─ /canon/2025/ (précédent)
└─ /backup/corse_mirror_[1,2,3]/

ORACLE TOWN INTEGRATION
├─ /oracle_town/ledger/observations/
├─ oracle_town/ledger/verdicts/ (linked, not copied)

RITUAL VAULT (Calvi)
├─ /ritual/calvi/ANNUAL_CODEX_[YEAR].sealed
├─ Physical Archive (ceremonial storage)

DISTRIBUTED MIRRORS
├─ Town.Ajaccio:/corse_mirror/
├─ Town.Bastia:/corse_mirror/
└─ Town.[N]:/corse_mirror/
```

---

## 🔒 IMMUTABILITÉ GARANTIE

### Mecanismes

```
1. TIMESTAMP CHAINING
   Hash(Day N) = SHA256(Day N-1 Hash + Day N Data)

2. RITUAL SEALING
   Annual codex sealed on 2026-06-15
   Never open for modification

3. DISTRIBUTED WITNESS
   4+ independent parties hold copies
   Any modification attempt immediately detected

4. BLOCKCHAIN INTEGRATION
   Daily seals recorded in Oracle Town ledger
   Immutable by cryptographic receipt (K1)
```

---

## 🏛️ GOUVERNANCE DE LA CHARTE

### Modification de la Charte CORSE

```
Aucune modification ne peut être apportée sans :

1. Inter-town Consensus (all Mayors + NPC input)
2. 6-month notice period (published daily)
3. Calvi on the Rocks ritual approval (non-binding testimony)
4. New canonical edition sealed (with amendment log)
5. Old edition archived forever (never deleted)

Note: Modification = creation of NEW EDITION
      Not replacement of old (which remain canonical)
```

---

## ✅ VÉRIFICATION DE COMPLÉTUDE

```
✓ Daily edition : [publication timestamp].json
✓ Archive integrity : [hash verification].sha256
✓ Ritual seal (annual) : [ceremonial closure date]
✓ No modifications post-publication : [immutable]
✓ Backup redundancy : [4+ locations confirmed]
✓ Chain continuity : [hash chain unbroken]
```

---

**Status** : ✓ Registre Actif
**Last Update** : 2026-02-01
**Next Audit** : 2026-03-01
**Annual Ritual** : 2026-06-15 (Calvi on the Rocks)

🐎 TRACULINU NUNZIA — *La chaîne des messages est intacte*

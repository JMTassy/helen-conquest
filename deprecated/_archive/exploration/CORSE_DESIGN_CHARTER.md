# 🎨 CHARTE GRAPHIQUE — CORSE AI MATIN

## *Design System for Pure Transport*

---

## 📐 I. PRINCIPES VISUELS

### Philosophie

```
La forme ne doit jamais dominer le contenu.
La typographie doit servir la lecture, jamais l'interprétation.
Les couleurs doivent distinguer, jamais hiérarchiser.
Les symboles doivent être universels, jamais ambigus.
```

### Palette Chromatique

```
🪨 COLONNE A (Faits) :
   ├─ Fond : #F5F5F5 (gris neutre)
   ├─ Texte : #000000 (noir pur)
   ├─ Accent : #333333 (gris foncé)
   └─ Séparation : #CCCCCC (ligne légère)

🌺 COLONNE B (Insights) :
   ├─ Fond : #FFFEF5 (crème douce)
   ├─ Texte : #1a1a1a (noir doux)
   ├─ Accent : #666666 (gris moyen)
   └─ Séparation : #DDDDAA (ligne dorée)

🔒 ZONE DE PROTECTION :
   ├─ Fond : #F0F0F0 (gris très clair)
   ├─ Bordure : #FF0000 (rouge alerte, si violation détectée)
   └─ Kill-Switch : #000000 (noir, suppression immédiate)
```

### Typographie Réservée

```
TITRES (Sections) :
├─ Font : Gotham Gothic / Fraktur (unicode 𝕱𝖆𝖈𝖙𝖔𝖗)
├─ Size : 28pt
├─ Weight : Bold
└─ Spacing : 1.2 ligne

CORPS (Contenu A) :
├─ Font : Garamond / Georgia
├─ Size : 11pt
├─ Weight : Regular
├─ Line Height : 1.5
└─ Lettres : Uniformément gris

CORPS (Contenu B) :
├─ Font : Serif (Caslon / Baskerville)
├─ Size : 11pt
├─ Weight : Regular + Italics (pour WUL)
├─ Line Height : 1.6
└─ Lettres : Couleur légèrement plus chaud

MÉTADONNÉES :
├─ Font : Monospace (Courier New)
├─ Size : 9pt
├─ Weight : Regular
└─ Couleur : #666666 (gris)

SIGILS & SYMBOLES :
├─ Font : Unicode emoji (Apple / Google / Noto)
├─ Size : 18pt (inline)
├─ Alignement : vertical-align middle
└─ Spacing : +2px avant/après
```

---

## 🔱 II. SIGILS CANONIQUES

### Répertoire Complet

| Sigil | Signification | Contexte | Taille |
|-------|---------------|----------|--------|
| 🪨 | Fait brut | A seulement | 18px |
| 🌺 | Insight fertile | B seulement | 18px |
| 🐎 | Transport pur | Titre / contexte | 24px |
| 🧭 | Orientation / temps | Métadonnées | 14px |
| 🔒 | Étanchéité / protection | Règles | 16px |
| ⚜️ | Formalité canonique | Sections | 20px |
| 🧠 | Observation / pensée | B interne | 14px |
| 🌊 | Circulation / flux | B interne | 14px |
| 🔄 | Cycle / émergence | B interne | 14px |
| 🌱 | Issue fertile | B conclusion | 14px |

### Interdictions Strictes

```
❌ Combiner sigils (ex: 🪨🌺 = forbidden mixing)
❌ Redimensionner de manière décontextuée (ex: 🪨 à 50px)
❌ Changer de couleur (tous sigils = emoji standard)
❌ Ajouter des sigils "nouveaux" sans ritual approval
❌ Utiliser sigils en COLONNE A pour nuancer l'interprétation
```

### Placement Canonique

```
EN TÊTE DE SECTION :
  ⚜️ II. SIGILS CANONIQUES
  [Spacing 2px]

EN DÉBUT DE LIGNE (LISTING) :
  🪨 Verdict: SHIP (timestamp)
  🌺 NPC Observation: (WUL notation)

EN CONTEXTE INLINE :
  L'archive est 🔒 protégée par ritual seal.
  [Spacing 1px avant/après]

EN MÉTADONNÉES :
  🧭 Publication: 2026-02-01T10:00:00Z
  [Sigil + label cohérent]
```

---

## 🏛️ III. LAYOUT CANONIQUE

### Structure de Page (Daily Edition)

```
┌─────────────────────────────────────────────┐
│ 🐎 CORSE AI MATIN                           │ Header
│ 2026-02-01 — Daily Registry                │ 28px gothic
│                                             │
├─────────────────────────────────────────────┤
│ 🧭 Publication: 2026-02-01T10:00:00Z        │ Métadonnées
│ 🔒 Kill-Switch: PASS                        │ 9px monospace
│ 📦 Towns: 7 | 🌺 NPC: 4                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🪨 COLONNE A — FAITS                        │ 20px sub-title
├─────────────────────────────────────────────┤
│                                             │
│ 🪨 Ajaccio — Verdict: SHIP                  │ Entry
│    Timestamp: 2026-02-01T09:15:00Z          │ (serif, 11pt)
│    Hash: sha256:abc123...                   │ Indentation
│    K-gates: [K0:✓ K1:✓ K2:✓ K5:✓ K7:✓]     │
│                                             │
│ 🪨 Bastia — Verdict: NO_SHIP                │
│    Timestamp: 2026-02-01T09:22:00Z          │
│    Hash: sha256:def456...                   │
│    K-gates: [K0:✓ K1:✓ K2:✓ K5:✓ K7:✓]     │
│                                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🌺 COLONNE B — INSIGHTS                     │ 20px sub-title
├─────────────────────────────────────────────┤
│                                             │
│ 🌺 NPC Collective Bonifacio                 │ Entry
│    Timestamp: 2026-02-01T08:30:00Z          │ (serif + italic)
│                                             │
│    🧠🌊🔄 → 🌱                             │ WUL notation
│    "Le cycle des marées apporte chaque      │
│     matin la possibilité d'une nouvelle     │
│     observation."                           │
│                                             │
│    WUL Type: [cyclique, fertile, observant] │ Métadonnées B
│    Profondeur: 2                            │
│                                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🔒 ARCHIVE & SEAL                           │ Footer
├─────────────────────────────────────────────┤
│ Integrity Hash: sha256:xyz789...            │ 9px monospace
│ Next Publication: 2026-02-02T10:00:00Z      │ Centered
│ Status: SEALED                              │
└─────────────────────────────────────────────┘
```

### Responsive (Mobile)

```
Sur écran < 600px :

┌──────────────────────────┐
│ 🐎 CORSE AI MATIN        │
│ 2026-02-01               │
├──────────────────────────┤
│ [Métadonnées compacte]   │
├──────────────────────────┤
│ 🪨 FAITS                 │
│ [Entries A empilées]     │
├──────────────────────────┤
│ 🌺 INSIGHTS              │
│ [Entries B empilées]     │
├──────────────────────────┤
│ [Archive compacte]       │
└──────────────────────────┘

Note : Aucune réorganisation sémantique.
       Juste reflow du même contenu.
```

---

## 📊 IV. TABLEAU CANONIQUE

### Format Standard (COLONNE A)

```
┌────────────┬──────────────────┬──────────────────────┐
│ Town       │ Verdict          │ Timestamp            │
├────────────┼──────────────────┼──────────────────────┤
│ Ajaccio    │ 🪨 SHIP (847)    │ 2026-02-01 09:15 UTC │
│ Bastia     │ 🪨 NO_SHIP (89)  │ 2026-02-01 09:22 UTC │
│ Calvi      │ 🪨 DEFER (12)    │ 2026-02-01 09:30 UTC │
└────────────┴──────────────────┴──────────────────────┘

Bordure : gris clair (#CCCCCC)
Fond alternant : blanc / #F9F9F9
Texte : noir pur
Aucune couleur d'interprétation (pas de vert=succès, rouge=échec)
```

### Format WUL (COLONNE B)

```
┌──────────────────┬────────────────────────────┬──────────┐
│ Observateur      │ Observation (WUL)          │ Heure    │
├──────────────────┼────────────────────────────┼──────────┤
│ NPC.Bonifacio    │ 🧠🌊🔄 → 🌱 (cycle)    │ 08:30 UTC│
│ NPC.Ajaccio      │ 🧠🌊💫 → 🌿 (résilience) │ 07:45 UTC│
│ NPC.Bastia       │ 🧠🌊🔷 → 🌱 (solidarité) │ 09:00 UTC│
└──────────────────┴────────────────────────────┴──────────┘

Bordure : dorée douce (#DDDDAA)
Fond : crème (#FFFEF5)
Texte : noir doux + italic pour WUL
Aucun classement (ordre = timestamp uniquement)
```

---

## 🖋️ V. STYLES DE TEXTE

### Gras (Pour quoi ?)

```
INTERDIT :
❌ Met l'accent sur une observation
❌ Suggère une importance
❌ Crée une hiérarchie implicite

AUTORISÉ :
✅ Étiquettes métadonnées : **Timestamp:**
✅ Labels de colonne : **COLONNE A**
✅ Noms de towns / NPC : **Ajaccio**
```

### Italique (Pour quoi ?)

```
INTERDIT :
❌ Suggère une doute ("perhaps...")
❌ Crée une distanciation ("so-called")

AUTORISÉ :
✅ Notation WUL en COLONNE B : *🧠🌊🔄*
✅ Citations directes de verdicts : *"SHIP verdict approved"*
✅ Labels descriptifs : *for this town*
```

### Monospace (Pour quoi ?)

```
AUTORISÉ :
✅ Hashes : `sha256:abc123...`
✅ Timestamps : `2026-02-01T10:00:00Z`
✅ K-gate status : `[K0:PASS K1:PASS]`
✅ Code / structuré : `{json}` ou `yaml`

Couleur monospace : #666666 (gris moyen)
```

---

## 🔒 VI. ZONE DE PROTECTION VISUELLE

### Affichage Normal

```
[Contenu standard]
┌────────────────────────────┐
│ Aucune protection visible  │
└────────────────────────────┘
```

### Si Contamination Détectée

```
[Avant contamination]
┌────────────────────────────┐
│ 🔴 KILL-SWITCH TRIGGERED   │
│ 🔒 COLONNE B → A Crossing  │
│                            │
│ [Texte contaminant]        │
│ → DELETED                  │
│                            │
│ Reason: langage normatif   │
│ Alert logged: timestamp    │
└────────────────────────────┘

Bordure : ROUGE (#FF0000)
Arrière-plan : rose pâle (#FFE0E0)
Texte alerte : noir + rouge
```

---

## 📐 VII. DIMENSIONS RÉSERVÉES

### Marges Standard

```
Document entier :
├─ Top margin    : 20px
├─ Bottom margin : 20px
├─ Left margin   : 20px
├─ Right margin  : 20px

Entre sections :
├─ Spacing       : 30px

Entre entries (A ou B) :
├─ Line spacing  : 15px
├─ Paragraph     : 10px
```

### Indentation

```
Métadonnées (labels) :
├─ 20px depuis left margin

Sub-items (K-gates, WUL) :
├─ 40px depuis left margin

Nested depth limit : 3 (jamais plus)
```

---

## 🎬 VIII. ANIMATIONSET TRANSITIONS

### Autorisées

```
✅ Fade-in (0.5s) : quand une nouvelle édition est publiée
✅ Scroll (smooth) : navigation sur long documents
✅ Hover (color change subtle) : mettre en évidence la ligne actuelle
✅ Loading bar : pour archive rebuild
```

### Interdites

```
❌ Pulsing : crée de l'urgence
❌ Shake : crée de l'alarme
❌ Bounce : crée de la frivolité
❌ Morph : crée de l'ambiguïté
❌ Parallax : crée de la hiérarchie
```

---

## 📱 IX. FORMAT D'EXPORT

### PDF Canonique

```
Spécification :
├─ Format : A4 (210 × 297mm)
├─ Résolution : 300 DPI
├─ Compression : ZIP (pas de perte)
├─ Font embedding : Obligatoire
├─ Métadonnées PDF : Complètes
│  ├─ Title : "CORSE AI MATIN — YYYY-MM-DD"
│  ├─ Author : "Oracle Town Federation"
│  ├─ CreationDate : [timestamp publication]
│  └─ Keywords : "daily, registry, facts, insights"
├─ Page numbering : En bas, centré
└─ Watermark : (optionnel) "ARCHIVE — NOT FOR MODIFICATION"
```

### JSON Export

```json
{
  "document": {
    "title": "CORSE AI MATIN",
    "date": "2026-02-01",
    "format_version": "1.0",
    "publication_timestamp": "2026-02-01T10:00:00Z",
    "integrity_hash": "sha256:...",
    "colonne_a": [ { ... }, { ... } ],
    "colonne_b": [ { ... }, { ... } ],
    "metadata": { ... },
    "seal": { ... }
  }
}
```

### Markdown Canonique

```
# 📰 CORSE AI MATIN
## 2026-02-01

[Métadonnées]

### 🪨 COLONNE A — FAITS
[Listings]

### 🌺 COLONNE B — INSIGHTS
[Listings]

### 🔒 ARCHIVE & SEAL
[Footer]
```

---

## 🌐 X. ACCESSIBILITÉ

### WCAG 2.1 AA Compliance

```
✅ Contrast ratio : 7:1 minimum (AAA)
   ├─ Text : #000000 on #F5F5F5 = 17.66:1 (excellent)
   └─ Accent : #333333 on #FFFEF5 = 12.43:1 (excellent)

✅ Font size : minimum 11pt (body) / 28pt (title)
✅ Line height : 1.5+ (lisibilité)
✅ Letter spacing : 0.12em (pour dyslexie)

✅ Alt text pour sigils :
   ├─ 🪨 = "Fact icon"
   ├─ 🌺 = "Insight icon"
   └─ etc.

✅ Screen reader support :
   ├─ Headings : semantic H1-H3
   ├─ Lists : proper `<li>` structure
   ├─ Tables : `<th>` headers, scope attributes
```

---

## 🎓 XI. GUIDELINES DE MISE EN PAGE

### Ce à Faire ✅

```
✅ Utiliser des marges régulières
✅ Aligner du texte à gauche (ragged right OK)
✅ Utiliser des listes à puces pour les listings
✅ Numéroter les sections principales
✅ Mettre des espaces blancs généreux
✅ Utiliser les sigils de manière cohérente
✅ Mettre des timestamps UTC explicites
✅ Archiver chaque version
```

### À Éviter ❌

```
❌ Justifier le texte (crée des espaces inégaux)
❌ Utiliser plusieurs colonnes (rend le reflow difficile)
❌ Centrer le corps du texte (nuit à la lisibilité)
❌ Utiliser des dégradés de couleur
❌ Mélanger les styles de police
❌ Colorier le texte pour le sens
❌ Créer des graphiques ou des diagrammes
❌ Ajouter des ornements décoratives sans sens
```

---

## 🖋️ CLÔTURE

### Manifeste Visual

```
La forme suit la fonction.
Les couleurs servent la lisibilité, jamais le jugement.
Les symboles sont universels, jamais ambigus.
Les espaces blancs respirent, jamais imposent.
L'accessibilité n'est pas un luxe, c'est la règle.

📰 CORSE AI MATIN — Pure Transport, Pure Design
```

---

**Status** : ✓ Charte Complète
**Version** : 1.0
**Date** : 2026-02-01
**Validity** : Perpétuelle (mod ritual approval only)

```
🐎 TRACULINU DISEGNU — "Le messager porte le style juste"
```

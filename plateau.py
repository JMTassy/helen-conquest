#!/usr/bin/env python3
"""
CONQUEST — Le Plateau en Mouvement  v1.0
=========================================
Le savoir mène au pouvoir.

Mécaniques exactes du jeu plateau:
  Dé → Catégorie (Sci/Hist/Lit) → QCM → Zols (±)
  Accumuler 250K zols → acheter territoire → 6 territoires = victoire

Archétypes (asymétrie réelle):
  Militaire  — Force dés+1, prison 3 tours si capturé
  Prince     — Immunisé prison, mais QCM perd 1 choix
  Savant     — QCM +5s (simulé par bonus), dés-1
  Diplomate  — Achète à 80%, ne peut attaquer qu'un tour sur deux
  Princesse  — Reçoit 10% quand un autre achète, ne peut pas acheter dernier territoire
  Millionnaire — Démarre +30K zols, dés-2

Duel (2/3 manches):
  1. Connaissance (QCM simulé)
  2. Écologique (hasard pur)
  3. Dés (hasard pur)

Usage:
  python3 plateau.py              # 4 joueurs, seed aléatoire
  python3 plateau.py 42           # seed déterministe
  python3 plateau.py --demo       # démo automatique 30 tours
  python3 plateau.py --help
"""

import sys
import random
import os
import time
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

# ── couleur optionnelle ───────────────────────────────────────
try:
    from colorama import Fore, Back, Style, init as _cinit
    _cinit(autoreset=True)
    C = True
except ImportError:
    C = False
    class _F:
        def __getattr__(self, _): return ""
    Fore = Style = _F()

def c(color_attr, text):
    if C: return getattr(Fore, color_attr, "") + str(text) + Style.RESET_ALL
    return str(text)

def bold(text):
    if C: return Style.BRIGHT + str(text) + Style.RESET_ALL
    return str(text)

# ═══════════════════════════════════════════════════════════════
# DONNÉES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Archetype:
    name: str
    glyph: str
    bonus_desc: str
    handicap_desc: str
    dice_bonus: int          # bonus dé en duel
    qcm_time_bonus: int      # secondes supplémentaires (simulé: +% précision)
    prison_turns: int        # tours en prison si capturé (0 = immunisé)
    start_zols_bonus: int    # zols de départ supplémentaires
    buy_discount: float      # multiplicateur achat (1.0 = normal, 0.8 = -20%)
    princess_passive: bool   # reçoit % des achats des autres
    insight_win: str
    insight_loss: str

ARCHETYPES = [
    Archetype(
        name="MILITAIRE", glyph="⚔",
        bonus_desc="Duel dés +1",
        handicap_desc="Prison 3 tours si capturé",
        dice_bonus=1, qcm_time_bonus=0, prison_turns=3,
        start_zols_bonus=0, buy_discount=1.0, princess_passive=False,
        insight_win="La force sans sagesse est aveugle. Tu as gagné par la lame — combien de temps tiendra-t-elle?",
        insight_loss="La prison révèle ce que la victoire cache: qui es-tu quand tu ne peux plus agir?",
    ),
    Archetype(
        name="PRINCE", glyph="♛",
        bonus_desc="Immunisé prison",
        handicap_desc="QCM: perd 10% de précision",
        dice_bonus=0, qcm_time_bonus=0, prison_turns=0,
        start_zols_bonus=0, buy_discount=1.0, princess_passive=False,
        insight_win="Naître dans la fortune n'est pas la mériter. Tu l'as prise — est-ce toujours tien?",
        insight_loss="L'immunité te protège du risque. Elle te prive aussi de la transformation.",
    ),
    Archetype(
        name="SAVANT", glyph="📚",
        bonus_desc="QCM précision +15%",
        handicap_desc="Duel dés -1",
        dice_bonus=-1, qcm_time_bonus=5, prison_turns=1,
        start_zols_bonus=0, buy_discount=1.0, princess_passive=False,
        insight_win="La connaissance t'a mené ici. Ce que tu sais définit ce que tu peux conquérir.",
        insight_loss="Savoir n'est pas suffire. La vérité que tu portais — l'as-tu vraiment appliquée?",
    ),
    Archetype(
        name="DIPLOMATE", glyph="🤝",
        bonus_desc="Achète territoires -20%",
        handicap_desc="Attaque seulement un tour sur deux",
        dice_bonus=0, qcm_time_bonus=0, prison_turns=1,
        start_zols_bonus=0, buy_discount=0.8, princess_passive=False,
        insight_win="Tu as bâti des ponts là où d'autres creusaient des fossés. C'est rare.",
        insight_loss="La diplomatie a ses limites. Quand les autres refusent de parler, que fais-tu?",
    ),
    Archetype(
        name="PRINCESSE", glyph="👑",
        bonus_desc="Reçoit 10% quand un autre achète",
        handicap_desc="Ne peut pas acheter le dernier territoire",
        dice_bonus=0, qcm_time_bonus=0, prison_turns=1,
        start_zols_bonus=0, buy_discount=1.0, princess_passive=True,
        insight_win="Tu as prospéré dans l'écosystème de l'autre. Est-ce victoire ou dépendance?",
        insight_loss="La richesse des autres ne suffit pas. À quel moment décides-tu d'agir seule?",
    ),
    Archetype(
        name="MILLIONNAIRE", glyph="💰",
        bonus_desc="Démarre avec +30,000 zols",
        handicap_desc="Duel dés -2",
        dice_bonus=-2, qcm_time_bonus=0, prison_turns=1,
        start_zols_bonus=30000, buy_discount=1.0, princess_passive=False,
        insight_win="La fortune offre un départ. Ce que tu en fais révèle ta vraie valeur.",
        insight_loss="L'argent a ses limites. Ce que l'argent ne peut pas acheter — tu l'as appris?",
    ),
]

@dataclass
class Territoire:
    name: str
    price: int
    glyph: str
    owner_id: Optional[int] = None

TERRITOIRES = [
    Territoire("Versailles", 60000, "🏰"),
    Territoire("Corse",      40000, "🏝"),
    Territoire("Alpes",      35000, "⛰"),
    Territoire("Bretagne",   30000, "🌊"),
    Territoire("Bordeaux",   25000, "🍷"),
    Territoire("Camargue",   20000, "🦩"),
]

@dataclass
class Question:
    category: str
    question: str
    choices: List[str]
    correct: int     # index

QUESTIONS = [
    # Science
    Question("Science", "Quel élément a le numéro atomique 79?",
             ["Argent", "Or", "Platine", "Cuivre"], 1),
    Question("Science", "Quelle planète est la plus proche du Soleil?",
             ["Vénus", "Mars", "Mercure", "Terre"], 2),
    Question("Science", "Vitesse de la lumière (approx, km/s)?",
             ["200 000", "299 792", "350 000", "150 000"], 1),
    Question("Science", "Combien de chromosomes l'humain possède-t-il?",
             ["23", "46", "48", "44"], 1),
    Question("Science", "Qui a découvert la pénicilline?",
             ["Pasteur", "Curie", "Fleming", "Koch"], 2),
    Question("Science", "Formule chimique de l'eau?",
             ["HO", "H2O", "H3O", "OH2"], 1),
    Question("Science", "L'ADN est composé de combien de brins?",
             ["1", "2", "3", "4"], 1),
    Question("Science", "Quelle est la force qui maintient les planètes en orbite?",
             ["Magnétisme", "Électricité", "Gravité", "Friction"], 2),
    # Histoire
    Question("Histoire", "Année de la Révolution française?",
             ["1776", "1789", "1792", "1804"], 1),
    Question("Histoire", "Premier Président de la Ve République?",
             ["Pompidou", "De Gaulle", "Mitterrand", "Chirac"], 1),
    Question("Histoire", "Quelle bataille Napoléon a perdue en 1815?",
             ["Austerlitz", "Iéna", "Waterloo", "Borodino"], 2),
    Question("Histoire", "Année de la chute du mur de Berlin?",
             ["1987", "1990", "1989", "1991"], 2),
    Question("Histoire", "Civilisation qui a construit le Colisée?",
             ["Grecque", "Romaine", "Égyptienne", "Byzantine"], 1),
    Question("Histoire", "Sigle de l'alliance militaire occidentale fondée en 1949?",
             ["ONU", "OTAN", "UE", "OCDE"], 1),
    Question("Histoire", "Louis XIV a régné pendant combien d'années?",
             ["42", "55", "72", "61"], 2),
    Question("Histoire", "Qui était Cléopâtre VII?",
             ["Grecque", "Romaine", "Égyptienne", "Perse"], 2),
    # Littérature
    Question("Littérature", "Qui a écrit 'Les Misérables'?",
             ["Balzac", "Zola", "Victor Hugo", "Flaubert"], 2),
    Question("Littérature", "Roman avec Raskolnikov?",
             ["Crime et Châtiment", "L'Idiot", "Les Frères Karamazov", "Guerre et Paix"], 0),
    Question("Littérature", "Qui a écrit 'À la recherche du temps perdu'?",
             ["Camus", "Proust", "Sartre", "Gide"], 1),
    Question("Littérature", "Pays de 'Don Quichotte'?",
             ["Portugal", "France", "Espagne", "Italie"], 2),
    Question("Littérature", "Créateur de Sherlock Holmes?",
             ["Christie", "Poe", "Conan Doyle", "Leblanc"], 2),
    Question("Littérature", "Qui a écrit 'L'Étranger'?",
             ["Sartre", "Gide", "Camus", "Beauvoir"], 2),
    Question("Littérature", "Dans quel roman trouve-t-on Gatsby?",
             ["Gatsby le Magnifique", "Tender is the Night", "This Side of Paradise", "The Beautiful and Damned"], 0),
]

CATEGORIES = ["Science", "Histoire", "Littérature"]

EPOCHS = [
    ("GROUNDING",  "Les fondations se posent"),
    ("SEEING",     "Les patterns émergent"),
    ("STRUGGLE",   "La pression monte"),
    ("ORDER",      "L'ordre s'impose"),
    ("BONDING",    "Les alliances se révèlent"),
    ("SHEDDING",   "Ce qui n'est plus nécessaire tombe"),
]

ZOLS_TARGET       = 250000
ZOLS_PER_CORRECT  = 2000
ZOLS_PENALTY      = 500
ZOLS_DUEL_WIN     = 5000
QCM_BASE_ACCURACY = 0.55   # base AI accuracy for QCM simulation

# ═══════════════════════════════════════════════════════════════
# ÉTAT
# ═══════════════════════════════════════════════════════════════

@dataclass
class LedgerEntry:
    turn: int
    player_id: int
    entry_type: str   # "contradiction" | "moment" | "pattern"
    text: str

@dataclass
class Player:
    id: int
    archetype: Archetype
    zols: int
    territories: List[int] = field(default_factory=list)
    prison_turns: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    duels_won: int = 0
    duels_lost: int = 0
    can_attack: bool = True  # Diplomate: alternating

    @property
    def accuracy(self):
        total = self.total_correct + self.total_wrong
        return self.total_correct / total if total > 0 else 0

    def qcm_accuracy_effective(self):
        base = QCM_BASE_ACCURACY
        if self.archetype.name == "SAVANT":
            base += 0.15
        elif self.archetype.name == "PRINCE":
            base -= 0.10
        return base

@dataclass
class GameState:
    seed: int
    rng: random.Random
    players: List[Player]
    territories: List[Territoire]
    turn: int = 1
    current_player: int = 0
    epoch_idx: int = 0
    turns_in_epoch: int = 0
    ledger: List[LedgerEntry] = field(default_factory=list)
    log: List[str] = field(default_factory=list)
    used_questions: Set[int] = field(default_factory=set)
    winner: Optional[Player] = None
    demo_mode: bool = False

# ═══════════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════════

def new_game(seed: int, num_players: int = 4, demo: bool = False) -> GameState:
    rng = random.Random(seed)
    archetype_indices = list(range(len(ARCHETYPES)))
    rng.shuffle(archetype_indices)
    selected = archetype_indices[:num_players]

    players = []
    for i, ai in enumerate(selected):
        arch = ARCHETYPES[ai]
        starting_zols = 20000 + arch.start_zols_bonus
        players.append(Player(id=i, archetype=arch, zols=starting_zols))

    territories = [Territoire(t.name, t.price, t.glyph) for t in TERRITOIRES]

    gs = GameState(
        seed=seed, rng=rng,
        players=players, territories=territories,
        demo_mode=demo,
    )

    gs.log.append(f"Le Plateau s'éveille. Seed={seed}. {num_players} joueurs.")
    gs.log.append("Le savoir mène au pouvoir.")
    return gs

# ═══════════════════════════════════════════════════════════════
# MÉCANIQUE
# ═══════════════════════════════════════════════════════════════

def roll_die(gs: GameState) -> int:
    return gs.rng.randint(1, 6)

def get_question(gs: GameState, category: str) -> Question:
    pool = [i for i, q in enumerate(QUESTIONS) if q.category == category and i not in gs.used_questions]
    if not pool:
        gs.used_questions.clear()
        pool = [i for i, q in enumerate(QUESTIONS) if q.category == category]
    idx = gs.rng.choice(pool)
    gs.used_questions.add(idx)
    return QUESTIONS[idx]

def simulate_qcm(gs: GameState, player: Player, question: Question) -> bool:
    """Simulate player answering QCM (for demo/AI mode)."""
    acc = player.qcm_accuracy_effective()
    return gs.rng.random() < acc

def run_duel(gs: GameState, attacker: Player, defender: Player, terr_id: int) -> Player:
    """
    Duel 2/3 manches:
      1. Connaissance (QCM simulé)
      2. Écologique (hasard pur)
      3. Dés si nécessaire
    Retourne le vainqueur.
    """
    atk_score = 0
    def_score = 0
    log_lines = []

    # Manche 1: Connaissance
    q = get_question(gs, gs.rng.choice(CATEGORIES))
    atk_correct = simulate_qcm(gs, attacker, q)
    def_correct = simulate_qcm(gs, defender, q)

    if atk_correct and not def_correct:
        atk_score += 1
        log_lines.append(f"  M1 Connaissance: {attacker.archetype.glyph}ATK ✓  {defender.archetype.glyph}DEF ✗  → ATK +1")
    elif def_correct and not atk_correct:
        def_score += 1
        log_lines.append(f"  M1 Connaissance: {attacker.archetype.glyph}ATK ✗  {defender.archetype.glyph}DEF ✓  → DEF +1")
    else:
        log_lines.append(f"  M1 Connaissance: {'✓' if atk_correct else '✗'}/{' ✓' if def_correct else '✗'} → Égalité")

    # Manche 2: Écologique (hasard pur)
    eco_options = ["pluie", "rivière", "océan"]
    eco_atk = gs.rng.choice(eco_options)
    eco_def = gs.rng.choice(eco_options)
    # Règle: océan > rivière > pluie (ou hasard pur si égal)
    eco_order = {"pluie": 0, "rivière": 1, "océan": 2}
    if eco_order[eco_atk] > eco_order[eco_def]:
        atk_score += 1
        log_lines.append(f"  M2 Écologique: {eco_atk} vs {eco_def} → ATK +1 (HASARD PUR)")
    elif eco_order[eco_def] > eco_order[eco_atk]:
        def_score += 1
        log_lines.append(f"  M2 Écologique: {eco_atk} vs {eco_def} → DEF +1 (HASARD PUR)")
    else:
        # Égalité: dés rapide
        winner_eco = gs.rng.choice([attacker, defender])
        if winner_eco.id == attacker.id:
            atk_score += 1
        else:
            def_score += 1
        log_lines.append(f"  M2 Écologique: {eco_atk} vs {eco_def} → Égalité → {winner_eco.archetype.name} (HASARD PUR)")

    # Manche 3 si nécessaire (1-1)
    if atk_score == 1 and def_score == 1:
        atk_roll = roll_die(gs) + attacker.archetype.dice_bonus
        def_roll = roll_die(gs) + defender.archetype.dice_bonus
        atk_roll = max(1, atk_roll)
        def_roll = max(1, def_roll)
        log_lines.append(f"  M3 Dés: {attacker.archetype.glyph}[{atk_roll}] vs {defender.archetype.glyph}[{def_roll}] (HASARD PUR)")
        if atk_roll >= def_roll:
            atk_score += 1
        else:
            def_score += 1

    winner = attacker if atk_score > def_score else defender
    loser  = defender if winner.id == attacker.id else attacker

    return winner, loser, log_lines

def process_turn(gs: GameState, player: Player, interactive: bool = True) -> None:
    """Joue un tour complet pour un joueur."""
    print()
    print(c("YELLOW", f"═══ TOUR {gs.turn} │ {player.archetype.glyph} {player.archetype.name} ({player.zols:,} zols) ═══"))

    # Prison
    if player.prison_turns > 0:
        player.prison_turns -= 1
        print(c("RED", f"  {player.archetype.glyph} {player.archetype.name} est en PRISON. ({player.prison_turns} tours restants)"))
        gs.log.append(f"T{gs.turn}: {player.archetype.name} reste en prison. {player.prison_turns}t restants.")
        return

    # Diplomate: alterne
    if player.archetype.name == "DIPLOMATE" and not player.can_attack:
        player.can_attack = True
        print(c("CYAN", "  DIPLOMATE: ce tour sans attaque (règle alternance). Zols collectés."))
        # Still earns from QCM
        dice = roll_die(gs)
        print(f"  Dé: {dice}")
        category = CATEGORIES[(dice - 1) % 3]
        print(f"  Catégorie: {c('CYAN', category)}")
        q = get_question(gs, category)
        correct = run_qcm(gs, player, q, interactive)
        if correct:
            player.zols += ZOLS_PER_CORRECT
            print(c("GREEN", f"  ✓ Correct! +{ZOLS_PER_CORRECT:,} zols → {player.zols:,}"))
        else:
            player.zols = max(0, player.zols - ZOLS_PENALTY)
            print(c("RED", f"  ✗ Faux. -{ZOLS_PENALTY:,} zols → {player.zols:,}"))
        return

    if player.archetype.name == "DIPLOMATE":
        player.can_attack = False  # next turn no attack

    # 1. Lance dé
    if interactive and not gs.demo_mode:
        input(c("DIM", "  [Entrée pour lancer le dé...]"))
    else:
        time.sleep(0.3)

    dice = roll_die(gs)
    die_faces = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    print(f"  Dé: {die_faces[dice]} ({dice})")

    # 2. Catégorie
    category = CATEGORIES[(dice - 1) % 3]
    print(f"  Catégorie: {c('CYAN', category.upper())}")
    gs.log.append(f"T{gs.turn}: {player.archetype.name} tire {dice} → {category}")

    # 3. QCM
    q = get_question(gs, category)
    correct = run_qcm(gs, player, q, interactive)

    if correct:
        player.zols += ZOLS_PER_CORRECT
        player.total_correct += 1
        print(c("GREEN", f"  ✓ Correct! +{ZOLS_PER_CORRECT:,} zols → {player.zols:,}"))
        gs.log.append(f"  → Correct +{ZOLS_PER_CORRECT:,}z. Total: {player.zols:,}")

        # Ledger: contradiction check
        if player.archetype.name == "MILITAIRE" and category == "Science":
            if player.total_correct > player.duels_won:
                add_ledger(gs, player.id, "contradiction",
                    f"MILITAIRE excelle en {category} ({player.total_correct}x correct) mais se définit par la force. "
                    f"Identité déclarée vs compétence réelle.")
    else:
        player.zols = max(0, player.zols - ZOLS_PENALTY)
        player.total_wrong += 1
        print(c("RED", f"  ✗ Faux. Réponse correcte: {c('YELLOW', q.choices[q.correct])}"))
        print(c("RED", f"  -{ZOLS_PENALTY:,} zols → {player.zols:,}"))
        gs.log.append(f"  → Faux -{ZOLS_PENALTY:,}z. Total: {player.zols:,}")

        if player.archetype.name == "SAVANT" and player.total_wrong >= 3:
            add_ledger(gs, player.id, "contradiction",
                f"SAVANT s'est trompé {player.total_wrong}× — la connaissance affichée est-elle réelle?")

    # 4. Achat territoire?
    check_territory_purchase(gs, player, interactive)


def run_qcm(gs: GameState, player: Player, q: Question, interactive: bool) -> bool:
    """Affiche la question. Retourne True si correct."""
    print()
    print(f"  {c('YELLOW', '?')} {q.question}")
    choices_display = list(q.choices)

    # PRINCE: retire un mauvais choix
    prince_removed = None
    if player.archetype.name == "PRINCE" and len(choices_display) > 2:
        wrong_idxs = [i for i in range(len(choices_display)) if i != q.correct]
        remove_idx = gs.rng.choice(wrong_idxs)
        prince_removed = choices_display[remove_idx]
        choices_display = [c_ for i, c_ in enumerate(choices_display) if i != remove_idx]
        print(c("DIM", f"  (Prince: choix retiré — '{prince_removed}')"))

    for i, ch in enumerate(choices_display):
        print(f"    {chr(65+i)}) {ch}")

    # Vrai correct idx after possible removal
    correct_text = q.choices[q.correct]
    new_correct = next((i for i, ch in enumerate(choices_display) if ch == correct_text), 0)

    if interactive and not gs.demo_mode:
        raw = input(c("DIM", "  Votre réponse (A/B/C/D ou Q pour passer): ")).strip().upper()
        if raw in "ABCD" and len(raw) == 1:
            chosen = ord(raw) - ord("A")
            return chosen == new_correct
        else:
            # Simulate
            return gs.rng.random() < player.qcm_accuracy_effective()
    else:
        # Demo: simulate
        return gs.rng.random() < player.qcm_accuracy_effective()


def check_territory_purchase(gs: GameState, player: Player, interactive: bool) -> None:
    """Vérifie si le joueur peut et veut acheter un territoire."""
    available = [
        t for i, t in enumerate(gs.territories)
        if t.owner_id is None
    ]

    if not available:
        return

    # Can player afford anything?
    affordable = []
    for t in available:
        cost = int(t.price * player.archetype.buy_discount)
        # Princesse ne peut pas acheter le dernier territoire
        if player.archetype.princess_passive and len(available) == 1:
            continue
        if player.zols >= cost:
            affordable.append((t, cost))

    if not affordable:
        return

    if not interactive or gs.demo_mode:
        # Auto-buy cheapest if zols > 40% target
        if player.zols >= ZOLS_TARGET * 0.4:
            t, cost = min(affordable, key=lambda x: x[1])
            do_buy(gs, player, t, cost)
        return

    print()
    print(c("GOLD" if C else "YELLOW", f"  💰 {player.archetype.name} peut acheter:"))
    for i, (t, cost) in enumerate(affordable):
        contested = " ⚔ [CONTESTÉ]" if False else ""
        print(f"    {i+1}) {t.glyph} {t.name:<12} {cost:>8,} zols{contested}")
    print(f"    0) Passer")

    raw = input(c("DIM", "  Choisir (0 = passer): ")).strip()
    try:
        idx = int(raw)
        if idx == 0:
            return
        if 1 <= idx <= len(affordable):
            t, cost = affordable[idx - 1]
            do_buy(gs, player, t, cost)
    except ValueError:
        pass


def do_buy(gs: GameState, player: Player, t: Territoire, cost: int) -> None:
    """Achète un territoire."""
    # Check if contested (owned by another player)
    if t.owner_id is not None and t.owner_id != player.id:
        run_duel_for_territory(gs, player, gs.players[t.owner_id], t)
        return

    player.zols -= cost
    t.owner_id = player.id
    player.territories.append(gs.territories.index(t))

    print(c("GREEN" if C else "YELLOW", f"  ✓ {player.archetype.glyph} Acquiert {t.glyph} {t.name}! (-{cost:,}z)"))
    gs.log.append(f"T{gs.turn}: {player.archetype.name} acquiert {t.name} pour {cost:,}z")

    add_ledger(gs, player.id, "moment",
        f"Tour {gs.turn}: {player.archetype.name} acquiert {t.name}. "
        f"Territoires: {len(player.territories)}/6")

    # Princesse passive: reçoit 10%
    for other in gs.players:
        if other.archetype.princess_passive and other.id != player.id:
            bonus = int(cost * 0.10)
            other.zols += bonus
            print(c("YELLOW", f"  {other.archetype.glyph} PRINCESSE reçoit {bonus:,}z (10% passif)"))
            add_ledger(gs, other.id, "contradiction",
                f"PRINCESSE reçoit {bonus:,}z de l'achat de {player.archetype.name}. "
                f"Profit sans risque: est-ce une stratégie ou une dépendance?")


def run_duel_for_territory(gs: GameState, attacker: Player, defender: Player, t: Territoire) -> None:
    """Lance un duel pour un territoire contesté."""
    print()
    print(c("RED", f"  ⚔ DUEL: {attacker.archetype.glyph}{attacker.archetype.name} vs {defender.archetype.glyph}{defender.archetype.name}"))
    print(c("YELLOW", f"  Territoire: {t.glyph} {t.name} ({t.price:,}z)"))

    cost_atk = int(t.price * attacker.archetype.buy_discount)
    if attacker.zols < cost_atk:
        print(c("RED", f"  {attacker.archetype.name} n'a pas assez de zols pour ce territoire."))
        return

    winner, loser, duel_log = run_duel(gs, attacker, defender, gs.territories.index(t))

    for line in duel_log:
        print(c("DIM", line))

    if winner.id == attacker.id:
        attacker.zols -= cost_atk
        attacker.duels_won += 1
        defender.duels_lost += 1
        attacker.zols += ZOLS_DUEL_WIN

        # Transfer territory
        if t.owner_id is not None:
            old_owner = gs.players[t.owner_id]
            old_owner.territories = [tid for tid in old_owner.territories if tid != gs.territories.index(t)]
        t.owner_id = attacker.id
        attacker.territories.append(gs.territories.index(t))

        print(c("GREEN", f"  ✓ {attacker.archetype.glyph} {attacker.archetype.name} conquiert {t.name}! (+{ZOLS_DUEL_WIN:,}z bonus)"))
        gs.log.append(f"T{gs.turn}: {attacker.archetype.name} conquiert {t.name} par duel")
        add_ledger(gs, attacker.id, "moment", attacker.archetype.insight_win)

        # Prison pour le perdant Militaire
        if loser.archetype.prison_turns > 0:
            loser.prison_turns = loser.archetype.prison_turns
            print(c("RED", f"  {loser.archetype.glyph} {loser.archetype.name} → PRISON ({loser.prison_turns} tours)"))
            gs.log.append(f"  {loser.archetype.name} emprisonné {loser.prison_turns} tours")
            add_ledger(gs, loser.id, "contradiction", loser.archetype.insight_loss)

        # Flag: 2/3 du duel = hasard pur
        hasard_count = sum(1 for l in duel_log if "HASARD PUR" in l)
        if hasard_count >= 1:
            add_ledger(gs, attacker.id, "contradiction",
                f"Note: {hasard_count}/3 manche(s) du duel = hasard pur. "
                f"La victoire de {attacker.archetype.name} était-elle méritée?")

    else:
        defender.duels_won += 1
        attacker.duels_lost += 1
        print(c("RED", f"  ✗ {defender.archetype.glyph} {defender.archetype.name} défend {t.name}"))
        gs.log.append(f"T{gs.turn}: {defender.archetype.name} défend {t.name}")
        add_ledger(gs, defender.id, "moment", defender.archetype.insight_win)

        if loser.archetype.prison_turns > 0:
            loser.prison_turns = loser.archetype.prison_turns
            add_ledger(gs, loser.id, "contradiction", loser.archetype.insight_loss)


# ═══════════════════════════════════════════════════════════════
# LEDGER
# ═══════════════════════════════════════════════════════════════

def add_ledger(gs: GameState, player_id: int, entry_type: str, text: str) -> None:
    gs.ledger.append(LedgerEntry(
        turn=gs.turn, player_id=player_id,
        entry_type=entry_type, text=text
    ))

# ═══════════════════════════════════════════════════════════════
# VICTOIRE
# ═══════════════════════════════════════════════════════════════

def check_victory(gs: GameState) -> Optional[Player]:
    for p in gs.players:
        if len(p.territories) >= 6:
            return p
        if p.zols >= ZOLS_TARGET and len(p.territories) >= 3:
            return p
    return None

# ═══════════════════════════════════════════════════════════════
# RENDU
# ═══════════════════════════════════════════════════════════════

def _clear():
    os.system("clear" if os.name == "posix" else "cls")

def render_header(gs: GameState) -> None:
    ep_name, ep_desc = EPOCHS[gs.epoch_idx]
    print()
    print(c("YELLOW", "╔══════════════════════════════════════════════════════╗"))
    print(c("YELLOW", "║") + bold("          CONQUEST — LE PLATEAU EN MOUVEMENT          ") + c("YELLOW", "║"))
    print(c("YELLOW", f"║  Tour {gs.turn:<5}  Époque: {ep_name:<12}  Seed: {gs.seed:<8}  ║"))
    print(c("YELLOW", "╚══════════════════════════════════════════════════════╝"))

def render_players(gs: GameState) -> None:
    print()
    print(c("CYAN", "JOUEURS:"))
    print(c("DIM", "─" * 70))
    for p in gs.players:
        a = p.archetype
        bar_len = 20
        filled = min(bar_len, int(bar_len * p.zols / ZOLS_TARGET))
        bar = "█" * filled + "░" * (bar_len - filled)
        acc = f"{int(100*p.accuracy)}%" if (p.total_correct + p.total_wrong) > 0 else "—"
        prison_str = c("RED", f" [PRISON {p.prison_turns}t]") if p.prison_turns > 0 else ""
        active_marker = c("YELLOW", " ◄") if gs.players[gs.current_player].id == p.id else ""

        line = (f"  {a.glyph} {a.name:<14}"
                f" {p.zols:>9,}z  [{bar}]  "
                f"QCM:{acc}  Duels:{p.duels_won}W/{p.duels_lost}L"
                f"  Terr:{len(p.territories)}/6")
        print(line + prison_str + active_marker)
    print(c("DIM", "─" * 70))

def render_territories(gs: GameState) -> None:
    print()
    print(c("CYAN", "PLATEAU — 6 TERRITOIRES:"))
    for i, t in enumerate(gs.territories):
        if t.owner_id is not None:
            owner = gs.players[t.owner_id]
            owner_str = c("GREEN", f"  ← {owner.archetype.glyph} {owner.archetype.name}")
        else:
            owner_str = c("DIM", "  (libre)")
        print(f"  {i+1}) {t.glyph} {t.name:<12} {t.price:>8,}z {owner_str}")

def render_ledger(gs: GameState, n: int = 5) -> None:
    if not gs.ledger:
        return
    print()
    print(c("YELLOW", "REGISTRE DES RÉVÉLATIONS (Kernel Ledger):"))
    recent = gs.ledger[-n:]
    for e in reversed(recent):
        if e.player_id >= 0:
            p = gs.players[e.player_id]
            who = f"{p.archetype.glyph} {p.archetype.name}"
        else:
            who = "★ Plateau"

        if e.entry_type == "contradiction":
            prefix = c("RED", "  ⚡ CONTRADICTION")
        elif e.entry_type == "moment":
            prefix = c("GREEN", "  ✦ MOMENT")
        else:
            prefix = c("CYAN", "  ~ PATTERN")

        text_lines = textwrap.wrap(e.text, width=58)
        print(f"{prefix}  T{e.turn} | {who}")
        for line in text_lines:
            print(f"     {c('DIM', line)}")

def render_log(gs: GameState, n: int = 8) -> None:
    if not gs.log:
        return
    print()
    print(c("DIM", f"LOG (derniers {n}):"))
    for entry in gs.log[-n:]:
        print(c("DIM", f"  {entry}"))

def render_full(gs: GameState) -> None:
    render_header(gs)
    render_players(gs)
    render_territories(gs)
    render_ledger(gs)

def render_victory(gs: GameState, winner: Player) -> None:
    print()
    print(c("YELLOW", "╔══════════════════════════════════════════════════════╗"))
    print(c("YELLOW", "║") + c("GREEN", f"     VICTOIRE: {winner.archetype.glyph} {winner.archetype.name:<40}") + c("YELLOW", "║"))
    print(c("YELLOW", "╚══════════════════════════════════════════════════════╝"))
    print()
    print(f"  Territoires: {len(winner.territories)}/6")
    print(f"  Zols finaux: {winner.zols:,}")
    acc = int(100 * winner.accuracy) if (winner.total_correct + winner.total_wrong) > 0 else 0
    print(f"  Précision QCM: {acc}% ({winner.total_correct}✓ / {winner.total_wrong}✗)")
    print(f"  Duels: {winner.duels_won}W / {winner.duels_lost}L")
    print()
    print(c("CYAN", f"  Insight: {winner.archetype.insight_win}"))
    print()

    # Ledger summary
    contradictions = [e for e in gs.ledger if e.entry_type == "contradiction"]
    if contradictions:
        print(c("YELLOW", f"  Contradictions enregistrées: {len(contradictions)}"))
        for e in contradictions[-3:]:
            p = gs.players[e.player_id] if e.player_id >= 0 else None
            who = p.archetype.name if p else "Plateau"
            print(c("DIM", f"    · {who}: {e.text[:60]}…"))

    print()
    # Final question: qui gagne vraiment?
    if winner.accuracy > 0.65:
        print(c("GREEN", "  → Le cultivé a gagné. La connaissance était le vrai moteur."))
    elif winner.duels_won >= 3:
        print(c("RED", "  → Le stratège a gagné. La conquête était le vrai moteur."))
    elif winner.archetype.start_zols_bonus > 0:
        print(c("YELLOW", "  → L'argent de départ a-t-il fait la différence? Analyse à 100 parties."))
    else:
        print(c("CYAN", "  → Leçon en cours. Répéter pour savoir qui gagne vraiment."))

# ═══════════════════════════════════════════════════════════════
# BOUCLE PRINCIPALE
# ═══════════════════════════════════════════════════════════════

def game_loop(gs: GameState, interactive: bool = True) -> None:
    _clear()
    render_full(gs)

    max_turns = 200  # safety

    while gs.winner is None and gs.turn <= max_turns:
        player = gs.players[gs.current_player]

        if interactive and not gs.demo_mode:
            # Allow some meta-commands
            raw = input(c("DIM", f"\n[T{gs.turn} | {player.archetype.glyph} {player.archetype.name}] > ")).strip().lower()
            if raw in ("q", "quit", "exit"):
                print("Au revoir.")
                return
            elif raw in ("l", "log"):
                render_log(gs, 20)
                continue
            elif raw in ("m", "map"):
                render_territories(gs)
                continue
            elif raw in ("r", "ledger"):
                render_ledger(gs, 15)
                continue
            elif raw in ("s", "status"):
                render_full(gs)
                continue
            elif raw == "help":
                print_help()
                continue
            # Any other input falls through to process_turn

        process_turn(gs, player, interactive=interactive)

        # Check victory
        gs.winner = check_victory(gs)
        if gs.winner:
            break

        # Advance player
        gs.current_player = (gs.current_player + 1) % len(gs.players)

        # Epoch advance
        gs.turns_in_epoch += 1
        if gs.turns_in_epoch >= 6:
            gs.epoch_idx = (gs.epoch_idx + 1) % len(EPOCHS)
            gs.turns_in_epoch = 0
            ep_name, ep_desc = EPOCHS[gs.epoch_idx]
            print()
            print(c("YELLOW", f"  ★ NOUVELLE ÉPOQUE: {ep_name} — {ep_desc}"))
            add_ledger(gs, -1, "moment", f"Époque {gs.epoch_idx+1}: {ep_name}. {ep_desc}.")

        gs.turn += 1

        if interactive and not gs.demo_mode:
            print()
            render_players(gs)

    if gs.winner:
        render_victory(gs, gs.winner)
    elif gs.turn > max_turns:
        print(c("YELLOW", f"\nPartie terminée après {max_turns} tours (limite atteinte)."))
        # Declare winner by zols
        winner = max(gs.players, key=lambda p: p.zols + len(p.territories) * 10000)
        gs.winner = winner
        render_victory(gs, winner)


def print_help():
    print()
    print(c("YELLOW", "COMMANDES:"))
    print("  [Entrée]   — Jouer le tour du joueur actif")
    print("  l / log    — Afficher le journal complet")
    print("  m / map    — Afficher les territoires")
    print("  r / ledger — Afficher le registre des révélations")
    print("  s / status — Afficher l'état complet")
    print("  q / quit   — Quitter")

# ═══════════════════════════════════════════════════════════════
# DEMO (headless)
# ═══════════════════════════════════════════════════════════════

def run_demo(seed: int, num_players: int = 4) -> None:
    print(c("YELLOW", f"CONQUEST — Démo automatique (seed={seed}, {num_players} joueurs)"))
    print(c("DIM", "Simulation de la mécanique exacte du plateau physique.\n"))
    gs = new_game(seed, num_players, demo=True)
    render_players(gs)
    game_loop(gs, interactive=False)

    # Final stats
    print()
    print(c("CYAN", "══ STATISTIQUES FINALES ══"))
    for p in gs.players:
        acc = int(100 * p.accuracy) if (p.total_correct + p.total_wrong) > 0 else 0
        print(f"  {p.archetype.glyph} {p.archetype.name:<14}"
              f"  {p.zols:>9,}z"
              f"  QCM:{acc}%"
              f"  Duels:{p.duels_won}W/{p.duels_lost}L"
              f"  Terr:{len(p.territories)}")

    print()
    print(c("CYAN", "══ REGISTRE COMPLET ══"))
    for e in gs.ledger:
        if e.player_id >= 0:
            who = gs.players[e.player_id].archetype.name
        else:
            who = "Plateau"
        marker = "⚡" if e.entry_type == "contradiction" else "✦"
        print(c("DIM", f"  T{e.turn:03d} {marker} {who}: {e.text[:70]}"))

# ═══════════════════════════════════════════════════════════════
# ENTRÉE
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print("CONQUEST — Le Plateau en Mouvement v1.0")
        print("Usage: python3 plateau.py [SEED] [--demo] [--players N]")
        print("  SEED       seed déterministe (défaut: aléatoire)")
        print("  --demo     démo automatique (sans interaction)")
        print("  --players  nombre de joueurs (2-6, défaut: 4)")
        sys.exit(0)

    demo = "--demo" in args
    if "--demo" in args: args.remove("--demo")

    num_players = 4
    if "--players" in args:
        idx = args.index("--players")
        try:
            num_players = max(2, min(6, int(args[idx+1])))
            args.pop(idx); args.pop(idx)
        except (ValueError, IndexError):
            pass

    seed = int(args[0]) if args and args[0].isdigit() else random.randint(1, 99999)

    print(c("YELLOW", "╔══════════════════════════════════════════════╗"))
    print(c("YELLOW", "║  CONQUEST — Le Plateau en Mouvement  v1.0    ║"))
    print(c("YELLOW", f"║  Seed: {seed:<6}   Joueurs: {num_players}                    ║"))
    print(c("YELLOW", "║  Le savoir mène au pouvoir.                  ║"))
    print(c("YELLOW", "╚══════════════════════════════════════════════╝"))

    if demo:
        run_demo(seed, num_players)
    else:
        gs = new_game(seed, num_players, demo=False)
        game_loop(gs, interactive=True)


if __name__ == "__main__":
    main()

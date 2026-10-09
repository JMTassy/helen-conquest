#!/usr/bin/env python3
"""Decision-model pilot (Unsloth FastDecisionModel on Qwen3.5-4B) for customer-care triage. Local, research.

NON_SOVEREIGN · authority=false. The model PROPOSES a routing with a calibrated probability; it never decides.
Rules that can be written stay rules (see RULES_THAT_STAY_RULES); low-confidence cases go to a person.

    python decision_pilot.py check                              # versions, GPU, disk; downloads nothing
    python decision_pilot.py synth --out runs/care_synth.jsonl  # synthetic French care tickets with gold
    python decision_pilot.py baselines --data runs/care_synth.jsonl
    python decision_pilot.py train --data public --out runs/public          # step 1: reproduce the notebook
    python decision_pilot.py train --data runs/care_synth.jsonl --out runs/synth   # step 2
    # step 3, only on JM's word, data and outputs stay on this machine:
    python decision_pilot.py train --data client.jsonl --source-kind client --allow-client-data --out runs/client

Rows are {state, questions, gold} as FastDecisionModel.build_dataset expects (checked in unsloth 2026.10.3):
questions = {name: {"type": "choice"|"noul"|"score", "instructions": str, "criteria": dict|list}},
gold = {name: option key | true/false | level index}.

Measured on a held-out test split of rows (ours, by hash, never trained on): accuracy per question, expected
calibration error, the share of decisions above confidence thresholds and their accuracy (what could be
proposed automatically vs sent to a person), and the same accuracy for two baselines without a model
(majority answer, keyword rules). A model that does not beat the keyword rules is not worth its cost.
"""
import argparse
import hashlib
import json
import pathlib
import platform
import random
import re
import shutil
import sys

PINNED = {"unsloth": "2026.10.3", "unsloth_zoo": "2026.10.3", "transformers": "5.2.0", "trl": "0.22.2"}
BASE_MODEL = "unsloth/Qwen3.5-4B"          # Qwen/Qwen3.5-4B is Apache-2.0
PUBLIC_DATA = "LocalLLaMA/typed-decisions"  # Apache-2.0, synthetic
LICENCE_NOTES = ["Qwen3.5-4B: Apache-2.0", "typed-decisions dataset: Apache-2.0",
                 "unsloth package: Apache-2.0, but its decision-model files (unsloth/models/decision*.py) are "
                 "AGPL-3.0-only: fine for local research; review before serving it to others or in a client product",
                 "unsloth_zoo: LGPL-3.0-or-later"]
THRESHOLDS = (0.6, 0.7, 0.8, 0.9)
TEST_SHARE = 0.2

# ------------------------------------------------------------------ the care questions (no client data)

QUESTIONS = {
    "motif": {"type": "choice", "instructions": "Quel est le motif principal du message ?",
              "criteria": {"livraison": "retard, colis perdu ou abîmé, suivi",
                           "produit_defectueux": "flacon cassé, vernis épais, sec, qui ne tient pas",
                           "reaction_cutanee": "irritation, allergie, rougeur, démangeaison",
                           "retour_remboursement": "retour d'un article, demande de remboursement",
                           "modification_commande": "changer l'adresse, annuler, ajouter un article",
                           "conseil_produit": "choix de teinte, tenue, lampe, application, dépose",
                           "autre": "aucun des autres motifs"}},
    "remboursement": {"type": "noul", "instructions": "Le client demande-t-il un remboursement ?"},
    "urgence": {"type": "score", "instructions": "Quelle est l'urgence ?",
                "criteria": ["pas urgent", "sous 48 heures", "aujourd'hui"]},
}

# A deterministic rule beats a learned guess when it can be written down. These never go through the model.
RULES_THAT_STAY_RULES = {
    "reaction_cutanee": "any skin-reaction word routes to a person immediately, whatever the model says",
    "case_still_open": "whether a historical case is still open is a lookup in the case records, not a prediction",
}

_TEMPLATES = {
    "livraison": ["Ma commande {cmd} n'est toujours pas arrivée, ça fait {n} jours.",
                  "Le suivi indique livré mais je n'ai rien reçu (commande {cmd}).",
                  "Colis reçu ouvert et abîmé, il manque {produit}.",
                  "Bonjour, où en est ma livraison {cmd} ? Je pars {quand}."],
    "produit_defectueux": ["Le flacon de {produit} est arrivé cassé.",
                           "Mon {produit} est devenu épais au bout de {n} jours.",
                           "Le vernis {produit} s'écaille dès le lendemain, c'est normal ?",
                           "Le pinceau du {produit} est abîmé, impossible d'appliquer."],
    "reaction_cutanee": ["J'ai des rougeurs autour des ongles depuis que j'utilise {produit}.",
                         "Démangeaisons et irritation après la pose de {produit}, que faire ?",
                         "Je pense faire une allergie au {produit}, mes doigts gonflent."],
    "retour_remboursement": ["Je souhaite retourner {produit}, la teinte ne me plaît pas.",
                             "Pouvez-vous me rembourser la commande {cmd} ?",
                             "Comment faire un retour pour {produit} ?"],
    "modification_commande": ["Je me suis trompée d'adresse pour la commande {cmd}, pouvez-vous la changer ?",
                              "Est-il possible d'annuler la commande {cmd} ?",
                              "Puis-je ajouter {produit} à ma commande {cmd} ?"],
    "conseil_produit": ["Quelle teinte proche de {produit} me conseillez-vous pour l'été ?",
                        "Combien de temps tient {produit} avec la lampe ?",
                        "Comment déposer {produit} sans abîmer l'ongle ?",
                        "{produit} convient-il aux ongles fragiles ?"],
    "autre": ["Vous recrutez en ce moment ?", "J'adore vos produits, merci !",
              "Avez-vous une boutique à {ville} ?"],
}
_REFUND_ADDONS = ["Je veux être remboursée.", "Merci de me rembourser.", "Je demande un remboursement."]
_URGENT_ADDONS = {2: ["C'est urgent, c'est pour aujourd'hui.", "Réponse aujourd'hui svp, je pars ce soir."],
                  1: ["Merci de revenir vers moi rapidement.", "J'en ai besoin cette semaine."]}
_FILL = {"produit": ["Coral Reef", "Pistachio", "Active Glow", "la base Green Flash", "le top coat", "Chestnut"],
         "cmd": ["#40{0}".format(i) for i in range(10, 99, 7)], "n": ["3", "5", "8", "12", "15"],
         "quand": ["demain", "samedi", "dans deux jours"], "ville": ["Lyon", "Nantes", "Bordeaux"]}


def _typo(text, rng):
    if rng.random() < 0.25 and len(text) > 20:          # drop one character, as people do
        i = rng.randrange(5, len(text) - 5)
        text = text[:i] + text[i + 1:]
    if rng.random() < 0.2:
        text = text.lower()
    return text


def synth_rows(n=600, seed=3407):
    """Synthetic tickets with known gold. Deterministic for a seed. Not client data."""
    rng = random.Random(seed)
    rows = []
    motives = list(_TEMPLATES)
    weights = [0.24, 0.16, 0.06, 0.16, 0.12, 0.2, 0.06]   # skewed like a real inbox: majority baseline is not trivial
    for i in range(n):
        motif = rng.choices(motives, weights)[0]
        text = rng.choice(_TEMPLATES[motif]).format(**{k: rng.choice(v) for k, v in _FILL.items()})
        refund = motif == "retour_remboursement" and rng.random() < 0.7
        if motif in ("livraison", "produit_defectueux") and rng.random() < 0.35:
            refund = True
        if refund and rng.random() < 0.6:
            text += " " + rng.choice(_REFUND_ADDONS)
        urg = 2 if motif == "reaction_cutanee" else rng.choices([0, 1, 2], [0.55, 0.3, 0.15])[0]
        if urg and rng.random() < 0.75:
            text += " " + rng.choice(_URGENT_ADDONS[urg])
        rows.append({"id": f"synth-{i:04d}", "state": _typo(text, rng), "questions": QUESTIONS,
                     "gold": {"motif": motif, "remboursement": refund, "urgence": urg}})
    return rows


# ------------------------------------------------------------------ split, baselines, metrics (no GPU)

def is_test(row_id):
    return int(hashlib.sha256(str(row_id).encode()).hexdigest(), 16) % 1000 < TEST_SHARE * 1000


def split(rows):
    train, test = [], []
    for i, r in enumerate(rows):
        (test if is_test(r.get("id", i)) else train).append(r)
    return train, test


def norm_gold(kind, g):
    g = _parsed(g) if isinstance(g, str) and g[:1] == "{" else g
    if isinstance(g, dict):                      # gold given as {"label": ..., "probabilities": ...}
        g = g.get("label", g.get("noul"))
    if kind == "noul":
        return str(g).lower() in ("true", "1", "yes", "oui")
    if kind == "score":
        try:
            return int(g)
        except (TypeError, ValueError):
            return str(g)
    return str(g)


_KW = {"reaction_cutanee": r"rougeur|irritation|allergi|démang|demang|gonfl",
       "livraison": r"livr|colis|suivi|arriv|reçu|recu",
       "retour_remboursement": r"retour|rembours",
       "modification_commande": r"adresse|annuler|ajouter",
       "produit_defectueux": r"cass|épais|epais|écaill|ecaill|pinceau|abîm|abim",
       "conseil_produit": r"conseil|teinte|tient|déposer|deposer|convient"}


def keyword_answer(name, text):
    t = text.lower()
    if name == "motif":
        for motif, pat in _KW.items():               # order = priority, skin reaction first
            if re.search(pat, t):
                return motif
        return "autre"
    if name == "remboursement":
        return bool(re.search(r"rembours", t))
    if name == "urgence":
        return 2 if re.search(r"urgent|aujourd'hui|ce soir|rougeur|allergi|démang|gonfl", t) else (
            1 if re.search(r"rapidement|cette semaine|demain", t) else 0)
    return None


def ece(conf, correct, bins=10):
    """Expected calibration error: sum over confidence bins of |accuracy - mean confidence| x bin share."""
    n = len(conf)
    if n == 0:
        return None
    total = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(conf) if (lo < c <= hi) or (b == 0 and c == 0)]
        if idx:
            acc = sum(correct[i] for i in idx) / len(idx)
            mc = sum(conf[i] for i in idx) / len(idx)
            total += abs(acc - mc) * len(idx) / n
    return round(total, 4)


def coverage(conf, correct, thresholds=THRESHOLDS):
    out = {}
    for t in thresholds:
        idx = [i for i, c in enumerate(conf) if c >= t]
        out[str(t)] = {"share_auto": round(len(idx) / max(len(conf), 1), 3),
                       "accuracy_auto": round(sum(correct[i] for i in idx) / len(idx), 3) if idx else None}
    return out


def score_answers(rows, answer_fn):
    """answer_fn(row, name) -> (answer, confidence or None). Returns per-question accuracy (+ calibration)."""
    per = {}
    for r in rows:
        qs = _parsed(r["questions"])
        gold = _parsed(r["gold"])
        for name, q in qs.items():
            if name not in gold:
                continue
            a, c = answer_fn(r, name)
            ok = norm_gold(q["type"], a) == norm_gold(q["type"], gold[name])
            d = per.setdefault(name, {"correct": [], "conf": []})
            d["correct"].append(1.0 if ok else 0.0)
            if c is not None:
                d["conf"].append(float(c))
    out = {}
    for name, d in per.items():
        m = {"n": len(d["correct"]), "accuracy": round(sum(d["correct"]) / len(d["correct"]), 3)}
        if len(d["conf"]) == len(d["correct"]):
            m["ece"] = ece(d["conf"], d["correct"])
            m["coverage"] = coverage(d["conf"], d["correct"])
        out[name] = m
    return out


def baselines(train, test):
    majority = {}
    for r in train:
        for name, g in _parsed(r["gold"]).items():
            majority.setdefault(name, {}).setdefault(json.dumps(g), 0)
            majority[name][json.dumps(g)] += 1
    maj = {n: json.loads(max(c, key=c.get)) for n, c in majority.items()}
    res = {"majority": score_answers(test, lambda r, n: (maj.get(n), None))}
    if all(set(_parsed(r["questions"])) <= set(QUESTIONS) for r in test):
        res["keyword_rules"] = score_answers(test, lambda r, n: (keyword_answer(n, _state_text(r)), None))
    return res


def _parsed(v):
    return json.loads(v) if isinstance(v, str) else v


def _state_text(r):
    s = _parsed(r["state"]) if isinstance(r["state"], str) and r["state"][:1] in "{[" else r["state"]
    return s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)


def read_rows(path):
    return [json.loads(line) for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


# ------------------------------------------------------------------ GPU side (HAL·WITNESS machine)

def preflight():
    info = {"python": platform.python_version(), "pinned": PINNED, "licences": LICENCE_NOTES, "problems": []}
    try:
        import torch
        info["torch"] = torch.__version__
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            info["gpu"], info["vram_gb"] = p.name, round(p.total_memory / 2 ** 30, 1)
            info["bf16"] = bool(torch.cuda.is_bf16_supported())
            if info["vram_gb"] < 8:
                info["problems"].append(f"{info['vram_gb']} GB VRAM; the notebook needs about 8 GB in 4-bit")
        else:
            info["problems"].append("no CUDA GPU visible to torch")
    except ImportError:
        info["problems"].append("torch not installed")
    for pkg, want in PINNED.items():
        try:
            from importlib.metadata import version
            have = version(pkg)
            info[pkg] = have
            if have != want:
                info["problems"].append(f"{pkg} {have} installed, {want} pinned")
        except Exception:  # noqa: BLE001
            info["problems"].append(f"{pkg} not installed")
    try:
        free = shutil.disk_usage(pathlib.Path.home()).free / 2 ** 30
        info["disk_free_gb"] = round(free, 1)
        if free < 30:
            info["problems"].append(f"{free:.0f} GB free; keep 30 GB for the model and runs")
    except OSError:
        pass
    return info


def train(args):
    import torch
    from transformers import TrainingArguments
    from unsloth import DecisionTrainer, FastDecisionModel, is_bfloat16_supported

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.data == "public":
        from datasets import load_dataset
        all_rows = [dict(r, id=f"public-train-{i}") for i, r in enumerate(load_dataset(PUBLIC_DATA, "all", split="train"))]
        train_rows = all_rows
        test_rows = [dict(r, id=f"public-test-{i}") for i, r in enumerate(load_dataset(PUBLIC_DATA, "all", split="test"))]
    else:
        train_rows, test_rows = split(read_rows(args.data))
    report = {"status": "NON_SOVEREIGN", "authority": False, "use": "local research pilot; proposals, not decisions",
              "data": args.data if args.source_kind != "client" else "client (path not recorded)",
              "source_kind": args.source_kind, "licences": LICENCE_NOTES, "environment": preflight(),
              "rows": {"train": len(train_rows), "test": len(test_rows)},
              "rules_that_stay_rules": RULES_THAT_STAY_RULES}
    report["baselines_on_test"] = baselines(train_rows, test_rows)

    model, tokenizer = FastDecisionModel.from_pretrained(model_name=BASE_MODEL, revision=args.revision,
                                                         max_seq_length=2048, load_in_4bit=True)
    model = FastDecisionModel.get_peft_model(model, r=16, lora_alpha=16, lora_dropout=0,
                                             use_gradient_checkpointing="unsloth", random_state=3407)
    items, build = FastDecisionModel.build_dataset(train_rows, tokenizer, model)
    report["build_train"] = build
    if args.data != "public" and build["skipped"]:
        raise SystemExit(f"{build['skipped']} decisions skipped while building the data ({build}); fix the rows first")
    train_items, calib_items = FastDecisionModel.split_holdout(items, seed=3407)
    report["before_training_on_calibration_rows"] = FastDecisionModel.evaluate(model, tokenizer, calib_items)
    trainer = DecisionTrainer(model=model, processing_class=tokenizer, train_dataset=train_items,
                              eval_dataset=calib_items,
                              args=TrainingArguments(per_device_train_batch_size=8, gradient_accumulation_steps=4,
                                                     warmup_steps=10, max_steps=args.max_steps, learning_rate=2e-4,
                                                     lr_scheduler_type="cosine", weight_decay=0.01,
                                                     bf16=is_bfloat16_supported(), fp16=not is_bfloat16_supported(),
                                                     eval_strategy="no", logging_steps=10, output_dir=str(out / "trainer"),
                                                     report_to="none", seed=3407))
    stats = trainer.train()
    report["training"] = {"max_steps": args.max_steps, "seconds": stats.metrics.get("train_runtime"),
                          "peak_gb": round(torch.cuda.max_memory_reserved() / 2 ** 30, 2)}
    report["calibration"] = FastDecisionModel.calibrate(model, tokenizer, calib_items)
    test_items, build_test = FastDecisionModel.build_dataset(test_rows, tokenizer, model)
    report["unsloth_evaluate_on_test"] = FastDecisionModel.evaluate(model, tokenizer, test_items)

    FastDecisionModel.for_inference(model)
    cache = {}

    def answer(r, name):
        key = r.get("id") or _state_text(r)
        if key not in cache:
            cache[key] = FastDecisionModel.predict(model, tokenizer, _parsed(r["state"]), _parsed(r["questions"]))
        a = cache[key][name]
        return a["answer"], max(a["probabilities"].values())

    report["model_on_test"] = score_answers(test_rows, answer)
    model.save_pretrained(str(out / "adapter"))     # local only; this script never uploads anything
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({"baselines": report["baselines_on_test"], "model": report["model_on_test"]}, indent=1, ensure_ascii=False))
    print("Proposals only. Compare with the keyword rules before drawing any conclusion. Keep runs/ local.")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    s = sub.add_parser("synth")
    s.add_argument("--out", required=True)
    s.add_argument("--n", type=int, default=600)
    s.add_argument("--seed", type=int, default=3407)
    b = sub.add_parser("baselines")
    b.add_argument("--data", required=True)
    t = sub.add_parser("train")
    t.add_argument("--data", required=True, help='"public" or a .jsonl of {id, state, questions, gold}')
    t.add_argument("--source-kind", choices=["public", "synthetic", "client"], default=None)
    t.add_argument("--allow-client-data", action="store_true")
    t.add_argument("--max-steps", type=int, default=60)
    t.add_argument("--revision", default=None, help="Hugging Face commit of the base model; pin after the first run")
    t.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "check":
        info = preflight()
        print(json.dumps(info, indent=1, ensure_ascii=False))
        return info
    if args.cmd == "synth":
        rows = synth_rows(args.n, args.seed)
        p = pathlib.Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        print(f"{len(rows)} synthetic rows -> {p}")
        return rows
    if args.cmd == "baselines":
        tr, te = split(read_rows(args.data))
        res = baselines(tr, te)
        print(json.dumps(res, indent=1, ensure_ascii=False))
        return res
    kind = args.source_kind or ("public" if args.data == "public" else None)
    if kind is None:
        ap.error("--source-kind is required for a data file (synthetic or client)")
    if kind == "client" and not args.allow_client_data:
        ap.error("client data refused: run public and synthetic first; add --allow-client-data only on JM's word")
    args.source_kind = kind
    return train(args)


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)

# ORACLE SUPERTEAM — Academic Paper

## Quick Start

### Option 1: Using the compilation script (recommended)
```bash
cd paper
./compile.sh
```

### Option 2: Using Makefile
```bash
cd paper
make all      # Generate figures and compile PDF
make view     # Compile and open PDF
make clean    # Remove auxiliary files
```

### Option 3: Manual compilation
```bash
cd paper

# Generate city map (requires Graphviz)
mkdir -p figures
dot -Tpng ../viz/oracle_town.dot -o figures/oracle_town.png

# Compile PDF
pdflatex oracle_superteam.tex
bibtex oracle_superteam
pdflatex oracle_superteam.tex
pdflatex oracle_superteam.tex
```

---

## Requirements

### Required:
- **LaTeX** (pdflatex, bibtex)
  - macOS: `brew install --cask mactex-no-gui`
  - Ubuntu: `sudo apt-get install texlive-full`
  - Windows: https://miktex.org/download

### Optional:
- **Graphviz** (for city map figure)
  - macOS: `brew install graphviz`
  - Ubuntu: `sudo apt-get install graphviz`

---

## File Structure

```
paper/
├── oracle_superteam.tex    # Main LaTeX document
├── references.bib          # Bibliography (BibTeX)
├── compile.sh              # Simple compilation script
├── Makefile                # Make-based build system
├── figures/                # Generated figures (auto-created)
│   └── oracle_town.png     # Governance city map
└── README.md               # This file
```

---

## Paper Sections

1. **Abstract** — Governance-centric framework overview
2. **Introduction** — Motivation and contributions
3. **System Axioms** — 5 non-negotiable constitutional guarantees
4. **Formal Model** — Mathematical definitions
5. **Three-Layer Architecture** — Production, Adjudication, Integration
6. **QI-INT v2** — Complex amplitude scoring
7. **Replay Determinism** — Canonicalization protocol
8. **Test Vault Validation** — 10 adversarial scenarios
9. **Threat Model** — Security analysis
10. **Related Work** — Comparison with existing systems
11. **Future Work** — Extensions and research directions
12. **Conclusion**

---

## Output

**Generated file:** `oracle_superteam.pdf`

**Expected size:** ~300-400 KB (15-20 pages)

---

## Compilation Targets

| Target | Command | Description |
|--------|---------|-------------|
| Full build | `make all` | Generate figures and compile PDF |
| Quick compile | `make quick` | Compile without bibliography |
| View PDF | `make view` | Compile and open in viewer |
| Clean | `make clean` | Remove auxiliary files |
| Deep clean | `make distclean` | Remove all generated files |

---

## Troubleshooting

### "pdflatex: command not found"
Install LaTeX distribution (see Requirements above).

### "dot: command not found"
Install Graphviz or skip figure generation (city map).

### Bibliography not appearing
Ensure `bibtex` is installed and run full compilation (3 passes).

### Missing fonts/packages
Install full TeX Live distribution:
```bash
# macOS
brew install --cask mactex

# Ubuntu
sudo apt-get install texlive-full
```

---

## Submission Ready

This paper is ready for submission to:
- **NeurIPS** (Conference on Neural Information Processing Systems)
- **ICML** (International Conference on Machine Learning)
- **EAAMO** (Equity and Access in Algorithms, Mechanisms, and Optimization)
- **AAAI** (Association for the Advancement of Artificial Intelligence)
- **ArXiv** (preprint server)

---

## Citation

```bibtex
@article{tassy2026oracle,
  title={ORACLE SUPERTEAM: A Governance-Centric Multi-Agent Framework for Deterministic, Evidence-Bound Decision-Making},
  author={Tassy Simeoni, Jean Marie},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2026}
}
```

---

## License

See repository LICENSE file.

---

**ORACLE SUPERTEAM is not a conversation. It is an institution.**

# ORACLE SUPERTEAM Paper — Makefile

# Main LaTeX file
MAIN = oracle_superteam
LATEX = pdflatex
BIBTEX = bibtex

# Output directory
BUILD_DIR = build

.PHONY: all clean figures pdf view

all: figures pdf

# Generate figures
figures:
	@echo "Generating figures..."
	@mkdir -p figures
	@if command -v dot >/dev/null 2>&1; then \
		dot -Tpng ../viz/oracle_town.dot -o figures/oracle_town.png; \
		echo "✓ City map generated"; \
	else \
		echo "⚠  Graphviz not installed. Skipping city map generation."; \
		echo "  Install with: brew install graphviz (macOS) or apt-get install graphviz (Linux)"; \
	fi

# Compile PDF
pdf: figures
	@echo "Compiling LaTeX document..."
	@$(LATEX) $(MAIN).tex
	@if [ -f $(MAIN).aux ]; then $(BIBTEX) $(MAIN); fi
	@$(LATEX) $(MAIN).tex
	@$(LATEX) $(MAIN).tex
	@echo "✓ PDF compiled: $(MAIN).pdf"

# View PDF
view: pdf
	@if command -v open >/dev/null 2>&1; then \
		open $(MAIN).pdf; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open $(MAIN).pdf; \
	else \
		echo "Cannot open PDF viewer. Please open $(MAIN).pdf manually."; \
	fi

# Clean auxiliary files
clean:
	@echo "Cleaning auxiliary files..."
	@rm -f *.aux *.log *.bbl *.blg *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
	@echo "✓ Cleaned"

# Clean everything including PDF
distclean: clean
	@rm -f $(MAIN).pdf
	@rm -rf figures
	@echo "✓ Deep cleaned"

# Quick compile (no bibliography)
quick:
	@$(LATEX) $(MAIN).tex
	@echo "✓ Quick compile complete"

# Help
help:
	@echo "ORACLE SUPERTEAM Paper — Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make all      - Generate figures and compile PDF"
	@echo "  make pdf      - Compile PDF with bibliography"
	@echo "  make figures  - Generate figures (city map)"
	@echo "  make view     - Compile and open PDF"
	@echo "  make clean    - Remove auxiliary files"
	@echo "  make distclean- Remove all generated files"
	@echo "  make quick    - Quick compile (no bibtex)"
	@echo ""
	@echo "Requirements:"
	@echo "  - pdflatex (TeX Live or MiKTeX)"
	@echo "  - bibtex"
	@echo "  - graphviz (optional, for city map)"

#!/bin/bash
# ORACLE SUPERTEAM Paper — Simple Compilation Script

echo "========================================"
echo "ORACLE SUPERTEAM — Paper Compilation"
echo "========================================"
echo ""

# Check for pdflatex
if ! command -v pdflatex &> /dev/null; then
    echo "❌ pdflatex not found!"
    echo ""
    echo "Please install LaTeX:"
    echo "  macOS:  brew install --cask mactex-no-gui"
    echo "  Ubuntu: sudo apt-get install texlive-full"
    echo "  Windows: https://miktex.org/download"
    exit 1
fi

# Generate figures if graphviz available
echo "Step 1: Generating figures..."
mkdir -p figures

if command -v dot &> /dev/null; then
    dot -Tpng ../viz/oracle_town.dot -o figures/oracle_town.png
    echo "✓ City map generated"
else
    echo "⚠  Graphviz not installed (optional)"
    echo "   Install: brew install graphviz"
fi

# Compile LaTeX
echo ""
echo "Step 2: Compiling LaTeX (Pass 1/3)..."
pdflatex -interaction=nonstopmode oracle_superteam.tex > /dev/null 2>&1

if [ -f oracle_superteam.aux ]; then
    echo "Step 3: Processing bibliography..."
    bibtex oracle_superteam > /dev/null 2>&1 || echo "⚠  Bibliography warnings (non-fatal)"
fi

echo "Step 4: Compiling LaTeX (Pass 2/3)..."
pdflatex -interaction=nonstopmode oracle_superteam.tex > /dev/null 2>&1

echo "Step 5: Compiling LaTeX (Pass 3/3)..."
pdflatex -interaction=nonstopmode oracle_superteam.tex > /dev/null 2>&1

echo ""
if [ -f oracle_superteam.pdf ]; then
    echo "✅ SUCCESS! PDF generated: oracle_superteam.pdf"

    # Get file size
    SIZE=$(du -h oracle_superteam.pdf | cut -f1)
    echo "   File size: $SIZE"

    # Try to open
    echo ""
    echo "Opening PDF..."
    if command -v open &> /dev/null; then
        open oracle_superteam.pdf
    elif command -v xdg-open &> /dev/null; then
        xdg-open oracle_superteam.pdf
    else
        echo "   Please open oracle_superteam.pdf manually"
    fi
else
    echo "❌ FAILED! PDF not generated"
    echo "   Check oracle_superteam.log for errors"
    exit 1
fi

echo ""
echo "To clean auxiliary files: rm *.aux *.log *.bbl *.blg *.out"
echo "========================================"

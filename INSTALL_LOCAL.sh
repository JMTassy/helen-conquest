#!/bin/bash

# HELEN OS — Local Installation Script
# Installs HELEN OS with multi-model support on this machine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║        🧠 HELEN OS — LOCAL INSTALLATION 🧠                     ║"
echo "║                                                                ║"
echo "║         Multi-Model Unified AI Companion Setup                ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${RED}❌ Python 3.9+ required${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python version OK${NC}\n"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}  Virtual environment already exists, skipping creation${NC}"
else
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}\n"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel --quiet
echo -e "${GREEN}✅ pip upgraded${NC}\n"

# Install requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}\n"

# Create configuration directory
echo -e "${YELLOW}Setting up configuration directory...${NC}"
mkdir -p ~/.helen_os
echo -e "${GREEN}✅ Configuration directory: ~/.helen_os${NC}\n"

# Create .env template
echo -e "${YELLOW}Creating .env template...${NC}"
ENV_FILE=~/.helen_os/.env

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# ============================================================================
# HELEN OS — API Keys Configuration
# ============================================================================

# Anthropic Claude
ANTHROPIC_API_KEY=

# OpenAI GPT
OPENAI_API_KEY=

# xAI Grok
XAI_API_KEY=

# Google Gemini
GOOGLE_API_KEY=

# Alibaba Qwen
QWEN_API_KEY=

# ============================================================================
# DEPLOYMENT SETTINGS
# ============================================================================

HELEN_ENVIRONMENT=local
HELEN_DEBUG=false
HELEN_PORT=8000

# ============================================================================
# RUNTIME PREFERENCES
# ============================================================================

HELEN_DEFAULT_MODEL=claude-opus-4-6
HELEN_TEMPERATURE=0.7
HELEN_MAX_TOKENS=2048
HELEN_STREAMING=true
HELEN_AUTO_FALLBACK=true
HELEN_PREFER_LOCAL=true
EOF
    echo -e "${GREEN}✅ .env template created at: $ENV_FILE${NC}"
else
    echo -e "${YELLOW}  .env file already exists, not overwriting${NC}"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${GREEN}✅ Installation Complete!${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}\n"

echo "1. Edit your API keys:"
echo "   nano ~/.helen_os/.env"
echo ""
echo "2. Add your API keys for the models you want to use:"
echo "   • ANTHROPIC_API_KEY (for Claude)"
echo "   • OPENAI_API_KEY (for GPT)"
echo "   • XAI_API_KEY (for Grok)"
echo "   • GOOGLE_API_KEY (for Gemini)"
echo "   • QWEN_API_KEY (for Qwen)"
echo "   • OLLAMA_API_KEY (optional, for local Ollama)"
echo ""
echo "3. (Optional) Install and run Ollama for local LLM:"
echo "   curl https://ollama.ai/install.sh | sh"
echo "   ollama pull llama2"
echo "   ollama serve"
echo ""
echo "4. Start HELEN OS:"
echo "   source .venv/bin/activate"
echo "   python helen_unified_interface_v1.py"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${YELLOW}Supported Models:${NC}\n"
echo "  📍 Ollama (Local)"
echo "     - Llama 2"
echo "     - Mistral"
echo ""
echo "  ☁️  Cloud Models"
echo "     - Claude (Anthropic)"
echo "     - GPT-4 (OpenAI)"
echo "     - Grok (xAI)"
echo "     - Gemini (Google)"
echo "     - Qwen (Alibaba)"
echo ""

echo -e "${YELLOW}Configuration Directory:${NC}"
echo "  Location: ~/.helen_os"
echo "  Files:"
echo "    • .env (API keys)"
echo "    • deployment.json (deployment settings)"
echo "    • runtime.json (runtime preferences)"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "Ready to use HELEN OS! 🚀"
echo ""

#!/bin/bash

# HELEN QUICK START SCRIPT
# Deploymentet up local instance with Gemma 4 + Avatar

set -e

echo "🚀 HELEN LOCAL DEPLOYMENT QUICKSTART"
echo "===================================="
echo ""

# Step 1: Check Docker
echo "✓ Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
echo "  Docker found: $(docker --version)"
echo ""

# Step 2: Navigate to repo
REPO_DIR="/Users/jean-marietassy/Documents/GitHub/helen_os_v1"
echo "✓ Navigating to repository..."
cd "$REPO_DIR"
echo "  Directory: $(pwd)"
echo ""

# Step 3: Copy .env
echo "✓ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from template"
else
    echo "  .env already exists (skipped)"
fi
echo ""

# Step 4: Start deployment
echo "✓ Starting Docker containers..."
echo "  This may take 5 minutes on first run (downloading Gemma 4)..."
echo ""
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 3

# Step 5: Verify services
echo ""
echo "✓ Checking service status..."
docker-compose ps

echo ""
echo "✓ Waiting for Ollama to download Gemma 4 model..."
for i in {1..60}; do
    if docker exec helen_ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "  Ollama ready!"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "✓ Waiting for HELEN API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  API ready!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "✓ Waiting for Avatar frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "  Avatar ready!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "===================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "===================================="
echo ""
echo "🌐 HELEN Avatar: http://localhost:5173"
echo "📡 API Endpoint: http://localhost:8000"
echo "🤖 Ollama Server: http://localhost:11434"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:5173 in your browser"
echo "  2. Chat with HELEN avatar"
echo "  3. View logs: docker-compose logs -f"
echo "  4. Stop: docker-compose down"
echo ""
echo "Documentation: DEPLOYMENT_INSTRUCTIONS.md"
echo ""

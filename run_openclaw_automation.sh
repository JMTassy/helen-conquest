#!/bin/bash
# Run OpenClaw Kernel Automation

set -e

PROJECT_DIR="/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
cd "$PROJECT_DIR"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        OpenClaw Kernel Automation — Starting                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if kernel daemon is already running
if pgrep -f "kernel_daemon.py" > /dev/null; then
    echo "✓ Kernel daemon already running"
    KERNEL_PID=$(pgrep -f "kernel_daemon.py")
else
    echo "Starting kernel daemon..."
    python3 oracle_town/kernel/kernel_daemon.py > kernel_daemon.log 2>&1 &
    KERNEL_PID=$!
    echo "✓ Kernel daemon started (PID: $KERNEL_PID)"
    sleep 2  # Give daemon time to start
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        Running OpenClaw Skills Tests                               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Run the skills tests
python3 openclaw_skills_with_kernel.py

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        Automation Complete                                         ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Kernel daemon is running (PID: $KERNEL_PID)"
echo ""
echo "To monitor decisions:"
echo "  tail -f kernel/ledger.json"
echo ""
echo "To stop kernel daemon:"
echo "  kill $KERNEL_PID"
echo ""

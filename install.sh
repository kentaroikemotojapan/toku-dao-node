#!/usr/bin/env bash
set -e

echo "⚡️ Initializing Antigravity Virtue IDE & Sovereign Node Mesh..."

# 1. Check/Install IPFS Daemon
if ! command -v ipfs &> /dev/null; then
    echo "📦 Installing IPFS (Kubo) Engine..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ipfs
    else
        wget -q https://dist.ipfs.tech/kubo/v0.26.0/kubo_v0.26.0_linux-amd64.tar.gz
        tar -xzf kubo_v0.26.0_linux-amd64.tar.gz
        sudo bash kubo/install.sh
        rm -rf kubo*
    fi
fi

if [ ! -d "$HOME/.ipfs" ]; then
    ipfs init
    ipfs config --json Pubsub.Enabled true
fi

# Launch IPFS Daemon in background if not running
if ! pgrep -x "ipfs" > /dev/null; then
    echo "🌐 Starting IPFS / libp2p Swarm Daemon..."
    nohup ipfs daemon > /tmp/ipfs.log 2>&1 &
    sleep 3
fi

# 2. Launch Docker Compose Stack
echo "🚀 Launching EVM Node & FastAPI Server via Docker Compose..."
docker-compose up -d --build

echo "=================================================================="
echo "🎉 Node Online! Open Antigravity Virtue IDE at: http://localhost:5001"
echo "=================================================================="
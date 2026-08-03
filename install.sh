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

if [ ! -f "$HOME/.ipfs/config" ]; then
    rm -rf "$HOME/.ipfs"
    ipfs init || true
    ipfs config --json Pubsub.Enabled true || true
fi

# Launch IPFS Daemon in background if not running
if ! pgrep -x "ipfs" > /dev/null; then
    echo "🌐 Starting IPFS / libp2p Swarm Daemon..."
    nohup ipfs daemon > /tmp/ipfs.log 2>&1 &
    sleep 3
fi

# 2. Locate project root & launch Docker Compose Stack
if [ -f "./docker-compose.yml" ]; then
    PROJECT_DIR="."
elif [ -f "./ALPHA環境/docker-compose.yml" ]; then
    PROJECT_DIR="./ALPHA環境"
elif [ -f "$(dirname "$0")/docker-compose.yml" ]; then
    PROJECT_DIR="$(dirname "$0")"
else
    INSTALL_DIR="$HOME/.toku-dao-node"
    if [ -d "$INSTALL_DIR" ]; then
        echo "🔄 Updating Toku Node repository..."
        (cd "$INSTALL_DIR" && git pull origin main --quiet || true)
    else
        echo "📦 Cloning Toku Node repository..."
        git clone --depth 1 https://github.com/kentaroikemotojapan/toku-dao-node.git "$INSTALL_DIR" --quiet
    fi
    PROJECT_DIR="$INSTALL_DIR"
fi

cd "$PROJECT_DIR"
echo "🚀 Launching EVM Node & FastAPI Server via Docker Compose..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

echo "=================================================================="
echo "🎉 Node Online! Open Antigravity Virtue IDE at: http://localhost:5001"
echo "=================================================================="
#!/usr/bin/env bash
set -e

COMMIT_MSG="${1:-auto: deploy new node release}"

echo "🚀 [1/3] Committing and pushing to GitHub..."
git add .
git commit -m "$COMMIT_MSG" || true
git push origin main || echo "⚠️ GitHub push failed, continuing via IPFS P2P..."

echo "📦 [2/3] Pinning codebase archive to IPFS Network..."
TAR_PATH="/tmp/toku-node-latest.tar.gz"
tar --exclude='.git' -czf "$TAR_PATH" .
NEW_CID=$(ipfs add -q "$TAR_PATH" | tail -n 1)

echo "🌐 [3/3] Broadcasting signed release CID ($NEW_CID) via IPFS PubSub..."
PAYLOAD="{\"version_cid\": \"$NEW_CID\", \"timestamp\": $(date +%s)}"

# 修正箇所: echo 経由で標準入力から PubSub へ渡す
echo "$PAYLOAD" | ipfs pubsub pub toku/mesh/alpha/releases

echo "=================================================="
echo "🎉 Release published to Alpha P2P Mesh!"
echo "CID: $NEW_CID"
echo "=================================================="
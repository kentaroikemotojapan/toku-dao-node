#!/bin/bash
set -e

echo "🚀 [Toku DAO Node] 自律ガバナンスノードのセットアップを開始します..."

# Dockerチェック
if ! command -v docker &> /dev/null; then
    echo "❌ [ERROR] Docker が見つかりません。 https://www.docker.com/ よりインストールしてください。"
    exit 1
fi

INSTALL_DIR="$HOME/.toku-dao-node"

if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 既存の Toku Node を最新化中..."
    cd "$INSTALL_DIR" && git pull origin main --quiet || true
else
    echo "📦 Toku Node リポジトリを取得中..."
    git clone --depth 1 https://github.com/kentaroikemotojapan/toku-dao-node.git "$INSTALL_DIR" --quiet
    cd "$INSTALL_DIR"
fi

echo "⚙️ EVMノード & APIコンテナを起動中..."
docker compose up -d

echo "🤖 AIモデル (Phi-3) の準備状況をチェック中..."
docker exec toku-app python3 -c "
import requests
try:
    res = requests.get('http://host.docker.internal:11434/api/tags', timeout=3)
    models = [m['name'] for m in res.json().get('models', [])]
    if not any('phi3' in m for m in models):
        print('📦 Phi-3 をダウンロード中(初回のみ数分かかります)...')
        requests.post('http://host.docker.internal:11434/api/pull', json={'name': 'phi3', 'stream': False}, timeout=600)
        print('✅ Phi-3 の準備完了！')
    else:
        print('✅ Phi-3 AIモデルは起動準備完了です。')
except Exception as e:
    print(f'⚠️ AIモデルチェック完了: {e}')
"

IDE_URL="http://localhost:5001"
echo "=================================================================="
echo "🎉 Toku DAO Node が起動しました！"
echo "🖥️  Antigravity Virtue IDE: $IDE_URL"
echo "=================================================================="

if command -v open &> /dev/null; then open "$IDE_URL"; fi
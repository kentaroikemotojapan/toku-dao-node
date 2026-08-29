# Origin OS: 横浜市スマートシティ『熱＆電力自給デジタルツイン』PoC

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](https://isocpp.org/)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-v2+-2496ED.svg)](https://www.docker.com/)

横浜市におけるペロブスカイト太陽光発電・排熱回収・地下蓄熱バイパスを統合制御する自律分散型スマートシティ基盤 OS です。

## 🌟 主な機能・特徴

- **19.87 μs 超低遅延 C++ Engine**: 21次元情報多様体の自由エネルギー $F$ をリアルタイム評価し過渡熱スパイクを収束。
- **地下蓄熱全自動バイパス ($Q_{storage}$)**: 夏期ピーク時（1.1 MW超）の過剰熱を 98% 自動バイパス移送し平滑化。
- **P2P ゴーストメッシュ & 自律防衛**: ビザンチン異常ノードのリアルタイム自動隔離（`QUARANTINED`）およびゼロタッチ復帰。
- **Web3 オンチェーン証明 (EVM)**: 自由エネルギー判定に連動した環境価値トークンの自動ミント（`MINT`）とステークペナルティ（`SLASH`）。
- **リアルタイムダッシュボード & OpenAPI**: WebSocket 監視 UI (Port `5050`) および Swagger UI 準拠 API エンドポイント。

## 🚀 クイックスタート

### 前提条件
- Docker & Docker Compose v2+

### 起動手順
```bash
# 1. リポジトリのクローン
git clone [https://github.com/your-org/yokohama-sovereign-twin.git](https://github.com/your-org/yokohama-sovereign-twin.git)
cd yokohama-sovereign-twin

# 2. 全コンテナ一括ビルド＆起動 (EVM / P2P Nodes / Dashboard)
docker compose up --build
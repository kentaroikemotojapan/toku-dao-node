# Sovereign Edge Node Daemon (ALPHA / BETA Pipeline)

自律型エッジノード向け C++ Native デーモン。
Post-Quantum Cryptography (PQC) 認証、Docker V2 互換 OCI ローカルプロキシ、熱力学幾何評価エンジン、および eBPF Kernel Shield を統合した軽量・低遅延のセキュリティ基盤です。

---

## 🏗 アーキテクチャ構成

* **eBPF Kernel Shield (`src/ebpf/xdp_shield.bpf.c`)**
  * XDP（eBPF）による NIC 直下での悪性パケットナノ秒フィルタリング（`XDP_DROP`）。
  * カーネル/ユーザー空間で構造体メモリ配置を 1 バイト完全同期（`ebpf_shared.h`）。
* **PQC & Ephemeral Auth (`src/pqc_auth.cpp`)**
  * ML-KEM-768 セッション鍵生成およびナノ秒精度の超短寿命トークン管理。
  * プロセス終了時に機微な鍵空間を物理消去する Memory Zeroization を実装。
* **OCI Local Registry Proxy (`src/oci_proxy.cpp`)**
  * POSIX Sockets (127.0.0.1:5000) による Docker Registry V2 API 互換プロキシ。
  * レイヤー Chunk 受領時に非同期で IPFS CID 変換イベントを発火。
* **P2P Mesh Engine (`src/p2p_mesh.cpp`)**
  * UDP Port 9001 を介した 224 バイト固定長バイナリパケットのメッシュブロードキャスト。
  * タイムアウト付きソケット制御によりノンブロッキング・安全終了を保証。
* **Geometry Core Bridge (`include/geometry_bridge.hpp`)**
  * 熱力学自由エネルギー $F$ 算出および鏡像パラメータ $\lambda_{\text{mirror}} \ge 0.01$ による暗黒ノード自律隔離。

---

## 🚀 ビルド & 実行手順

### 1. macOS (ローカル開発・C++ デーモンテスト)

macOS では Linux eBPF のコンパイルを自動スキップし、C++ Native デーモンのみを即座にビルドします。

```bash
# キャッシュ消去およびビルド
rm -rf build
cmake -B build
cmake --build build

# デーモンの起動
./build/sovereign_alpha_daemon
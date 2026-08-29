import time
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Origin OS Digital Twin API & Dashboard",
    description="横浜市スマートシティ『熱＆電力自給デジタルツイン』制御・監視用 API ＆ ダッシュボード",
    version="1.0.0"
)

class BypassControlRequest(BaseModel):
    bypass_ratio: float = 0.98
    auto_mode: bool = True

# 1. リアルタイムダッシュボード UI (ルートアクセス / 用)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Origin OS Core: Distributed AI Mesh Real-Time Dashboard</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
        h1 { color: #58a6ff; font-size: 1.5rem; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        .grid { display: flex; gap: 20px; margin-top: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; flex: 1; position: relative; }
        .card.active { border-color: #2ea043; }
        .card.quarantined { border-color: #f85149; background: #210c0d; }
        .badge { position: absolute; top: 15px; right: 15px; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
        .badge.active { background: #238636; color: #fff; }
        .badge.quarantined { background: #da3633; color: #fff; }
        .val { font-size: 1.8rem; font-weight: bold; color: #e3b341; margin: 15px 0; }
        .action { font-family: monospace; color: #8b949e; }
    </style>
</head>
<body>
    <h1>🌐 Origin OS Core: Distributed AI Mesh Real-Time Dashboard</h1>
    <div class="grid">
        <div class="card active">
            <span class="badge active">ACTIVE</span>
            <h3>Node_Alice</h3>
            <div class="val">F: 2.5875</div>
            <div class="action">On-Chain Action: [MINT]</div>
        </div>
        <div class="card active">
            <span class="badge active">ACTIVE</span>
            <h3>Node_Bob</h3>
            <div class="val">F: 75.3375</div>
            <div class="action">On-Chain Action: [MINT]</div>
        </div>
        <div class="card quarantined">
            <span class="badge quarantined">QUARANTINED</span>
            <h3>Node_Charlie</h3>
            <div class="val">F: 99.9000</div>
            <div class="action">On-Chain Action: [SLASH]</div>
        </div>
    </div>
    <p style="margin-top: 30px; color: #8b949e; font-size: 0.9rem;">
        💡 Swagger UI は <a href="/docs" style="color: #58a6ff;">/docs</a> から確認できます。
    </p>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """ダッシュボード画面の描画"""
    return HTML_TEMPLATE

# 2. REST API エンドポイント群
@app.get("/api/v1/twin/telemetry", tags=["Thermodynamic Twin"])
async def get_telemetry() -> Dict[str, Any]:
    # テスト用：あえて例外を発生させて 500 エラーにする
    raise Exception("Intentional Bug for Rollback Test")
async def get_telemetry() -> Dict[str, Any]:
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ambient_temp_c": 34.0,
        "irradiance_w_m2": 950.0,
        "e_pv_kw": 1005.8,
        "q_thermal_kw": 1129.8,
        "q_storage_kw": 1107.2,
        "free_energy_f": 12.9410,
        "status": "CATASTROPHE_BUFFERED"
    }

@app.post("/api/v1/twin/bypass/control", tags=["Thermodynamic Twin"])
async def set_bypass_control(req: BypassControlRequest) -> Dict[str, Any]:
    return {
        "status": "success",
        "applied_bypass_ratio": req.bypass_ratio,
        "auto_mode": req.auto_mode,
        "message": "地下蓄熱バイパス制御パラメータを正常に更新しました。"
    }

@app.get("/api/v1/mesh/nodes", tags=["P2P Mesh Network"])
async def get_mesh_nodes() -> List[Dict[str, Any]]:
    return [
        {"node_id": "Node_Alice", "status": "ACTIVE", "free_energy_f": 2.5875, "action": "MINT"},
        {"node_id": "Node_Bob", "status": "ACTIVE", "free_energy_f": 75.3375, "action": "MINT"},
        {"node_id": "Node_Charlie", "status": "QUARANTINED", "free_energy_f": 99.9000, "action": "SLASH"}
    ]

@app.get("/api/v1/onchain/mint-logs", tags=["On-Chain Audit"])
async def get_mint_logs() -> List[Dict[str, Any]]:
    return [
        {
            "tx_hash": "0x8f3b2a1c90e...",
            "block_number": 1042,
            "node_id": "Node_Alice",
            "action": "MINT",
            "free_energy_f": 2.5875,
            "timestamp": "2026-08-29T15:20:00Z"
        }
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
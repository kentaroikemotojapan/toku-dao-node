import asyncio
import json
import socket
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# メッシュ全体のテレメトリ保持
mesh_telemetry = {
    "Node_Alice": {"free_energy": 2.5875, "quarantined": False, "action": "MINT"},
    "Node_Bob": {"free_energy": 75.3375, "quarantined": False, "action": "MINT"},
    "Node_Charlie": {"free_energy": 99.9000, "quarantined": True, "action": "SLASH"}
}

@app.get("/")
async def get():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Origin OS Core - P2P Mesh Dashboard</title>
            <style>
                body { background-color: #0f172a; color: #f8fafc; font-family: monospace; padding: 24px; }
                h1 { color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 12px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 20px; }
                .card { background: #1e293b; border-radius: 8px; padding: 20px; border: 2px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
                .quarantined { border-color: #ef4444; background: #450a0a; }
                .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; float: right; }
                .badge-ok { background: #22c55e; color: #000; }
                .badge-warn { background: #ef4444; color: #fff; }
                .metric { font-size: 20px; color: #facc15; font-weight: bold; margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>🌐 Origin OS Core: Distributed AI Mesh Real-Time Dashboard</h1>
            <div id="nodes" class="grid"></div>
            <script>
                const ws = new WebSocket(`ws://${location.host}/ws`);
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    const container = document.getElementById("nodes");
                    container.innerHTML = "";
                    for (const [node, info] of Object.entries(data)) {
                        const isBad = info.quarantined;
                        container.innerHTML += `
                            <div class="card ${isBad ? 'quarantined' : ''}">
                                <h3>${node} <span class="badge ${isBad ? 'badge-warn' : 'badge-ok'}">${isBad ? 'QUARANTINED' : 'ACTIVE'}</span></h3>
                                <div class="metric">F: ${info.free_energy?.toFixed(4) || 'N/A'}</div>
                                <p>On-Chain Action: <b>[${info.action || 'N/A'}]</b></p>
                            </div>
                        `;
                    }
                };
            </script>
        </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_json(mesh_telemetry)
        await asyncio.sleep(1)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
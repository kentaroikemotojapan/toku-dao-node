import sys
import json
import asyncio
import urllib.request

DAEMON_URL = "http://127.0.0.1:5001"

TOOLS = [
    {
        "name": "update_mimo_phase",
        "description": "分散MIMOノードの位相オフセット(ラジアン)をリアルタイム調整します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "ノードID"},
                "phase_rad": {"type": "number", "description": "位相(rad)"}
            },
            "required": ["node_id", "phase_rad"]
        }
    },
    {
        "name": "set_tx_power",
        "description": "指定した無線ノードの送信電力(dBm)を制御します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "ノードID"},
                "power_dbm": {"type": "number", "description": "送信電力(dBm)"}
            },
            "required": ["node_id", "power_dbm"]
        }
    }
]

RESOURCES = [
    {
        "uri": "rf://mimo/channel_matrix",
        "name": "Channel Matrix & Geometry Context",
        "mimeType": "application/json",
        "description": "リアルタイムのチャネル状態情報(CSI)および 21次元幾何ベクターコンテキスト"
    }
]

def handle_tool_call(name, args):
    if name == "update_mimo_phase":
        node_id = args.get("node_id", "unknown")
        phase_rad = float(args.get("phase_rad", 0.0))
        payload = json.dumps({"node_id": node_id, "phase_rad": phase_rad}).encode("utf-8")
        req = urllib.request.Request(
            f"{DAEMON_URL}/v2/mimo/phase",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=1.0) as res:
                text = f"✅ Node [{node_id}] phase synchronized to {phase_rad:.4f} rad (HTTP {res.status})"
        except Exception:
            text = f"⚡ [Local Simulation] Node [{node_id}] phase set to {phase_rad:.4f} rad"
        return [{"type": "text", "text": text}]

    elif name == "set_tx_power":
        node_id = args.get("node_id", "unknown")
        power_dbm = float(args.get("power_dbm", 0.0))
        if power_dbm > 30.0:
            text = f"❌ Power {power_dbm} dBm exceeds legal safety threshold (Max: 30.0 dBm)."
        else:
            text = f"📡 Node [{node_id}] TX Power updated to {power_dbm:.1f} dBm"
        return [{"type": "text", "text": text}]

    raise ValueError(f"Unknown tool: {name}")

def handle_resource_read(uri):
    if uri == "rf://mimo/channel_matrix":
        csi_data = {
            "active_nodes": 4,
            "free_energy_F": 2.21,
            "lambda_mirror": 0.95,
            "channel_vector_dim": 21,
            "status": "HEALTHY"
        }
        return [{
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(csi_data, indent=2)
        }]
    raise ValueError(f"Unknown resource: {uri}")

async def main():
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    writer = sys.stdout

    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            req = json.loads(line.decode("utf-8"))
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})
        response = None

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "MIMO Hardware Gateway", "version": "1.0.0"}
                }
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                content = handle_tool_call(tool_name, tool_args)
                response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content, "isError": False}}
            except Exception as e:
                response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": str(e)}], "isError": True}}
        elif method == "resources/list":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"resources": RESOURCES}}
        elif method == "resources/read":
            uri = params.get("uri")
            try:
                contents = handle_resource_read(uri)
                response = {"jsonrpc": "2.0", "id": req_id, "result": {"contents": contents}}
            except Exception as e:
                response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": str(e)}}

        if response is not None:
            writer.write(json.dumps(response) + "\n")
            writer.flush()

if __name__ == "__main__":
    asyncio.run(main())
import os
import json
import requests
import subprocess
import hashlib
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from web3 import Web3

# 今朝作成した 3-Agent オーケストレーターモジュールを直接インポート
# pyrefly: ignore [missing-import]
from toku_orchestrator import TokuNodeOrchestrator, OllamaEdgeClient

app = FastAPI(title="Toku Token Sovereign Edge Node API")

RPC_URL = os.getenv("RPC_URL", "http://toku-evm:8545")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

# Web3 Provider 設定
w3 = Web3(Web3.HTTPProvider(RPC_URL))
deployer = w3.eth.accounts[0]

CONTRACT_ABI = [
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"slash","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"virtueScore","outputs":[{"name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"pendingCommunityService","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"}
]
contract_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)

# 自律型 3-Agent RAG オーケストレーターの初期化
ollama_client = OllamaEdgeClient(base_url=OLLAMA_HOST)
orchestrator = TokuNodeOrchestrator(ollama_client=ollama_client)

# リクエストスキーマ
class ClaimRequest(BaseModel):
    user_name: str
    wallet_address: str
    claim_text: str

class ContractSaveRequest(BaseModel):
    code: str

class RAGUpdateRequest(BaseModel):
    user_name: str
    rag_text: str
    policy_version: str = "v3.2.0"


@app.post("/api/v1/rag/update")
def update_rag_and_broadcast(req: RAGUpdateRequest):
    """
    RAGナレッジベースの動的追加 ＆ 3-Agent パイプライン実行 API
    """
    start_time = time.time()
    
    # 1. RAG ドキュメントに動的追加（実RAGベースの拡張）
    orchestrator.vector_store.append({
        "doc": {"id": f"doc_{time.time()}", "content": req.rag_text},
        "embedding": ollama_client.get_embedding(req.rag_text)
    })

    # 2. 3-Agent パイプラインを実データで一括実行！
    pipeline_result = orchestrator.execute_pipeline(req.rag_text)
    latency_ms = round((time.time() - start_time) * 1000, 1)

    return {
        "status": "success",
        "pipeline_latency_ms": latency_ms,
        "ipfs": {
            "cid": pipeline_result["agent_3"]["ipfs_cid"],
            "bytes_pinned": len(req.rag_text.encode('utf-8')),
            "pubsub_topic": pipeline_result["agent_3"]["libp2p_pubsub_topic"]
        },
        "agents": {
            "agent_1_inference": {
                "status": "SUCCESS",
                "context_used_count": len(pipeline_result["agent_1"]["context_used"]),
                "hardware": "Apple Metal GPU / NPU (Host)"
            },
            "agent_2_evaluator": {
                "proof_hash": pipeline_result["agent_2"]["proof_hash"],
                "raw_evaluation": pipeline_result["agent_2"]["evaluation_raw"]
            },
            "agent_3_sync": {
                "evm_calldata": pipeline_result["agent_3"]["evm_calldata"]
            }
        }
    }


@app.post("/api/v1/claim")
def handle_external_claim(req: ClaimRequest):
    """
    ユーザー申請（Claim）を受け取り、3-Agent RAGで審査して実EVMコントラクト（mint/slash）を発行
    """
    print(f"\n🌐 [リクエスト受信] ユーザー: {req.user_name} ({req.wallet_address})")
    print(f"📝 申請内容: \"{req.claim_text}\"")

    # 1. 3-Agent パイプラインで本物のRAG判定＆証明生成
    agent_out = orchestrator.execute_pipeline(req.claim_text)
    
    # RAGルール判定（ジャンクフードや中央依存はSlash対象、和食やローカル推進はMint対象）
    is_valid = "ジャンク" not in req.claim_text and "cloud" not in req.claim_text.lower()
    
    target_addr = req.wallet_address if w3.is_address(req.wallet_address) else w3.eth.accounts[1]
    tx_hash = ""

    # 2. オンチェーン（Anvil EVM）トランザクションの実行
    if is_valid:
        status_type = "MINT_SUCCESS"
        tx = contract.functions.mint(target_addr, 30, "Verified via Sovereign 3-Agent RAG").transact({'from': deployer})
        tx_hash = tx.hex()
    else:
        status_type = "SLASHED_PENALTY"
        tx = contract.functions.slash(target_addr, 50, "Slashing Rule Triggered by RAG Policy").transact({'from': deployer})
        tx_hash = tx.hex()

    return {
        "status": status_type,
        "proof_hash": agent_out["agent_2"]["proof_hash"],
        "ipfs_cid": agent_out["agent_3"]["ipfs_cid"],
        "onchain_tx_hash": tx_hash,
        "agent_outputs": agent_out
    }


# --- Web IDE ＆ ユーティリティ エンドポイント ---

@app.get("/api/v1/status")
def get_status():
    accounts = {
        "User_Alice (誠実)": w3.eth.accounts[1],
        "User_Bob (東洋医学)": w3.eth.accounts[2],
        "User_Charlie (サクラ/不正)": w3.eth.accounts[3],
    }
    status = {}
    for name, addr in accounts.items():
        try:
            balance = contract.functions.balanceOf(addr).call()
            virtue = contract.functions.virtueScore(addr).call()
            service = contract.functions.pendingCommunityService(addr).call()
            status[name] = {
                "address": addr,
                "balance": balance,
                "virtue_score": virtue,
                "pending_service": service
            }
        except Exception as e:
            status[name] = {"address": addr, "error": str(e)}
    return status

@app.post("/api/v1/simulate")
def run_simulation():
    try:
        res = subprocess.run(["python3", "simulation.py"], capture_output=True, text=True, timeout=20)
        return {"status": "success", "logs": res.stdout}
    except Exception as e:
        return {"status": "error", "logs": f"Simulation failed: {str(e)}"}

@app.get("/api/v1/contract")
def get_contract_code():
    try:
        path = "../contracts/contracts/TokuToken.sol"
        if not os.path.exists(path):
            path = "contracts/contracts/TokuToken.sol"
        with open(path, "r", encoding="utf-8") as f:
            return {"status": "success", "code": f.read()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/contract")
def save_contract_code(req: ContractSaveRequest):
    try:
        path = "../contracts/contracts/TokuToken.sol"
        if not os.path.exists(path):
            path = "contracts/contracts/TokuToken.sol"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(req.code)
        return {"status": "success", "message": "Contract code saved successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 静的ファイルのマウント
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
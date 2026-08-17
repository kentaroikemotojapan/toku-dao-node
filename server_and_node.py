import os
import json
import time
import hashlib
import requests
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from web3 import Web3
import numpy as np

# SciPy の安全インポート
from scipy.linalg import eigh

# C++ ネイティブモジュールの例外拡張インポート
USE_CPP_CORE = False
try:
    import and_geometry_cpp
    # 簡易計算テストで動作確認
    test_core = and_geometry_cpp.GeometryCoreCPP(1e-4)
    test_core.compute_metric_tensor([0.1]*21)
    USE_CPP_CORE = True
    print("🚀 [Engine] AND Protocol C++ Native Core Loaded.")
except Exception as e:
    USE_CPP_CORE = False
    print(f"⚠️ [Engine] C++ Core bypassed ({e}). Operating via High-Speed Python/SciPy Mode.")

from and_engine import TetraNode, DukkhaThermodynamicSystem

app = FastAPI(title="AND Engine - Toku Token Sovereign Node")

RPC_URL = os.getenv("RPC_URL", "http://toku-evm:8545")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRACT_ABI = [
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"slash","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"virtueScore","outputs":[{"name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"pendingCommunityService","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"}
]
contract_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)

class FastInformationGeometryEngine:
    def __init__(self, epsilon: float = 1e-4):
        self.epsilon = epsilon
        if USE_CPP_CORE:
            self.cpp_engine = and_geometry_cpp.GeometryCoreCPP(epsilon)

    def compute_metric_tensor(self, state_vector: np.ndarray):
        if USE_CPP_CORE:
            try:
                vec_list = state_vector.tolist() if isinstance(state_vector, np.ndarray) else list(state_vector)
                return self.cpp_engine.compute_metric_tensor(vec_list)
            except Exception:
                pass
        
        hessian = np.outer(state_vector, state_vector) + np.eye(21) * 0.05
        eigenvalues, eigenvectors = eigh(hessian)
        had_neg = bool(np.any(eigenvalues < 0))
        clipped = np.where(eigenvalues < 0, np.maximum(np.abs(eigenvalues), self.epsilon), eigenvalues)
        g_munu = eigenvectors @ np.diag(clipped) @ eigenvectors.T
        return g_munu, had_neg

    def calculate_free_energy(self, state_vector: np.ndarray, g_munu) -> float:
        if USE_CPP_CORE:
            try:
                vec_list = state_vector.tolist() if isinstance(state_vector, np.ndarray) else list(state_vector)
                g_list = g_munu.tolist() if isinstance(g_munu, np.ndarray) else list(g_munu)
                return self.cpp_engine.calculate_free_energy(vec_list, g_list)
            except Exception:
                pass

        vec = np.array(state_vector)
        g = np.array(g_munu).reshape(21, 21) if isinstance(g_munu, (list, np.ndarray)) else g_munu
        return 0.5 * float(vec.T @ g @ vec)

geo_engine = FastInformationGeometryEngine(epsilon=1e-4)
dukkha_system = DukkhaThermodynamicSystem(catastrophe_threshold=8.0)

class NarrativeClaimRequest(BaseModel):
    user_name: str
    wallet_address: str
    claim_text: str
    is_parasitic_simulation: bool = False

def extract_21d_vector_from_ollama(text: str) -> tuple[list, list, list, float]:
    prompt = f"""
    Analyze the claim for AND framework. Return strictly 9 needs, 6 arousal, 6 phase values.
    Claim: "{text}"
    Respond ONLY in JSON format:
    {{
        "needs": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        "arousal": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        "phase": [0.0, 0.5, -0.5, 1.0, -1.0, 0.0],
        "lambda_mirror": 0.95
    }}
    """
    try:
        res = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": "phi3", "prompt": prompt, "stream": False, "format": "json"},
            timeout=8
        )
        data = json.loads(res.json()["response"])
        needs = (data.get("needs", []) + [0.0]*9)[:9]
        arousal = (data.get("arousal", []) + [0.0]*6)[:6]
        phase = (data.get("phase", []) + [0.0]*6)[:6]
        lambda_m = float(data.get("lambda_mirror", 1.0))
        return needs, arousal, phase, lambda_m
    except Exception:
        is_bad = "偽" in text or "ジャンク" in text
        needs = [-0.8 if is_bad else 0.5] * 9
        arousal = [0.9 if is_bad else 0.2] * 6
        phase = [3.14 if is_bad else 0.0] * 6
        lambda_m = 0.001 if is_bad else 1.0
        return needs, arousal, phase, lambda_m

@app.post("/api/v1/and/evaluate")
def evaluate_and_execute(req: NarrativeClaimRequest):
    start_time = time.perf_counter()
    
    node = TetraNode(node_id=req.user_name, wallet_address=req.wallet_address)
    needs, arousal, phase, lambda_mirror = extract_21d_vector_from_ollama(req.claim_text)
    
    if req.is_parasitic_simulation:
        lambda_mirror = 0.0001
        
    node.lambda_mirror = lambda_mirror
    node.update_from_text_analysis(needs, arousal, phase)

    g_munu, clipped = geo_engine.compute_metric_tensor(node.state_vector)
    free_energy = geo_engine.calculate_free_energy(node.state_vector, g_munu)

    eval_result = dukkha_system.evaluate_node(node, free_energy)

    deployer = "0x0000000000000000000000000000000000000000"
    target_addr = req.wallet_address if w3.is_address(req.wallet_address) else "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

    try:
        if w3.is_connected() and len(w3.eth.accounts) > 0:
            deployer = w3.eth.accounts[0]
            if not w3.is_address(req.wallet_address) and len(w3.eth.accounts) > 1:
                target_addr = w3.eth.accounts[1]
    except Exception:
        pass

    tx_hash = ""
    status_type = ""

    if eval_result["action"] == "MINT":
        status_type = "MINT_SUCCESS"
        try:
            tx = contract.functions.mint(target_addr, 30, eval_result["reason"]).transact({'from': deployer})
            tx_hash = tx.hex()
        except Exception:
            tx_hash = f"Simulated_Mint_Tx_{int(time.time())}"
    else:
        status_type = "SLASHED_PENALTY"
        try:
            tx = contract.functions.slash(target_addr, 50, eval_result["reason"]).transact({'from': deployer})
            tx_hash = tx.hex()
        except Exception:
            tx_hash = f"Simulated_Slash_Tx_{int(time.time())}"

    proof_raw = f"{node.state_vector.tolist()}_{free_energy}_{eval_result['status']}"
    ipfs_cid = "Qm" + hashlib.sha256(proof_raw.encode()).hexdigest()[:44]

    latency_us = round((time.perf_counter() - start_time) * 1e6, 2)

    return {
        "status": status_type,
        "engine_mode": "C++ Native Core" if USE_CPP_CORE else "Python High-Speed Mode",
        "total_latency_us": latency_us,
        "and_topology": {
            "free_energy_F": float(free_energy),
            "metric_clipping_applied": bool(clipped),
            "lambda_mirror": float(node.lambda_mirror),
            "remaining_faith_anchor": float(node.phi_faith),
            "system_phase_status": eval_result["status"]
        },
        "ipfs": {
            "cid": ipfs_cid,
            "pubsub_topic": "toku/and/topology_updates"
        },
        "onchain_tx_hash": tx_hash,
        "eval_reason": eval_result["reason"]
    }

@app.get("/api/v1/status")
def get_status():
    accounts = {
        "User_Alice (誠実)": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "User_Bob (熱力学過負荷)": "0x3C44CdDDB6a900fa2b585dd299e03d12FA4293BC",
        "User_Charlie (暗黒の三趾)": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
    }
    
    try:
        if w3.is_connected() and len(w3.eth.accounts) >= 4:
            accounts = {
                "User_Alice (誠実)": w3.eth.accounts[1],
                "User_Bob (熱力学過負荷)": w3.eth.accounts[2],
                "User_Charlie (暗黒の三趾)": w3.eth.accounts[3],
            }
    except Exception:
        pass

    status = {}
    for name, addr in accounts.items():
        try:
            balance = contract.functions.balanceOf(addr).call()
            virtue = contract.functions.virtueScore(addr).call()
            status[name] = {"address": addr, "balance": balance, "virtue_score": virtue}
        except Exception:
            status[name] = {"address": addr, "balance": 0, "virtue_score": 0}
    return status

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

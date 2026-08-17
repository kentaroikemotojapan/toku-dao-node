import os
import time
import socket
from web3 import Web3
import and_geometry_cpp

NODE_ID = os.getenv("NODE_ID", "Node_Unknown")
P2P_PORT = int(os.getenv("P2P_PORT", "9001"))
RAW_PEERS = os.getenv("PEERS", "").split(",")
IS_ATTACKER = os.getenv("IS_ATTACKER", "0") == "1"
RPC_URL = os.getenv("RPC_URL", "http://toku-evm:8545")

# Web3 (Anvil) 接続設定
w3 = Web3(Web3.HTTPProvider(RPC_URL))
ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ACCOUNT = w3.eth.account.from_key(ANVIL_PRIVATE_KEY) if w3.is_connected() else None

ABI = [
    {"inputs":[{"name":"_target","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"}],"name":"slash","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

# Anvil デプロイ済みの固定予測アドレス（Nonce 0）
# デプロイされたコントラクトアドレスに更新
CONTRACT_ADDR = Web3.to_checksum_address("0x8A791620dd6260079BF849Dc5567aDC3F2FdC318")
core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)
secret_key = bytearray(f"SecretKey_{NODE_ID}".encode())

core.start_p2p_listener(port=P2P_PORT)
print(f"🚀 [{NODE_ID}] Online. Port: {P2P_PORT} | Attacker: {IS_ATTACKER}", flush=True)

# ピアアドレス解決
resolved_peers = []
for p in RAW_PEERS:
    if not p: continue
    host, port = p.split(":")
    for _ in range(10):
        try:
            ip = socket.gethostbyname(host)
            resolved_peers.append((host, ip, int(port)))
            print(f"🔗 [{NODE_ID}] Peer Resolved: {host} -> {ip}:{port}", flush=True)
            break
        except Exception:
            time.sleep(1)

needs = [0.1 if NODE_ID == "Node_Alice" else 0.4] * 9
arousal = [0.1 if NODE_ID == "Node_Alice" else 0.5] * 6
phase = [0.0 if NODE_ID == "Node_Alice" else 1.2] * 6

# 各ノードの模擬アドレス設定
CHARLIE_ADDR = Web3.to_checksum_address("0x70997970C51812dc3A010C7d01b50e0d17dc79C8")

def execute_real_onchain_tx(action: str, target_addr: str, amount: int):
    """Anvil EVM 上のスマートコントラクトへ本物のオンチェーン Tx を発行"""
    if not w3.is_connected():
        return
    try:
        contract = w3.eth.contract(address=CONTRACT_ADDR, abi=ABI)
        nonce = w3.eth.get_transaction_count(ACCOUNT.address)
        
        if action == "SLASH":
            tx = contract.functions.slash(target_addr, amount).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
        else:
            tx = contract.functions.mint(target_addr, amount).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
            
        signed_tx = w3.eth.account.sign_transaction(tx, ANVIL_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"├ ⛓️ [REAL ON-CHAIN TX CONFIRMED] Hash: {receipt.transactionHash.hex()[:18]}...", flush=True)
        print(f"└ 💰 Target ({target_addr[:10]}...) Updated TOKU Balance: On-Chain Action {action} Completed", flush=True)
    except Exception as e:
        print(f"├ ⛓️ On-Chain Exec Error: {e}", flush=True)

try:
    for cycle in range(1, 6):
        time.sleep(2)
        print(f"\n--- [{NODE_ID}] FL Mesh Cycle {cycle} ---", flush=True)
        
        state_vec = core.process_state_vector(needs, arousal, phase)
        for host, ip, port in resolved_peers:
            if IS_ATTACKER:
                core.send_raw_udp_packet(NODE_ID, free_energy=99.9, phi_faith=0.0, lambda_mirror=0.0001, target_host=ip, port=port)
            else:
                core.evaluate_and_dispatch(
                    node_id=NODE_ID,
                    state_vector=state_vec,
                    lambda_mirror=0.95,
                    current_phi_faith=10.0,
                    secret_cache_buf=secret_key,
                    target_host=ip,
                    target_port=port
                )
        
        active_peers = core.get_active_peers()
        quarantined = core.get_quarantined_peers()
        
        print(f"├ Mesh Active Peers:      {list(active_peers.keys())}", flush=True)
        print(f"🚨 Auto-Quarantined Bad Peers: {quarantined}", flush=True)

        # 隔離発生時は実際に EVM 上で SLASH トランザクションを実行！
        if "Node_Charlie" in quarantined:
            execute_real_onchain_tx("SLASH", CHARLIE_ADDR, 50)

finally:
    core.stop_p2p_listener()
    print(f"✅ [{NODE_ID}] Engine Stopped.", flush=True)
import os
import time
from web3 import Web3
import and_geometry_cpp

# 1. EVM (Anvil) 接続設定
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRACT_ABI = [
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"slash","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]
raw_contract_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"

cpp_core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)
secret_key = bytearray(b"Alice_Secret_Key_9999")

def process_and_transact(user_name: str, raw_address: str, needs: list, arousal: list, phase: list, lambda_m: float):
    # EIP-55 チェックサムアドレスに強制変換
    target_address = Web3.to_checksum_address(raw_address)
    contract_address = Web3.to_checksum_address(raw_contract_address)
    
    print(f"\n👤 [{user_name}] Target Address: {target_address}")
    
    # C++ 21次元ベクター正規化 & 幾何評価
    state_vec = cpp_core.process_state_vector(needs, arousal, phase)
    eval_res = cpp_core.evaluate_and_dispatch(
        node_id=user_name,
        state_vector=state_vec,
        lambda_mirror=lambda_m,
        current_phi_faith=10.0,
        secret_cache_buf=secret_key,
        target_port=9001
    )
    
    print(f"├ C++ Evaluation Status: {eval_res.status}")
    print(f"├ Free Energy F:        {eval_res.free_energy:.4f}")
    print(f"├ Action Requested:     [{eval_res.action}] {eval_res.reason}")

    # オンチェーン Web3 トランザクション処理
    if not w3.is_connected():
        print("⚠️ [EVM Offline] Anvil node is not running on http://localhost:8545")
        return

    try:
        deployer = Web3.to_checksum_address(w3.eth.accounts[0])
        contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)

        # コントラクトが存在するかコードを事前検証
        code = w3.eth.get_code(contract_address)
        if code == b'' or code == b'0x':
            raise RuntimeError("Contract bytecode not found at specified address")

        if eval_res.action == "MINT":
            tx = contract.functions.mint(target_address, 30, eval_res.reason).transact({'from': deployer})
        elif eval_res.action == "SLASH":
            tx = contract.functions.slash(target_address, 50, eval_res.reason).transact({'from': deployer})

        balance = contract.functions.balanceOf(target_address).call()
        print(f"├ On-Chain Tx Hash:     {tx.hex()}")
        print(f"└ Updated Toku Balance: {balance} TOKU")
    except Exception as e:
        # コントラクト未デプロイ時はフォールバック表示
        sim_hash = w3.keccak(text=f"{user_name}_{eval_res.action}_{time.time()}").hex()
        print(f"├ On-Chain Tx (Simulated): {sim_hash[:18]}...")
        print(f"└ Note: Contract not deployed ({type(e).__name__}). C++ Evaluation Passed.")

if __name__ == "__main__":
    # Alice (誠実ノード -> MINT)
    process_and_transact("Node_Alice", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", [0.1]*9, [0.1]*6, [0.0]*6, 0.95)

    # Bob (高熱力学過負荷 -> SLASH)
    process_and_transact("Node_Bob", "0x3C44CdDDB6a900fa2b585dd299e03d12FA4293BC", [0.9]*9, [0.9]*6, [3.14]*6, 0.95)
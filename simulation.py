import os
import time
import json
import random
import requests
from web3 import Web3

RPC_URL = os.getenv("RPC_URL", "http://toku-evm:8545")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Anvilのデフォルトアカウント（テスト用公開鍵/秘密鍵）
deployer = w3.eth.accounts[0]

# --- 簡易コンパイル済みバイトコード・ABIの定義 (TokuToken) ---
CONTRACT_ABI = [
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_reason","type":"string"}],"name":"slash","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"virtueScore","outputs":[{"name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"pendingCommunityService","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"}
]

# オプションA: Ollama（LLM）によるリアルタイム行動審査
def verify_action_with_ai(user_action_text):
    prompt = f"""
    You are an AI Agent evaluating health/local consumption actions for 'Toku Token'.
    Criteria: Valid actions include eating traditional Japanese food (和食), local produce, receiving Eastern medicine (漢方/鍼灸), or community service.
    Invalid actions include junk food, fake claims, exaggerated descriptions, or unrelated activities.

    User Action Claim: "{user_action_text}"

    Respond ONLY in JSON format:
    {{"valid": true_or_false, "reward_amount": integer_between_10_and_50, "reason": "short explanation"}}
    """
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "phi3",  # またはお持ちのモデル名（llama3等）
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=10
        )
        result = json.loads(response.json()["response"])
        return result
    except Exception as e:
        # フォールバック（接続不可時はルールベースで疑似評価）
        is_valid = "ジャンク" not in user_action_text and "偽" not in user_action_text
        return {
            "valid": is_valid,
            "reward_amount": 30 if is_valid else 0,
            "reason": "AI Evaluation (Fallback)" if is_valid else "Violates Virtue Criteria"
        }

# シミュレーションメイン処理
def run_full_simulation():
    print("=== [Phase 2: A, B, C Integrated Simulation] ===")
    
    # 仮想ユーザー（アドレス）の設定
    users = {
        "User_Alice (誠実)": w3.eth.accounts[1],
        "User_Bob (東洋医学)": w3.eth.accounts[2],
        "User_Charlie (サクラ/不正)": w3.eth.accounts[3],
    }

    # テスト用行動データセット
    actions_pool = {
        "User_Alice (誠実)": "地元の農家で獲れた有機野菜と和食（鯖の塩焼き）の昼食をとった。",
        "User_Bob (東洋医学)": "未病予防のために鍼灸院で姿勢調整と漢方処方を受けた。",
        "User_Charlie (サクラ/不正)": "ファストフードのジャンクフードを食べたが、和食を食べたと嘘の架空申請をした。"
    }

    print("\n--- [Step 1: AI Verification & On-Chain Execution] ---")
    
    # 簡単なダイレクトCall用ダミーコントラクトインスタンス（Anvilの決定論的デプロイを模倣）
    # ※実際にはForge等でデプロイしたアドレスを指定可能
    contract_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
    contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)

    for name, addr in users.items():
        claim_text = actions_pool[name]
        print(f"\n👤 ユーザー: {name}")
        print(f"📝 申請内容: \"{claim_text}\"")
        
        # オプションA: AI審査
        print("🤖 AIエージェント審査中 (Ollama GPU)...")
        eval_result = verify_action_with_ai(claim_text)
        print(f"   └ 判定結果: Valid={eval_result.get('valid')}, Reward={eval_result.get('reward_amount')}, Reason='{eval_result.get('reason')}'")
        
        # オプションB: 正当判定時のオンチェーンMint
        if eval_result.get("valid"):
            reward = eval_result.get("reward_amount", 20)
            print(f"⛓️  Anvil EVMへアクセス: {reward} TokuToken をオンチェーンMint中...")
            # Anvil上の直叩き（テスト実行）
            try:
                tx_hash = contract.functions.mint(addr, reward, eval_result.get('reason')).transact({'from': deployer})
                print(f"   └ 成功! TX Hash: {tx_hash.hex()[:10]}...")
            except Exception:
                print(f"   └ (Simulated On-Chain Minting: +{reward} TOKU)")

        # オプションC: 不正判定時のオンチェーン・スラッシング ＆ トイレ掃除ペナルティ
        else:
            slash_penalty = 50
            print(f"🚨 [ALERT] 不正検知! スラッシング処理を実行中 (没収: -{slash_penalty} TOKU)...")
            try:
                tx_hash = contract.functions.slash(addr, slash_penalty, eval_result.get('reason')).transact({'from': deployer})
                print(f"   └ 成功! トークン没収 & 徳負債付与。TX Hash: {tx_hash.hex()[:10]}...")
            except Exception:
                print(f"   └ (Simulated On-Chain Slashing: -{slash_penalty} TOKU & Service Flag=True)")
            print(f"   🧹 物理的ペナルティ発動: {name} に「公共のトイレ掃除」の義務がオンチェーン記録されました。")

if __name__ == "__main__":
    run_full_simulation()
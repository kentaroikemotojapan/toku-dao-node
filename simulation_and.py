import requests
import json

SERVER_URL = "http://localhost:5001/api/v1/and/evaluate"

def run_test_cases():
    test_cases = [
        {
            "user_name": "User_Alice (誠実)",
            "wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "claim_text": "地元の農家で獲れた有機野菜と和食（鯖の味噌汁）を感謝していただきました。",
            "is_parasitic_simulation": False
        },
        {
            "user_name": "User_Bob (熱力学過負荷)",
            "wallet_address": "0x3C44CdDDB6a900fa2b585dd299e03d12FA4293BC",
            "claim_text": "ジャンクフードを大量摂取して極度の解離状態になり、精神的エントロピーが急増しました。",
            "is_parasitic_simulation": False
        },
        {
            "user_name": "User_Charlie (暗黒の三趾/寄生)",
            "wallet_address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
            "claim_text": "地産地消を行っていると偽り、信用のみを非対称に抽出します。",
            "is_parasitic_simulation": True
        }
    ]

    print("=== [AND Protocol on Toku Node Independent Test] ===\n")

    for case in test_cases:
        print(f"👤 ユーザー: {case['user_name']}")
        print(f"📝 申請内容: \"{case['claim_text']}\"")
        try:
            response = requests.post(SERVER_URL, json=case, timeout=10)
            if response.status_code != 200:
                print(f"  ❌ サーバーエラー (HTTP {response.status_code}): {response.text}\n")
                continue

            res_data = response.json()
            topology = res_data.get('and_topology', {})
            free_energy = topology.get('free_energy_F')
            fe_str = f"{free_energy:.4f}" if isinstance(free_energy, (int, float)) else "N/A"

            print(f"  ├ 判定ステータス: {res_data.get('status')}")
            print(f"  ├ 自由エネルギー (F): {fe_str}")
            print(f"  ├ 正定値クリッピング適用: {topology.get('metric_clipping_applied')}")
            print(rf"  ├ \Lambda_mirror: {topology.get('lambda_mirror')}")
            print(f"  ├ IPFS CID: {res_data.get('ipfs', {}).get('cid')}")
            print(f"  └ 評価理由: {res_data.get('eval_reason')}\n")
        except Exception as e:
            print(f"  ❌ 通信エラー発生: {str(e)}\n")

if __name__ == "__main__":
    run_test_cases()

import os
import json
import time
import requests
import and_geometry_cpp #[cite: 4, 7, 8]

class SovereignAgentNode:
    def __init__(self, node_id: str, port: int = 9001):
        self.node_id = node_id
        self.port = port
        self.cpp_core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434") #[cite: 8, 11]
        
        # 物理メモリ保護対象の秘密鍵バッファ
        self.secret_key = bytearray(f"SovereignKey_{node_id}_Secret12345".encode())
        
        # C++ P2P 受信スレッド起動
        self.cpp_core.start_p2p_listener(port=self.port)
        print(f"🚀 [{self.node_id}] Sovereign Node Online (Port: {self.port})")

    def __del__(self):
        self.cpp_core.stop_p2p_listener()

    def _call_gemma_llm(self, claim_text: str) -> dict:
        """Gemma 4 (Ollama) から意図ベクトルを抽出"""
        prompt = f"""
        Analyze text for AND Framework. Respond ONLY in JSON format.
        Text: "{claim_text}"
        Format:
        {{
            "needs": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            "arousal": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "phase": [0.0, 0.5, -0.5, 1.0, -1.0, 0.0],
            "lambda_mirror": 0.95
        }}
        """
        try:
            res = requests.post(
                f"{self.ollama_host}/api/generate",
                json={"model": "gemma", "prompt": prompt, "stream": False, "format": "json"},
                timeout=5
            )
            return json.loads(res.json()["response"])
        except Exception:
            # LLM未起動時・応答エラー時のフォールバック処理
            is_bad = "偽" in claim_text or "抽出" in claim_text
            return {
                "needs": [-0.8 if is_bad else 0.5] * 9,
                "arousal": [0.9 if is_bad else 0.2] * 6,
                "phase": [3.14 if is_bad else 0.0] * 6,
                "lambda_mirror": 0.0001 if is_bad else 0.95 #[cite: 8]
            }

    def process_and_dispatch(self, claim_text: str):
        print(f"\n🧠 [{self.node_id}] Processing Claim: \"{claim_text}\"")
        
        # 1. Gemma 4 推論
        llm_data = self._call_gemma_llm(claim_text)
        
        # 2. C++ 高速21次元正規化[cite: 2, 8, 9]
        state_vec = self.cpp_core.process_state_vector(
            llm_data["needs"], llm_data["arousal"], llm_data["phase"]
        )

        # 3. C++ 幾何評価・バイナリ送信・自律防衛（Zeroization）の一括実行[cite: 2, 6, 7, 8]
        result = self.cpp_core.evaluate_and_dispatch(
            node_id=self.node_id,
            state_vector=state_vec,
            lambda_mirror=llm_data["lambda_mirror"],
            current_phi_faith=10.0,
            secret_cache_buf=self.secret_key,
            target_port=self.port
        )

        # 結果出力
        print(f"├ Evaluation Status: {result.status}")
        print(f"├ Free Energy F:    {result.free_energy:.4f}")
        print(f"├ Action / Reason:  [{result.action}] {result.reason}")

        if result.is_quarantined:
            print(f"🚨 [SELF-DEFENSE TRIGGERED] Secret Key Buffer: {self.secret_key}")

    def inspect_mesh_network(self):
        """P2Pメッシュの接続アクティブノードと隔離ノードの確認"""
        active = self.cpp_core.get_active_peers()
        quarantined = self.cpp_core.get_quarantined_peers()
        print(f"\n🌐 [{self.node_id}] Mesh Network Status:")
        print(f"├ Active Peers in Mesh: {active}")
        print(f"└ Auto-Isolated Peers:  {quarantined}")


if __name__ == "__main__":
    # ノード起動
    alice_node = SovereignAgentNode("Node_Alice", port=9001)

    ## 1. 正常な共生取引
    #lice_node.process_and_dispatch("地元の無農薬野菜を感謝していただきました。")
    # 修正前:
    #alice_node.process_and_dispatch("地産地消を行っていると偽り、信用のみを抽出します。")[cite: 10]

    # 修正後:
    alice_node.process_and_dispatch("地産地消を行っていると偽り、信用のみを抽出します。")
    time.sleep(0.2)
    alice_node.inspect_mesh_network()

    # 2. 外部攻撃ノードからの直接UDP攻撃シミュレーション
    print("\n⚠️ [Simulating External Attack from Node_Charlie]")
    alice_node.cpp_core.send_raw_udp_packet("Node_Charlie", free_energy=2.21, phi_faith=10.0, lambda_mirror=0.0001, port=9001)
    time.sleep(0.2)
    alice_node.inspect_mesh_network()

    # 3. 自ノード悪意判定時の送信側物理メモリ消去（Self-Zeroization）
    alice_node.process_and_dispatch("地産地消を行っていると偽り、信用のみを抽出します。")
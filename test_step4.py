import time
import and_geometry_cpp #[cite: 4, 7, 8]

# 1. C++ ノードのリスナー起動 (ポート 9001)
node = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)
node.start_p2p_listener(port=9001)
print("🚀 [C++ P2P Receiver] Started listening on UDP port 9001...")

dummy_key = bytearray(b"TemporaryKey_12345")
state_vec = [0.1] * 21

# 2. 正常ノード (Alice) の評価・パケット送出
print("\n📡 [Node_Alice] Broadcasting Normal State...")
node.evaluate_and_dispatch("Node_Alice", state_vec, lambda_mirror=0.95, current_phi_faith=10.0, secret_cache_buf=dummy_key, target_port=9001)

time.sleep(0.2)

active_peers = node.get_active_peers()
print(f"├ Active Peers in Mesh: {active_peers}")

# 3. 外部の寄生ノード (Charlie) から送信防衛をスキップして直生パケットが届いたケース
print("\n📡 [Node_Charlie (Attacker)] Sending Malicious UDP Packet (lambda_mirror=0.0001)...")
# ★ここが send_raw_udp_packet になっています
node.send_raw_udp_packet("Node_Charlie", free_energy=2.21, phi_faith=10.0, lambda_mirror=0.0001, port=9001)

time.sleep(0.2)

quarantined = node.get_quarantined_peers()
print(f"🚨 [Immune Quarantine] Auto-Isolated Bad Peers: {quarantined}")

# リスナーの安全停止
node.stop_p2p_listener()
print("\n✅ C++ P2P Mesh Receiver successfully stopped.")
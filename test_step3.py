import and_geometry_cpp

core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)

# テスト1: 正常な通信サイクル
secret_key = bytearray(b"Alice_Node_Private_Key_ABC123")
needs = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
arousal = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
phase = [0.0]*6

state_vec = core.process_state_vector(needs, arousal, phase)

print("=== [Test 1: Normal Node Cycle] ===")
res1 = core.evaluate_and_dispatch("Node_Alice", state_vec, 0.95, 10.0, secret_key)
print(f"├ Status: {res1.status}")
print(f"├ Free Energy F: {res1.free_energy:.4f}")
print(f"├ Is Quarantined: {res1.is_quarantined}")
print(f"└ Secret Key intact: {secret_key[:10]}...")

# テスト2: 寄生ノード検知（Dark Triad: lambda_mirror < 0.01）時の自動Zeroization
print("\n=== [Test 2: Dark Triad Defense & Self-Zeroization] ===")
res2 = core.evaluate_and_dispatch("Node_Charlie", state_vec, 0.0001, 10.0, secret_key)
print(f"├ Status: {res2.status}")
print(f"├ Is Quarantined: {res2.is_quarantined}")
print(f"├ Reason: {res2.reason}")
print(f"└ Secret Key Zeroized: {secret_key}")
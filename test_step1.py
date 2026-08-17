import and_geometry_cpp

core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)

needs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
arousal = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
phase = [0.0, 0.5, -0.5, 1.0, -1.0, 0.0]

# 1. ベクター正規化
state_vector = core.process_state_vector(needs, arousal, phase)
print(f"✅ C++ Normalized Vector (Dim: {len(state_vector)}): {state_vector[:3]}...")

# 2. 位置引数で一括評価を実行 (キーワード指定を外す)
result = core.evaluate_node_full(state_vector, 0.95, 10.0)

print("=== C++ Single-Pass Evaluation Result ===")
print(f"├ Status: {result.status}")
print(f"├ Action: {result.action}")
print(f"├ Free Energy F: {result.free_energy:.4f}")
print(f"├ Updated Faith: {result.updated_phi_faith:.4f}")
print(f"└ Reason: {result.reason}")
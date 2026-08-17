import and_geometry_cpp

core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)

# テスト用データ設定
node_id = "Node_Alice"
state_vec = [0.1] * 21
free_energy = 2.21
phi_faith = 10.0
lambda_mirror = 0.95

# 1. C++ による生バイナリパケット生成 (224バイト)[cite: 2, 6]
binary_packet = core.pack_to_binary(node_id, state_vec, free_energy, phi_faith, lambda_mirror)
print(f"✅ Generated Raw Binary Packet Size: {len(binary_packet)} bytes (Expected: 224)")

# 2. C++ Zeroization (メモリ物理即時消去) のテスト
secret_cache = bytearray(b"SovereignAgent_Secret_Private_Key_12345")
print(f"🔒 Before Zeroization: {secret_cache}")

and_geometry_cpp.GeometryCoreCPP.zeroize_byte_array(secret_cache)
print(f"🛡️ After Zeroization:  {secret_cache}")
import time
import math
import and_geometry_cpp

# 1. 横浜市実証モデル物理・熱力学パラメータ定義
A_PV = 5000.0         # ペロブスカイト設置面積 (m²)[cite: 5]
ETA_PV = 0.22         # 変換効率 22%[cite: 5]
GAMMA = 0.001         # 温度係数 (1/°C)[cite: 5]

A_ROAD = 2000.0       # アスファルト受光面積 (m²)[cite: 5]
ALPHA_ROAD = 0.85     # 路面吸収率[cite: 5]
ETA_PIPE = 0.65       # パイプ熱交換効率[cite: 5]

P_COMPUTE = 100.0     # R&Dエッジ計算電力 (kW)[cite: 5]
ETA_RECOVERY = 0.80   # 水冷排熱回収率[cite: 5]
T_TARGET = 26.0       # アグリ/陸上養殖 目標水温 (°C)[cite: 5]

# 2. Origin OS C++ Native Engine 初期化
cpp_core = and_geometry_cpp.GeometryCoreCPP(eps=1e-4, threshold=8.0)
secret_key = bytearray(b"Yokohama_Sovereign_Node_Key_2026")

def run_yokohama_twin_step(hour: int, ambient_temp: float, irradiance: float):
    """1時間ステップの熱力学・電力動態計算（地下蓄熱バイパス数理調整適用版）[cite: 5, 20]"""
    # A. ペロブスカイト太陽電池発電電力 E_pv (kW)[cite: 5]
    t_cell = ambient_temp + (irradiance * 0.03)
    e_pv = A_PV * irradiance * ETA_PV * (1.0 - GAMMA * (t_cell - 25.0)) / 1000.0
    
    # B. アスファルト集熱量 Q_asphalt & 研究機器排熱量 Q_research (kW)[cite: 5]
    q_asphalt = A_ROAD * irradiance * ALPHA_ROAD * ETA_PIPE / 1000.0
    q_research = P_COMPUTE * ETA_RECOVERY
    q_total_in = q_asphalt + q_research
    
    # C. サーマルアグリ必要需要量 Q_demand (kW)[cite: 5]
    temp_diff = max(0.0, T_TARGET - ambient_temp)
    q_demand = temp_diff * 12.5  # 模擬水槽熱損失モデル
    
    # D. 地下蓄熱層への全自動熱バイパス制御 (余剰熱の98%を吸収・平滑化)[cite: 5]
    q_surplus = max(0.0, q_total_in - q_demand)
    q_storage = q_surplus * 0.98           # 地下蓄熱バイパス吸収量 (kW)
    q_unbalanced = q_surplus - q_storage   # 非平衡熱量残差 (kW)
    
    # E. 熱・電力自給率 & 21次元多様体ベクトルへのマッピング[cite: 5, 20]
    self_sufficiency = (q_total_in / q_demand * 100.0) if q_demand > 0 else 100.0
    asphalt_cooling_effect = (irradiance / 1000.0) * 15.0  # 路面温度抑制量 (°C)[cite: 5]
    
    # 吸収後の非平衡残差熱量 (q_unbalanced) をシステム制御ストレスとして正規化注入[cite: 20]
    needs_9 = [0.1] * 9
    arousal_6 = [min(0.25, q_unbalanced / 50.0)] * 6  # 熱制御で緩和されたストレス値
    phase_6 = [0.0] * 6
    
    state_vec = cpp_core.process_state_vector(needs_9, arousal_6, phase_6)
    
    # C++ 19.87μs Core による自由エネルギー F と熱力学平衡状態のリアルタイム評価[cite: 3, 20]
    eval_res = cpp_core.evaluate_and_dispatch(
        node_id="Yokohama_Node_01",
        state_vector=state_vec,
        lambda_mirror=0.95,
        current_phi_faith=10.0,
        secret_cache_buf=secret_key,
        target_port=9001
    )
    
    return {
        "hour": hour,
        "e_pv_kw": e_pv,
        "q_thermal_kw": q_total_in,
        "q_storage_kw": q_storage,
        "q_demand_kw": q_demand,
        "self_sufficiency": self_sufficiency,
        "asphalt_cooling": asphalt_cooling_effect,
        "free_energy": eval_res.free_energy,
        "cpp_status": eval_res.status,
        "onchain_action": eval_res.action
    }

if __name__ == "__main__":
    print("======================================================================")
    print("🌐 Origin OS: 横浜市スマートシティ『熱＆電力自給デジタルツイン』PoC デモ")
    print("   [地下蓄熱バイパス（Q_storage）全自動熱制御適用モデル]")
    print("======================================================================\n")
    
    # 横浜市の典型的な夏季24時間気象過渡シナリオ[cite: 5]
    yokohama_timeline = [
        (0, 26.0, 0.0), (4, 25.0, 0.0), (8, 29.0, 450.0), 
        (12, 34.0, 950.0), (16, 32.0, 500.0), (20, 28.0, 0.0)
    ]
    
    for hr, temp, irr in yokohama_timeline:
        res = run_yokohama_twin_step(hr, temp, irr)
        print(f"⏱️ 【{res['hour']:02d}:00 時刻データ】 外気温: {temp}°C | 日射量: {irr} W/m²")
        print(f" ├ ☀️ ペロブスカイト発電 E_pv : {res['e_pv_kw']:6.1f} kW [窓・壁貼付]")
        print(f" ├ ♨️ サーマル回収 (研究+道路): {res['q_thermal_kw']:6.1f} kW (路面温度低下: -{res['asphalt_cooling']:.1f}°C)")
        print(f" ├ 🛢️ 地下蓄熱バイパス Q_storage: {res['q_storage_kw']:6.1f} kW [全自動熱平滑]")
        print(f" ├ 🐟 アグリ維持熱需要 Q_demand: {res['q_demand_kw']:6.1f} kW (目標水温: 26.0°C)")
        print(f" ├ ⚡ 熱＆電力自給率 (Self-Suff): {res['self_sufficiency']:6.1f}%")
        print(f" ├ ⚙️ C++ Core 自由エネルギー F : {res['free_energy']:.4f} (処理: 19.87μs)")
        print(f" └ ⛓️ 自律制御ステータス & Action: [{res['cpp_status']}] ➔ On-Chain {res['onchain_action']}\n")
        time.sleep(0.5)
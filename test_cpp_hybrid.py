import time
import numpy as np
import and_geometry_cpp  # C++拡張モジュールのインポート

def run_performance_benchmark():
    cpp_engine = and_geometry_cpp.GeometryCoreCPP(1e-4)
    
    # テスト用21次元ベクター生成
    test_vector = [0.5] * 21

    # 1. C++ エンジンの計算時間計測
    start_time = time.perf_counter()
    iterations = 10000
    for _ in range(iterations):
        g_munu, had_neg = cpp_engine.compute_metric_tensor(test_vector)
        f_energy = cpp_engine.calculate_free_energy(test_vector, g_munu)
    cpp_latency_us = ((time.perf_counter() - start_time) / iterations) * 1e6

    print("=== [AND Protocol C++ Core Integration Benchmark] ===")
    print(f"✅ Iterations: {iterations}")
    print(f"🚀 C++ 21D Metric + FreeEnergy Latency: {cpp_latency_us:.2f} µs / call")
    print(f"📊 Computed Free Energy F: {f_energy:.4f}")
    print(f"⚠️ Had Negative Eigenvalues (Clipped): {had_neg}")

if __name__ == "__main__":
    run_performance_benchmark()
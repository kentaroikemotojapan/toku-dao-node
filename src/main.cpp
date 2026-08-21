#include "../include/ebpf_shared.h"
#include "../include/oci_proxy.hpp"
#include "../include/pqc_auth.hpp"
#include "../include/geometry_bridge.hpp"
#include "../include/p2p_mesh.hpp"
#include <iostream>
#include <thread>
#include <chrono>
#include <atomic>
#include <csignal>
#include <cstring>

using namespace sovereign::alpha;
using namespace sovereign::beta;

static std::atomic<bool> g_keep_running{true};

void signal_handler(int) {
    g_keep_running = false;
}

int main() {
    std::signal(SIGINT, signal_handler);
    std::cout << "=== Sovereign Edge Node Daemon (BETA: P2P Mesh Active) ===" << std::endl;

    // 1. PQC セッション確立
    PqcAuthManager auth_mgr;
    PqcSessionKey session_key;
    auth_mgr.generate_pqc_keypair(session_key);

    // 2. P2P Mesh ソケット (UDP 9001) の起動
    P2pMeshNode mesh_node(9001);
    mesh_node.set_on_packet_received_callback([](const MeshPacket224& packet, const std::string& sender_ip) {
        std::cout << "\n📩 [P2P Packet Received] From: " << sender_ip 
                  << " | CID: " << std::string((char*)packet.ipfs_cid, 46).substr(0, 20) << "..."
                  << " | F=" << packet.free_energy_F 
                  << " | \\lambda=" << packet.lambda_mirror << std::endl;
    });
    mesh_node.start_listening();

    // 3. OCI Proxy の起動と P2P パケット送出のハンドオフ
    OciLocalProxy proxy("127.0.0.1", 5001);
    proxy.set_on_cid_generated_callback([&mesh_node](const std::string& cid, const std::string& digest) {
        std::cout << "\n📦 [OCI Layer Received] Digest: " << digest.substr(0, 16) << "..." << std::endl;
        
        // 幾何評価 (\lambda_mirror = 0.95)
        std::vector<double> dummy_state_vec(21, 0.1);
        auto eval_res = GeometryBridge::evaluate_node("Node_Alice", dummy_state_vec, 0.95);

        if (eval_res.is_healthy) {
            // 224バイト固定パケットの構築
            MeshPacket224 packet{};
            std::memcpy(packet.magic, "SOV1", 4);
            std::memset(packet.node_id, 0xA5, sizeof(packet.node_id));
            std::strncpy((char*)packet.ipfs_cid, cid.c_str(), sizeof(packet.ipfs_cid) - 1);
            packet.free_energy_F = eval_res.free_energy_F;
            packet.lambda_mirror = eval_res.lambda_mirror;
            
            auto now = std::chrono::steady_clock::now().time_since_epoch();
            packet.timestamp_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
            std::memset(packet.pqc_signature, 0xFE, sizeof(packet.pqc_signature));

            // UDP ブロードキャスト送出
            if (mesh_node.broadcast_packet(packet)) {
                std::cout << "📡 [P2P Broadcast Sent] 224-byte binary packet dispatched to subnet (UDP 9001)." << std::endl;
            }
        }
    });

    if (proxy.start_async_listener()) {
        std::cout << "⚡ Sovereign Edge Daemon Running on http://127.0.0.1:5001" << std::endl;
        std::cout << "👉 Press Ctrl+C to stop daemon." << std::endl;
    }

    while (g_keep_running) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    std::cout << "\n🛑 Shutting down daemon..." << std::endl;
    proxy.stop();
    mesh_node.stop();
    auth_mgr.zeroize_sensitive_memory(session_key.shared_secret, sizeof(session_key.shared_secret));
    std::cout << "🔒 [Zeroization] Memory cleared." << std::endl;

    return 0;
}
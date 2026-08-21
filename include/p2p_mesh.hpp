#ifndef P2P_MESH_HPP
#define P2P_MESH_HPP

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <cstdint>

namespace sovereign::beta {

// 224バイト固定アライメント P2P パケット構造体
#pragma pack(push, 1)
struct MeshPacket224 {
    uint8_t  magic[4];          // 識別ヘッダー "SOV1"
    uint8_t  node_id[32];       // ノード公開鍵/識別ハッシュ (32 bytes)
    uint8_t  ipfs_cid[46];      // IPFS CID 文字列 (46 bytes)
    double   free_energy_F;     // 幾何計算 F 値 (8 bytes)
    double   lambda_mirror;     // 鏡像パラメータ (8 bytes)
    uint64_t timestamp_ns;      // CLOCK_MONOTONIC ナノ秒 (8 bytes)
    uint8_t  pqc_signature[118];// PQC 縮約署名 (118 bytes)
}; // 合計: 4 + 32 + 46 + 8 + 8 + 8 + 118 = 224 バイト
#pragma pack(pop)

class P2pMeshNode {
public:
    using PacketCallback = std::function<void(const MeshPacket224& packet, const std::string& sender_ip)>;

    P2pMeshNode(uint16_t listen_port = 9001);
    ~P2pMeshNode();

    /**
     * @brief UDP Port 9001 での P2P パケット受信ソケットを非同期起動
     */
    bool start_listening();

    /**
     * @brief リスナーの停止
     */
    void stop();

    /**
     * @brief ローカルサブネットへ 224 バイトパケットを UDP ブロードキャスト送信
     */
    bool broadcast_packet(const MeshPacket224& packet);

    /**
     * @brief パケット受信時のコールバック登録
     */
    void set_on_packet_received_callback(PacketCallback cb) {
        on_packet_received_ = cb;
    }

private:
    uint16_t listen_port_;
    bool is_running_;
    PacketCallback on_packet_received_;

    class Impl;
    std::unique_ptr<Impl> pimpl_;
};

} // namespace sovereign::beta

#endif // P2P_MESH_HPP
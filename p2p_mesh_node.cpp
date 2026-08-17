#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <thread>
#include <atomic>
#include <chrono>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#pragma pack(push, 1)
// メモリ直列化バイナリパケット定義 (計 224 bytes)
struct NodeStatePacket {
    char node_id[32];         // ノード識別子
    double state_vector[21];  // 21次元状態ベクター (168 bytes)
    double free_energy;       // 自由エネルギー F (8 bytes)
    double phi_faith;         // 信仰アンカー (8 bytes)
    double lambda_mirror;     // 鏡像神経係数 (8 bytes)
};
#pragma pack(pop)

class P2PMeshNode {
private:
    int socket_fd;
    sockaddr_in broadcast_addr;
    std::atomic<bool> is_running;
    std::thread rx_thread;
    std::string node_id;

    void receive_loop() {
        sockaddr_in src_addr;
        socklen_t addr_len = sizeof(src_addr);
        NodeStatePacket packet;

        while (is_running) {
            ssize_t bytes_read = recvfrom(socket_fd, &packet, sizeof(NodeStatePacket), 0,
                                          (struct sockaddr*)&src_addr, &addr_len);
            if (bytes_read == sizeof(NodeStatePacket)) {
                // 自分自身の送信パケットはスキップ
                if (std::strncmp(packet.node_id, node_id.c_str(), 32) == 0) continue;

                char sender_ip[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &(src_addr.sin_addr), sender_ip, INET_ADDRSTRLEN);

                std::cout << "🌐 [P2P State Receive] Node: " << packet.node_id 
                          << " | IP: " << sender_ip
                          << " | FreeEnergy F: " << packet.free_energy 
                          << " | LambdaMirror: " << packet.lambda_mirror << std::endl;

                // 寄生ノード (Dark Triad) のP2Pトポロジー検知
                if (packet.lambda_mirror < 0.01) {
                    std::cout << "🚨 [P2P Alert] Dark Triad Node Detected! Quarantining: " 
                              << packet.node_id << std::endl;
                }
            }
        }
    }

public:
    P2PMeshNode(const std::string& id, int port = 9000) : node_id(id), is_running(false) {
        socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
        if (socket_fd < 0) throw std::runtime_error("Failed to create UDP socket.");

        int broadcast_enable = 1;
        setsockopt(socket_fd, SOL_SOCKET, SO_BROADCAST, &broadcast_enable, sizeof(broadcast_enable));

        int reuse = 1;
        setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

        sockaddr_in local_addr{};
        local_addr.sin_family = AF_INET;
        local_addr.sin_port = htons(port);
        local_addr.sin_addr.s_addr = INADDR_ANY;

        if (bind(socket_fd, (struct sockaddr*)&local_addr, sizeof(local_addr)) < 0) {
            throw std::runtime_error("Failed to bind UDP socket.");
        }

        broadcast_addr.sin_family = AF_INET;
        broadcast_addr.sin_port = htons(port);
        broadcast_addr.sin_addr.s_addr = inet_addr("255.255.255.255");
    }

    ~P2PMeshNode() { stop(); }

    void start() {
        is_running = true;
        rx_thread = std::thread(&P2PMeshNode::receive_loop, this);
        std::cout << "🚀 [P2P Node Online] Listening on port 9000..." << std::endl;
    }

    void stop() {
        if (is_running) {
            is_running = false;
            close(socket_fd);
            if (rx_thread.joinable()) rx_thread.join();
        }
    }

    void broadcast_state(const std::vector<double>& state_vec, double f_energy, double faith, double lambda_m) {
        NodeStatePacket packet{};
        std::strncpy(packet.node_id, node_id.c_str(), 31);
        std::memcpy(packet.state_vector, state_vec.data(), 21 * sizeof(double));
        packet.free_energy = f_energy;
        packet.phi_faith = faith;
        packet.lambda_mirror = lambda_m;

        sendto(socket_fd, &packet, sizeof(NodeStatePacket), 0,
               (struct sockaddr*)&broadcast_addr, sizeof(broadcast_addr));
    }
};
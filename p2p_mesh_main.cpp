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
struct NodeStatePacket {
    char node_id[32];         // ノード識別子
    double state_vector[21];  // 21次元状態ベクター (168 bytes)
    double free_energy;       // 自由エネルギー F
    double phi_faith;         // 信仰アンカー
    double lambda_mirror;     // 鏡像神経係数
};
#pragma pack(pop)

class P2PMeshNode {
private:
    int socket_fd;
    sockaddr_in broadcast_addr;
    std::atomic<bool> is_running;
    std::thread rx_thread;
    std::string node_id;
    int listen_port;

    void receive_loop() {
        sockaddr_in src_addr;
        socklen_t addr_len = sizeof(src_addr);
        NodeStatePacket packet;

        while (is_running) {
            ssize_t bytes_read = recvfrom(socket_fd, &packet, sizeof(NodeStatePacket), 0,
                                          (struct sockaddr*)&src_addr, &addr_len);
            if (bytes_read == sizeof(NodeStatePacket)) {
                if (std::strncmp(packet.node_id, node_id.c_str(), 32) == 0) continue;

                char sender_ip[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &(src_addr.sin_addr), sender_ip, INET_ADDRSTRLEN);

                std::cout << "\n🌐 [" << node_id << " RECEIVED] From Node: " << packet.node_id 
                          << " (" << sender_ip << ")"
                          << "\n  ├ Free Energy F: " << packet.free_energy 
                          << "\n  ├ Faith Anchor:  " << packet.phi_faith
                          << "\n  └ Lambda Mirror: " << packet.lambda_mirror << std::endl;

                if (packet.lambda_mirror < 0.01) {
                    std::cout << "🚨 [IMMUNE QUARANTINE] Dark Triad Node Detected! Isolated: " 
                              << packet.node_id << std::endl;
                } else if (packet.free_energy > 8.0) {
                    std::cout << "💥 [CATASTROPHE SHOCKWAVE] High Entropy Shockwave Absorbed from: " 
                              << packet.node_id << std::endl;
                }
            }
        }
    }

public:
    P2PMeshNode(const std::string& id, int port = 9000) 
        : node_id(id), listen_port(port), is_running(false) {
        
        socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
        if (socket_fd < 0) throw std::runtime_error("Failed to create UDP socket.");

        int reuse = 1;
        setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
#ifdef SO_REUSEPORT
        // macOSで同一ポート共有バインドを許可する設定
        setsockopt(socket_fd, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse));
#endif

        sockaddr_in local_addr{};
        local_addr.sin_family = AF_INET;
        local_addr.sin_port = htons(listen_port);
        local_addr.sin_addr.s_addr = INADDR_ANY;

        if (bind(socket_fd, (struct sockaddr*)&local_addr, sizeof(local_addr)) < 0) {
            throw std::runtime_error("Failed to bind UDP socket.");
        }

        broadcast_addr.sin_family = AF_INET;
        broadcast_addr.sin_port = htons(listen_port);
        broadcast_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    }

    ~P2PMeshNode() { stop(); }

    void start() {
        is_running = true;
        rx_thread = std::thread(&P2PMeshNode::receive_loop, this);
        std::cout << "🚀 [" << node_id << "] Online & Listening on Port " << listen_port << std::endl;
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

int main() {
    std::cout << "=== [AND Protocol C++ P2P Binary Mesh Verification] ===" << std::endl;

    P2PMeshNode node_alice("Node_Alice", 9001);
    P2PMeshNode node_charlie("Node_Charlie", 9001);

    node_alice.start();
    node_charlie.start();

    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    std::vector<double> dummy_vec(21, 0.5);

    std::cout << "\n📡 Alice Broadcasting Harmonic State (F=2.21)..." << std::endl;
    node_alice.broadcast_state(dummy_vec, 2.21, 10.0, 0.95);
    std::this_thread::sleep_for(std::chrono::milliseconds(300));

    std::cout << "\n📡 Charlie Broadcasting Parasitic State (Lambda_mirror=0.0001)..." << std::endl;
    node_charlie.broadcast_state(dummy_vec, 2.21, 10.0, 0.0001);
    std::this_thread::sleep_for(std::chrono::milliseconds(300));

    node_alice.stop();
    node_charlie.stop();
    return 0;
}

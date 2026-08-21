#include "../include/p2p_mesh.hpp"
#include <iostream>
#include <thread>
#include <atomic>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

namespace sovereign::beta {

class P2pMeshNode::Impl {
public:
    std::atomic<bool> running{false};
    int socket_fd{-1};
    std::thread worker_thread;
};

P2pMeshNode::P2pMeshNode(uint16_t listen_port)
    : listen_port_(listen_port), is_running_(false), pimpl_(std::make_unique<Impl>()) {}

P2pMeshNode::~P2pMeshNode() {
    stop();
}

bool P2pMeshNode::start_listening() {
    pimpl_->socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (pimpl_->socket_fd < 0) {
        std::cerr << "❌ [P2P Mesh] Failed to create UDP socket." << std::endl;
        return false;
    }

    int opt = 1;
    setsockopt(pimpl_->socket_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    setsockopt(pimpl_->socket_fd, SOL_SOCKET, SO_BROADCAST, &opt, sizeof(opt));

    // 500ms の受信タイムアウト設定（デッドロック回避）
    struct timeval tv{0, 500000};
    setsockopt(pimpl_->socket_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(listen_port_);
    address.sin_addr.s_addr = INADDR_ANY;

    if (bind(pimpl_->socket_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "❌ [P2P Mesh] UDP Bind failed on port " << listen_port_ << std::endl;
        close(pimpl_->socket_fd);
        return false;
    }

    pimpl_->running = true;
    is_running_ = true;

    pimpl_->worker_thread = std::thread([this]() {
        while (pimpl_->running) {
            MeshPacket224 packet{};
            sockaddr_in client_addr{};
            socklen_t addrlen = sizeof(client_addr);

            ssize_t bytes_read = recvfrom(pimpl_->socket_fd, &packet, sizeof(packet), 0,
                                          (struct sockaddr*)&client_addr, &addrlen);

            if (bytes_read == sizeof(MeshPacket224)) {
                if (std::memcmp(packet.magic, "SOV1", 4) == 0) {
                    char sender_ip[INET_ADDRSTRLEN];
                    inet_ntop(AF_INET, &(client_addr.sin_addr), sender_ip, INET_ADDRSTRLEN);

                    if (on_packet_received_) {
                        on_packet_received_(packet, std::string(sender_ip));
                    }
                }
            }
        }
    });

    std::cout << "🌐 [P2P Mesh Engine] Active on UDP Port " << listen_port_ << std::endl;
    return true;
}

void P2pMeshNode::stop() {
    if (pimpl_->running) {
        pimpl_->running = false;
        is_running_ = false;
        if (pimpl_->socket_fd >= 0) {
            shutdown(pimpl_->socket_fd, SHUT_RDWR);
            close(pimpl_->socket_fd);
            pimpl_->socket_fd = -1;
        }
        if (pimpl_->worker_thread.joinable()) {
            pimpl_->worker_thread.join();
        }
        std::cout << "🛑 [P2P Mesh Engine] Stopped." << std::endl;
    }
}

bool P2pMeshNode::broadcast_packet(const MeshPacket224& packet) {
    if (pimpl_->socket_fd < 0) return false;

    sockaddr_in broad_addr{};
    broad_addr.sin_family = AF_INET;
    broad_addr.sin_port = htons(listen_port_);
    broad_addr.sin_addr.s_addr = inet_addr("255.255.255.255");

    ssize_t sent = sendto(pimpl_->socket_fd, &packet, sizeof(packet), 0,
                          (struct sockaddr*)&broad_addr, sizeof(broad_addr));

    return sent == sizeof(packet);
}

} // namespace sovereign::beta
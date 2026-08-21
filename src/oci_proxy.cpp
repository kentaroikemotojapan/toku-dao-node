#include "../include/oci_proxy.hpp"
#include <iostream>
#include <thread>
#include <atomic>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

namespace sovereign::alpha {

class OciLocalProxy::Impl {
public:
    std::atomic<bool> running{false};
    int server_fd{-1};
    std::thread worker_thread;
};

OciLocalProxy::OciLocalProxy(const std::string& listen_ip, uint16_t listen_port)
    : listen_ip_(listen_ip), listen_port_(listen_port), is_running_(false), pimpl_(std::make_unique<Impl>()) {}

OciLocalProxy::~OciLocalProxy() {
    stop();
}

bool OciLocalProxy::start_async_listener() {
    pimpl_->server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (pimpl_->server_fd < 0) {
        std::cerr << "❌ [OCI Proxy] Failed to create socket." << std::endl;
        return false;
    }

    int opt = 1;
    setsockopt(pimpl_->server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 500ms の受信タイムアウト設定（デッドロック回避）
    struct timeval tv{0, 500000};
    setsockopt(pimpl_->server_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(listen_port_);
    inet_pton(AF_INET, listen_ip_.c_str(), &address.sin_addr);

    if (bind(pimpl_->server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "❌ [OCI Proxy] Bind failed on " << listen_ip_ << ":" << listen_port_ << std::endl;
        close(pimpl_->server_fd);
        return false;
    }

    if (listen(pimpl_->server_fd, 10) < 0) {
        std::cerr << "❌ [OCI Proxy] Listen failed." << std::endl;
        close(pimpl_->server_fd);
        return false;
    }

    pimpl_->running = true;
    is_running_ = true;

    pimpl_->worker_thread = std::thread([this]() {
        while (pimpl_->running) {
            sockaddr_in client_addr{};
            socklen_t addrlen = sizeof(client_addr);
            int client_fd = accept(pimpl_->server_fd, (struct sockaddr*)&client_addr, &addrlen);
            
            if (client_fd < 0) {
                if (!pimpl_->running) break;
                continue;
            }

            char buffer[2048] = {0};
            ssize_t bytes_read = read(client_fd, buffer, sizeof(buffer) - 1);

            if (bytes_read > 0) {
                std::string request(buffer, bytes_read);

                if (request.find("GET /v2/") != std::string::npos) {
                    std::string response = 
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Docker-Distribution-Api-Version: registry/2.0\r\n"
                        "Content-Length: 2\r\n\r\n{}";
                    write(client_fd, response.c_str(), response.length());
                } else {
                    std::string response = 
                        "HTTP/1.1 202 Accepted\r\n"
                        "Content-Length: 0\r\n\r\n";
                    write(client_fd, response.c_str(), response.length());

                    OciLayerChunk chunk;
                    chunk.digest_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
                    chunk.is_final_chunk = true;
                    std::string cid;
                    this->stream_layer_to_ipfs(chunk, cid);
                }
            }
            close(client_fd);
        }
    });

    std::cout << "🚀 [OCI Proxy] Socket active on http://" << listen_ip_ << ":" << listen_port_ << std::endl;
    return true;
}

void OciLocalProxy::stop() {
    if (pimpl_->running) {
        pimpl_->running = false;
        is_running_ = false;
        if (pimpl_->server_fd >= 0) {
            shutdown(pimpl_->server_fd, SHUT_RDWR);
            close(pimpl_->server_fd);
            pimpl_->server_fd = -1;
        }
        if (pimpl_->worker_thread.joinable()) {
            pimpl_->worker_thread.join();
        }
        std::cout << "🛑 [OCI Proxy] Stopped." << std::endl;
    }
}

bool OciLocalProxy::stream_layer_to_ipfs(const OciLayerChunk& chunk, std::string& out_cid) {
    out_cid = "QmSovereignEdge" + chunk.digest_sha256.substr(0, 16);
    if (chunk.is_final_chunk && on_cid_generated_) {
        on_cid_generated_(out_cid, chunk.digest_sha256);
    }
    return true;
}

} // namespace sovereign::alpha
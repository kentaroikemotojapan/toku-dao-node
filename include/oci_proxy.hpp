#ifndef OCI_PROXY_HPP
#define OCI_PROXY_HPP

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <cstdint>

namespace sovereign::alpha {

struct OciLayerChunk {
    std::string digest_sha256;
    std::vector<uint8_t> data;
    size_t chunk_index;
    bool is_final_chunk;
};

class OciLocalProxy {
public:
    using IpfsCidCallback = std::function<void(const std::string& cid, const std::string& digest)>;

    OciLocalProxy(const std::string& listen_ip = "127.0.0.1", uint16_t listen_port = 5000);
    ~OciLocalProxy();

    bool start_async_listener();
    void stop();
    bool stream_layer_to_ipfs(const OciLayerChunk& chunk, std::string& out_cid);

    void set_on_cid_generated_callback(IpfsCidCallback cb) {
        on_cid_generated_ = cb;
    }

private:
    std::string listen_ip_;
    uint16_t listen_port_;
    bool is_running_;
    IpfsCidCallback on_cid_generated_;

    class Impl;
    std::unique_ptr<Impl> pimpl_;
};

} // namespace sovereign::alpha

#endif // OCI_PROXY_HPP
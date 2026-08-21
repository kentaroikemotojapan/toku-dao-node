#ifndef PQC_AUTH_HPP
#define PQC_AUTH_HPP

#include "ebpf_shared.h"
#include <string>
#include <vector>
#include <memory>
#include <chrono>

namespace sovereign::alpha {

struct PqcSessionKey {
    uint8_t shared_secret[32];
    uint8_t public_key[1184];
    uint8_t secret_key[2400];
    bool    is_established;
};

class PqcAuthManager {
public:
    PqcAuthManager();
    ~PqcAuthManager();

    bool generate_pqc_keypair(PqcSessionKey& out_key);

    bool generate_ephemeral_token(uint32_t container_id, 
                                  uint32_t ttl_seconds, 
                                  EphemeralTokenValue& out_token);

    bool verify_manifest_signature(const std::string& payload_cid, 
                                   const std::vector<uint8_t>& signature, 
                                   const std::vector<uint8_t>& pubkey);

    void zeroize_sensitive_memory(uint8_t* buffer, size_t size);

private:
    PqcSessionKey current_session_;

    class Impl;
    std::unique_ptr<Impl> pimpl_;
};

} // namespace sovereign::alpha

#endif // PQC_AUTH_HPP
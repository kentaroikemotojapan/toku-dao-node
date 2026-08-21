#ifndef EBPF_SHARED_H
#define EBPF_SHARED_H

#ifdef __cplusplus
#include <cstdint>
extern "C" {
#else
#include <stdint.h>
#include <linux/types.h>
#endif

#pragma pack(push, 1)

struct TokenMapKey {
    uint32_t src_ip;
    uint32_t dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
};

struct EphemeralTokenValue {
    uint8_t  token_hash[32];
    uint64_t valid_until_ns;
    uint64_t created_at_ns;
    uint32_t container_id;
    uint8_t  flags;
};

#pragma pack(pop)

#define MAX_TOKEN_ENTRIES 10240

#ifdef __cplusplus
}
#endif

#endif // EBPF_SHARED_H
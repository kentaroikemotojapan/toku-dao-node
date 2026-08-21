#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#include "../../include/ebpf_shared.h"

char LICENSE[] SEC("license") = "GPL";

// eBPF Map 定義 (ユーザー空間 C++ Proxy との共有ハッシュマップ)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, struct TokenMapKey);
    __type(value, struct EphemeralTokenValue);
    __uint(max_entries, MAX_TOKEN_ENTRIES);
} token_map SEC(".maps");

SEC("xdp")
int xdp_shield_filter(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    // 1. Ethernet ヘッダー境界検証
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) {
        return XDP_PASS;
    }

    // IPv4 以外のパケットはスルー (ローカル制御プレーン等)
    if (eth->h_proto != bpf_htons(ETH_P_IP)) {
        return XDP_PASS;
    }

    // 2. IP ヘッダー境界検証
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) {
        return XDP_PASS;
    }

    struct TokenMapKey key = {};
    key.src_ip = ip->saddr;
    key.dst_ip = ip->daddr;

    // 3. L4 (TCP / UDP) ポート抽出
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)(ip + 1);
        if ((void *)(tcp + 1) > data_end) return XDP_PASS;
        key.src_port = tcp->source;
        key.dst_port = tcp->dest;
    } else if (ip->protocol == IPPROTO_UDP) {
        struct udphdr *udp = (void *)(ip + 1);
        if ((void *)(udp + 1) > data_end) return XDP_PASS;
        key.src_port = udp->source;
        key.dst_port = udp->dest;
    } else {
        return XDP_PASS;
    }

    // 4. eBPF Map から直接ルックアップ (ナノ秒単位)
    struct EphemeralTokenValue *token = bpf_map_lookup_elem(&token_map, &key);
    if (!token) {
        // 未承認通信 ➔ レスポンスすら返さず物理遮断 (サイレント・ドロップ)
        return XDP_DROP;
    }

    // 5. 単調増加クロック (CLOCK_MONOTONIC) による超短寿命判定
    uint64_t now_ns = bpf_ktime_get_ns();
    if (now_ns > token->valid_until_ns) {
        // 期限切れトークン ➔ 即時ドロップ
        return XDP_DROP;
    }

    // 6. フラグ検証 (0x01: Active)
    if (!(token->flags & 0x01)) {
        return XDP_DROP;
    }

    // すべての安全判定合格 ➔ コンテナ / ローカルアプリ層へ通過
    return XDP_PASS;
}
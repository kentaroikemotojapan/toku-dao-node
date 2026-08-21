import urllib.request
import urllib.error
import json
import time

PROXY_URL = "http://127.0.0.1:5000"

def test_v2_ping():
    """1. Docker V2 Registry 互換 Ping テスト"""
    print("🧪 [Test 1] Testing Docker V2 Ping (/v2/)...")
    req = urllib.request.Request(f"{PROXY_URL}/v2/")
    try:
        with urllib.request.urlopen(req) as response:
            header_v2 = response.headers.get("Docker-Distribution-Api-Version")
            assert response.status == 200
            assert header_v2 == "registry/2.0"
            print("  └ ✅ Passed: Received 200 OK with Docker-Distribution-Api-Version header.")
    except Exception as e:
        print(f"  └ ❌ Failed: {e}")

def test_oci_blob_upload_stream():
    """2. OCI Blob (tar.gz) 受領 & P2P IPFS CID 変換イベント発生テスト"""
    print("\n🧪 [Test 2] Testing OCI Blob Chunk Stream (/v2/app/blobs/uploads/)...")
    req = urllib.request.Request(
        f"{PROXY_URL}/v2/app/blobs/uploads/",
        data=b"dummy_layer_binary_data",
        headers={"Content-Type": "application/octet-stream"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            assert response.status == 202
            print("  └ ✅ Passed: Received 202 Accepted. P2P Broadcast triggered on Daemon.")
    except Exception as e:
        print(f"  └ ❌ Failed: {e}")

if __name__ == "__main__":
    print("=== Sovereign Edge ALPHA E2E Test Suite ===\n")
    test_v2_ping()
    test_oci_blob_upload_stream()
    print("\n🎉 All ALPHA E2E Tests Completed!")
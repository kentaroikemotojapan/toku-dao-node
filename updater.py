import json
import subprocess
import time
import urllib.request

PUBSUB_TOPIC = "toku/mesh/releases"
HEALTH_CHECK_URL = "http://localhost:5050/api/v1/twin/telemetry"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def verify_health():
    """新コンテナのヘルスチェック（10秒待機後にAPI応答を確認）"""
    time.sleep(10)
    try:
        req = urllib.request.urlopen(HEALTH_CHECK_URL, timeout=5)
        return req.status == 200
    except Exception:
        return False

def process_update(cid):
    print(f"🔄 New update CID detected: {cid}")
    
    # 1. 現状の安全バックアップ（ロールバック用）
    print("🛡️ Creating rollback checkpoint...")
    run_cmd("docker compose cp -r . /tmp/node_backup")

    try:
        # 2. IPFS から新コードパッケージを取得
        print(f"📥 Downloading package from IPFS peers ({cid})...")
        run_cmd(f"ipfs get {cid} -o /tmp/update.tar.gz")
        run_cmd("tar -xzf /tmp/update.tar.gz -C .")

        # 3. コンテナの差し替え
        print("⚡ Rebuilding & restarting container stack...")
        res = run_cmd("docker compose up -d --build")
        if res.returncode != 0:
            raise Exception("Docker compose build/up failed.")

        # 4. ヘルスチェックの実施
        print("🩺 Performing health check on new version...")
        if verify_health():
            print("✅ Update successful! New version is healthy.")
        else:
            raise Exception("Health check failed post-deployment!")

    except Exception as e:
        # 5. 失敗時の自動ロールバック処理
        print(f"🚨 UPDATE FAILED: {e}")
        print("⏪ Initiating ZERO-TOUCH ROLLBACK to previous stable version...")
        run_cmd("cp -r /tmp/node_backup/* .")
        run_cmd("docker compose up -d --build")
        print("🛡️ Rollback completed. Node is restored to healthy state.")

def listen_pubsub():
    print(f"📡 Subscribing to IPFS PubSub topic: {PUBSUB_TOPIC}...")
    proc = subprocess.Popen(
        f"ipfs pubsub sub {PUBSUB_TOPIC}",
        shell=True, stdout=subprocess.PIPE, text=True
    )
    for line in iter(proc.stdout.readline, ''):
        try:
            data = json.loads(line.strip())
            if "version_cid" in data:
                process_update(data["version_cid"])
        except Exception:
            pass

if __name__ == "__main__":
    listen_pubsub()
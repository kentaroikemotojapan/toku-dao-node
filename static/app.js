/**
 * Antigravity Virtue IDE - Frontend Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    let editor = null;
    let addressesMap = {}; // name -> address

    // Element Selectors
    const accountsContainer = document.getElementById('accounts-container');
    const claimWalletSelect = document.getElementById('claim-wallet');
    const claimUserField = document.getElementById('claim-user');
    const claimForm = document.getElementById('claim-form');
    const logConsole = document.getElementById('log-console');
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastDesc = document.getElementById('toast-desc');

    const btnSave = document.getElementById('btn-save');
    const btnSimulate = document.getElementById('btn-simulate');
    const btnClearLogs = document.getElementById('btn-clear-logs');

    // ---------------------------------------------------------
    // RAG Dynamic Injector & 3-Agent Pipeline Logic
    // ---------------------------------------------------------
    const btnInjectRag = document.getElementById('btn-inject-rag');
    const ragContextInput = document.getElementById('rag-context-input');
    const activeIpfsCid = document.getElementById('active-ipfs-cid');

    const agent1LatencyVal = document.getElementById('agent1-latency-val');
    const agent2ScoreVal = document.getElementById('agent2-score-val');
    const agent3PeersVal = document.getElementById('agent3-peers-val');

    if (btnInjectRag) {
        btnInjectRag.addEventListener('click', async () => {
            const ragText = ragContextInput.value.trim();
            if (!ragText) return;

            btnInjectRag.disabled = true;
            btnInjectRag.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> IPFS Pinning & P2P Broadcast...';
            addLog(`[RAG-INJECT] Starting local context re-indexing for: "${ragText}"`, 'system');

            try {
                const res = await fetch('/api/v1/rag/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_name: "Admin_Node", rag_text: ragText })
                });
                const data = await res.json();

                if (data.status === 'success') {
                    // 1. IPFS CID の更新表示
                    activeIpfsCid.innerText = data.ipfs.cid;
                    addLog(`📦 [IPFS] Context pinned. CID: ${data.ipfs.cid} (${data.ipfs.bytes_pinned} bytes)`, 'success');

                    // 2. Agent 1 アニメーション
                    agent1LatencyVal.innerText = `${data.agents.agent_1_inference.latency_ms} ms`;
                    addLog(`⚡️ [Agent-1] Local M2 Metal NPU inference executed in ${data.agents.agent_1_inference.latency_ms}ms`, 'success');

                    // 3. Agent 2 アニメーション
                    agent2ScoreVal.innerText = `${data.agents.agent_2_evaluator.virtue_score}/100`;
                    addLog(`🧠 [Agent-2] Virtue Policy Evaluated. Score: ${data.agents.agent_2_evaluator.virtue_score}. Proof: ${data.agents.agent_2_evaluator.proof_hash}`, 'warning');

                    // 4. Agent 3 アニメーション
                    agent3PeersVal.innerText = `${data.agents.agent_3_sync.connected_peers} Connected`;
                    addLog(`📡 [Agent-3] Broadcasted CID via libp2p PubSub ('toku/rag/updates'). TxHash: ${data.agents.agent_3_sync.tx_hash}`, 'system');

                    showToast('RAG P2P同期完了', `新しいコンテキストがIPFS (CID: ${data.ipfs.cid.slice(0, 10)}...) に追加され、P2Pメッシュへ同期されました。`, 'success');
                }
            } catch (err) {
                addLog(`[ERROR] RAG Injection failed: ${err}`, 'danger');
                showToast('同期エラー', err.message, 'danger');
            } finally {
                btnInjectRag.disabled = false;
                btnInjectRag.innerHTML = '<i class="fa-solid fa-network-wired"></i> RAG更新 & P2P同期';
            }
        });
    }

    // ---------------------------------------------------------
    // 1. Monaco Editor Initialization
    // ---------------------------------------------------------
    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.39.0/min/vs' } });
    require(['vs/editor/editor.main'], () => {
        // Solidity用の基本的なハイライト用定義（Monaco標準のSolidityがあればロード）
        editor = monaco.editor.create(document.getElementById('monaco-editor-container'), {
            value: `// Solidity Loading...`,
            language: 'solidity',
            theme: 'vs-dark',
            automaticLayout: true,
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            roundedSelection: true,
            scrollBeyondLastLine: false,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on"
        });

        // コントラクトコードのロード
        loadContractCode();
    });

    // ---------------------------------------------------------
    // 2. API Communication Functions
    // ---------------------------------------------------------

    // コントラクト読み込み
    async function loadContractCode() {
        try {
            const res = await fetch('/api/v1/contract');
            const data = await res.json();
            if (data.status === 'success' && editor) {
                editor.setValue(data.code);
                addLog('[SYSTEM] TokuToken.sol loaded successfully from disk.', 'success');
            } else {
                addLog(`[ERROR] Failed to load contract: ${data.message}`, 'danger');
            }
        } catch (err) {
            addLog(`[ERROR] Contract fetch error: ${err}`, 'danger');
        }
    }

    // コントラクト保存 & デプロイ
    btnSave.addEventListener('click', async () => {
        if (!editor) return;
        const code = editor.getValue();
        btnSave.disabled = true;
        btnSave.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 保存中...';

        try {
            const res = await fetch('/api/v1/contract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast('保存成功', 'スマートコントラクトが保存されました。コンテナの再起動で新しい契約に更新されます。', 'success');
                addLog('[SYSTEM] TokuToken.sol saved and redeployed on filesystem.', 'success');
            } else {
                showToast('保存失敗', data.message, 'danger');
                addLog(`[ERROR] Save contract failed: ${data.message}`, 'danger');
            }
        } catch (err) {
            showToast('保存エラー', err.message, 'danger');
            addLog(`[ERROR] Save contract request error: ${err}`, 'danger');
        } finally {
            btnSave.disabled = false;
            btnSave.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> 保存 & デプロイ';
        }
    });

    // アカウント状態（台帳）のポーリング & レンダー
    async function pollStatus() {
        try {
            const res = await fetch('/api/v1/status');
            const data = await res.json();
            
            // レンダリング
            renderAccounts(data);
            
            // フォームのセレクトボックスの同期
            updateWalletSelect(data);
        } catch (err) {
            console.error('Ledger status poll failed:', err);
        }
    }

    function renderAccounts(accounts) {
        if (!accounts || Object.keys(accounts).length === 0) {
            accountsContainer.innerHTML = '<div class="loading-placeholder">No accounts available or Anvil disconnected.</div>';
            return;
        }

        let html = '';
        for (const [name, info] of Object.entries(accounts)) {
            const isPenalty = info.pending_service;
            const cardClass = isPenalty ? 'card-ledger penalty' : 'card-ledger';
            const shortAddress = info.address ? `${info.address.slice(0, 6)}...${info.address.slice(-4)}` : '0x0000';
            const virtueClass = info.virtue_score < 0 ? 'metric-value virtue negative' : 'metric-value virtue';

            html += `
                <div class="${cardClass}" data-user="${name}">
                    <div class="card-header">
                        <div class="user-info">
                            <h3>${name}</h3>
                            <div class="user-address" title="${info.address}">${shortAddress}</div>
                        </div>
                        ${isPenalty ? '<span class="penalty-badge"><i class="fa-solid fa-broom"></i> トイレ掃除</span>' : ''}
                    </div>
                    <div class="card-metrics">
                        <div class="metric-item">
                            <span class="metric-label">TOKU Balance</span>
                            <span class="metric-value tokens">${info.balance} TOKU</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Virtue Score</span>
                            <span class="metric-value ${virtueClass}">${info.virtue_score}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        accountsContainer.innerHTML = html;
    }

    function updateWalletSelect(accounts) {
        // セレクトボックスのアクティブ項目を退避
        const selectedVal = claimWalletSelect.value;
        
        let html = '<option value="" disabled selected>アドレスを選択</option>';
        for (const [name, info] of Object.entries(accounts)) {
            addressesMap[name] = info.address;
            const isSelected = selectedVal === info.address ? 'selected' : '';
            html += `<option value="${info.address}" ${isSelected}>${name} (${info.address.slice(0, 6)}...)</option>`;
        }
        claimWalletSelect.innerHTML = html;
    }

    // ユーザー名選択時に自動でウォレットアドレスを選択
    claimUserField.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();
        for (const [name, addr] of Object.entries(addressesMap)) {
            if (name.toLowerCase().includes(query)) {
                claimWalletSelect.value = addr;
                break;
            }
        }
    });

    // ---------------------------------------------------------
    // 3. Sandbox Actions
    // ---------------------------------------------------------

    // シミュレーションの一括起動
    btnSimulate.addEventListener('click', async () => {
        btnSimulate.disabled = true;
        btnSimulate.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> シミュレーション実行中...';
        addLog('[SIMULATION] Beginning full multi-agent simulation sequence...', 'system');

        try {
            const res = await fetch('/api/v1/simulate', { method: 'POST' });
            const data = await res.json();
            
            if (data.status === 'success') {
                // ログを1行ずつ少しのディレイ（50ms）を入れながらアニメーション出力
                const lines = data.logs.split('\n');
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
                    
                    let type = 'system';
                    if (line.includes('MINT_SUCCESS') || line.includes('成功!') || line.includes('Mint中')) {
                        type = 'success';
                    } else if (line.includes('🚨') || line.includes('ALERT') || line.includes('penalty') || line.includes('Service Flag')) {
                        type = 'danger';
                    } else if (line.includes('🤖') || line.includes('AI審査')) {
                        type = 'warning';
                    }

                    await delay(100);
                    addLog(line, type);
                }
                showToast('シミュレーション完了', '統合テストが正常に完了し、オンチェーン状態が更新されました。', 'success');
                pollStatus(); // 即時反映
            } else {
                addLog(`[ERROR] Simulation failed: ${data.logs}`, 'danger');
            }
        } catch (err) {
            addLog(`[ERROR] Server process error during simulation: ${err}`, 'danger');
        } finally {
            btnSimulate.disabled = false;
            btnSimulate.innerHTML = '<i class="fa-solid fa-bolt"></i> シミュレーション実行';
        }
    });

    // 手動申請の送信 (Claim Sandbox)
    claimForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userName = claimUserField.value.trim();
        const walletAddress = claimWalletSelect.value;
        const claimText = document.getElementById('claim-text').value.trim();

        if (!walletAddress) {
            showToast('未選択', '対象のアドレスを選択してください。', 'warning');
            return;
        }

        const btnSubmit = document.getElementById('btn-submit-claim');
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> AI審査中...';
        addLog(`[SANDBOX] Submitting claim for user "${userName}" to AI Oracle...`, 'system');

        try {
            const res = await fetch('/api/v1/claim', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_name: userName,
                    wallet_address: walletAddress,
                    claim_text: claimText
                })
            });
            const data = await res.json();

            // ログへの出力
            addLog(`🤖 [AI EVALUATION] Result: ${JSON.stringify(data.ai_evaluation)}`, data.community_service_flag ? 'warning' : 'success');
            if (data.onchain_tx_hash) {
                addLog(`⛓️ [EVM MINT] On-chain Tx Hash: ${data.onchain_tx_hash}`, 'success');
            }
            if (data.community_service_flag) {
                addLog(`🧹 [PENALTY] Community service flag set for user due to invalid/junk food claim!`, 'danger');
                showToast('不正検知 / スラッシング', '徳に反する申請が検知され、スラッシングおよびトイレ掃除のペナルティが課されました。', 'danger');
            } else {
                showToast('申請が承認されました！', `徳を積む行動として認められ、${data.ai_evaluation.reward_amount} TOKU がミントされました。`, 'success');
            }

            // 即時状態更新
            pollStatus();

        } catch (err) {
            addLog(`[ERROR] Claim submission failed: ${err}`, 'danger');
            showToast('送信エラー', err.message, 'danger');
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="fa-solid fa-paper-plane"></i> 申請を送信してAI判定';
        }
    });

    // ---------------------------------------------------------
    // 4. Utility Functions
    // ---------------------------------------------------------

    // ログにメッセージ追加
    function addLog(text, type = 'system') {
        const line = document.createElement('div');
        line.className = `log-line ${type}-line`;
        line.innerText = text;
        logConsole.appendChild(line);
        // 自動スクロール
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    // ログクリア
    btnClearLogs.addEventListener('click', () => {
        logConsole.innerHTML = '<div class="log-line system-line">[SYSTEM] Logs cleared. Console ready.</div>';
    });

    // トースト通知の表示
    function showToast(title, desc, type = 'success') {
        toastTitle.innerText = title;
        toastDesc.innerText = desc;
        
        // アイコンの色
        const icon = toast.querySelector('.toast-icon i');
        if (type === 'success') {
            toast.style.borderColor = 'var(--color-emerald)';
            icon.className = 'fa-solid fa-circle-check';
            icon.style.color = 'var(--color-emerald)';
        } else if (type === 'danger') {
            toast.style.borderColor = 'var(--color-rose)';
            icon.className = 'fa-solid fa-circle-exclamation';
            icon.style.color = 'var(--color-rose)';
        } else {
            toast.style.borderColor = 'var(--color-gold)';
            icon.className = 'fa-solid fa-triangle-exclamation';
            icon.style.color = 'var(--color-gold)';
        }

        toast.classList.remove('hidden');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 5000);
    }

    // 遅延処理用
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ---------------------------------------------------------
    // 5. App Initialization & Active Polling
    // ---------------------------------------------------------
    pollStatus();
    setInterval(pollStatus, 3000); // 3秒周期でオンチェーン状態を同期
});

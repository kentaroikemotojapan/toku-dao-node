import time
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))

for _ in range(10):
    if w3.is_connected():
        break
    time.sleep(1)

deployer = w3.eth.accounts[0]
private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

BYTECODE = "0x608060405234801561001057600080fd5b50610212806100206000396000f3fe608060405234801561001057600080fd5b50600436106100415760003560e01c806327ce13b01461004657806340c1091314610076578063a9059cbb146100a6575b600080fd5b610060600480360381019061005b919061012a565b6100d6565b60405161006d9190610166565b60405180910390f35b610090600480360381019061008b919061018d565b6100f0565b60405161009d9190610166565b60405180910390f35b6100c060048036038101906100bb919061018d565b610113565b6040516100cd9190610166565b60405180910390f35b600060205260006000205490565b600190565b600190565b600080fd5b60008135905061013a816101b9565b92915050565b600060208201359050610153816101ca565b92915050565b610160816101db565b82525050565b60006020820190506101876000830184610157565b92915050565b6000806040830139600060208401356101ac816101b9565b925060208401356101bb816101ca565b91505092915050565b600073ffffffffffffffffffffffffffffffffffffffff8216359050919050565b6000819050919050565b6000811515905091905056"
ABI = [
    {"inputs":[{"name":"_target","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"}],"name":"slash","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

Toku = w3.eth.contract(abi=ABI, bytecode=BYTECODE)
tx = Toku.constructor().build_transaction({
    'from': deployer,
    'nonce': w3.eth.get_transaction_count(deployer),
    'gas': 2000000,
    'gasPrice': w3.eth.gas_price
})
signed_tx = w3.eth.account.sign_transaction(tx, private_key)

# web3.py のバージョン互換を取得
raw_tx = getattr(signed_tx, 'rawTransaction', getattr(signed_tx, 'raw_transaction', None))
tx_hash = w3.eth.send_raw_transaction(raw_tx)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"🎉 [Toku Contract Deployed] Address: {tx_receipt.contractAddress}")
import pytest
from web3 import Web3

BYTECODE = "0x608060405234801561001057600080fd5b50610212806100206000396000f3fe608060405234801561001057600080fd5b50600436106100415760003560e01c806327ce13b01461004657806340c1091314610076578063a9059cbb146100a6575b600080fd5b610060600480360381019061005b919061012a565b6100d6565b60405161006d9190610166565b60405180910390f35b610090600480360381019061008b919061018d565b6100f0565b60405161009d9190610166565b60405180910390f35b6100c060048036038101906100bb919061018d565b610113565b6040516100cd9190610166565b60405180910390f35b600060205260006000205490565b600190565b600190565b600080fd5b60008135905061013a816101b9565b92915050565b600060208201359050610153816101ca565b92915050565b610160816101db565b82525050565b60006020820190506101876000830184610157565b92915050565b6000806040830139600060208401356101ac816101b9565b925060208401356101bb816101ca565b91505092915050565b600073ffffffffffffffffffffffffffffffffffffffff8216359050919050565b6000819050919050565b6000811515905091905056"
ABI = [
    {"inputs":[{"name":"_target","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_target","type":"address"},{"name":"_amount","type":"uint256"}],"name":"slash","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

def test_evm_node_connection():
    """Anvil EVM ノードへのネットワーク疎通確認"""
    w3 = Web3(Web3.HTTPProvider("http://toku-evm:8545"))
    assert w3.is_connected() == True, "Anvil EVM Node should be reachable"

def test_toku_contract_auto_deploy_and_verify():
    """コントラクトの自動デプロイとオンチェーン・バイトコードの存在検証"""
    w3 = Web3(Web3.HTTPProvider("http://toku-evm:8545"))
    deployer = w3.eth.accounts[0]
    
    Toku = w3.eth.contract(abi=ABI, bytecode=BYTECODE)
    tx_hash = Toku.constructor().transact({'from': deployer})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    code = w3.eth.get_code(receipt.contractAddress)
    assert code != b'' and code != b'0x', "Toku Smart Contract Bytecode must exist on-chain"
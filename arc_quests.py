#!/usr/bin/env python3
"""
Arc Testnet - Properly compiled contract deployment + quest activity.
Fixes: correct bytecode from solc, proper nonce handling, rate-limit retry.
"""
import json
import time
import os
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

RPC_URL = "https://rpc.testnet.arc.network"
PRIVATE_KEY_FILE = "/root/arc_wallet.key"
CHAIN_ID = 5042002

with open(PRIVATE_KEY_FILE) as f:
    priv = f.read().strip()
if not priv.startswith('0x'):
    priv = '0x' + priv
acct = Account.from_key(priv)
w3 = Web3(Web3.HTTPProvider(RPC_URL))

USDC = Web3.to_checksum_address("0x3600000000000000000000000000000000000000")
ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},
]

LOG_FILE = "/root/arc_quests_log.json"

def log_action(action, tx_hash, status):
    entry = {"action": action, "tx": tx_hash, "status": status, "time": time.strftime('%Y-%m-%d %H:%M:%S')}
    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            data = json.load(f)
    data.append(entry)
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_tx(tx_data, gas_limit=150000):
    """Build, sign, send tx with retry on rate-limit."""
    for attempt in range(3):
        try:
            nonce = w3.eth.get_transaction_count(acct.address)
            tx = {
                'chainId': CHAIN_ID,
                'from': acct.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': w3.eth.gas_price,
                **tx_data,
            }
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"    TX: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
            if receipt.status == 1:
                print(f"    ✅ Gas: {receipt.gasUsed}, Block: {receipt.blockNumber}")
                return tx_hash.hex(), receipt
            else:
                print(f"    ❌ Reverted")
                return tx_hash.hex(), receipt
        except Exception as e:
            err = str(e).lower()
            if '429' in err or 'rate limit' in err or 'too many' in err:
                wait = 15 * (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"    ❌ Error: {e}")
            return None, None
    return None, None

def main():
    print(f"{'='*60}")
    print(f"Arc Testnet Quest Automation (Fixed)")
    print(f"Wallet: {acct.address}")
    
    usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    usdc_dec = usdc_contract.functions.decimals().call()
    usdc_bal = usdc_contract.functions.balanceOf(acct.address).call() / 10**usdc_dec
    native_bal = w3.eth.get_balance(acct.address) / 10**18
    nonce = w3.eth.get_transaction_count(acct.address)
    print(f"USDC: {usdc_bal:.6f} | Native: {native_bal:.6f} | Nonce: {nonce}")
    print(f"{'='*60}")
    
    tx_count = 0

    # ---- 1. Deploy SimpleStorage contract (properly compiled) ----
    print("\n[1/5] Deploy SimpleStorage Contract")
    bytecode = open('/root/contracts/build/SimpleStorage.bin').read().strip()
    tx_hash, receipt = send_tx({'data': bytecode, 'value': 0}, gas_limit=200000)
    if tx_hash:
        if receipt and receipt.status == 1 and receipt.contractAddress:
            print(f"    ✅ Contract: {receipt.contractAddress}")
            log_action("deploy_contract", tx_hash, "ok")
            tx_count += 1
            
            # Call set(42)
            print("    Calling set(42)...")
            storage = w3.eth.contract(address=receipt.contractAddress, abi=[
                {"inputs":[{"name":"_value","type":"uint256"}],"name":"set","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[],"name":"get","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            ])
            tx_hash2, _ = send_tx({'to': receipt.contractAddress, 'data': storage.functions.set(42).build_transaction({'gas': 0, 'gasPrice': 0, 'nonce': 0, 'chainId': 0, 'from': ''})['data'], 'value': 0}, gas_limit=100000)
            if tx_hash2:
                log_action("contract_set", tx_hash2, "ok")
                tx_count += 1
        else:
            log_action("deploy_contract", tx_hash, "reverted")
    time.sleep(3)

    # ---- 2. USDC Transfers ----
    print("\n[2/5] USDC Transfers")
    tiny = int(0.000001 * 10**usdc_dec)
    targets = [
        (acct.address, "self"),
        (Web3.to_checksum_address("0x000000000000000000000000000000000000dEaD"), "burn"),
    ]
    for dest, label in targets:
        print(f"  → {label}")
        tx_hash, _ = send_tx({
            'to': USDC,
            'data': usdc_contract.functions.transfer(dest, tiny).build_transaction({'gas': 0, 'gasPrice': 0, 'nonce': 0, 'chainId': 0, 'from': ''})['data'],
            'value': 0
        }, gas_limit=100000)
        if tx_hash:
            log_action(f"usdc_transfer_{label}", tx_hash, "ok")
            tx_count += 1
        time.sleep(2)

    # ---- 3. Native transfers ----
    print("\n[3/5] Native USDC Transfers")
    for dest, label in targets[:2]:
        print(f"  → native to {label}")
        tx_hash, _ = send_tx({'to': dest, 'value': 1000, 'data': '0x'}, gas_limit=21000)
        if tx_hash:
            log_action(f"native_transfer_{label}", tx_hash, "ok")
            tx_count += 1
        time.sleep(2)

    # ---- 4. Approve USDC ----
    print("\n[4/5] Approve USDC")
    tx_hash, _ = send_tx({
        'to': USDC,
        'data': usdc_contract.functions.approve(acct.address, 2**256 - 1).build_transaction({'gas': 0, 'gasPrice': 0, 'nonce': 0, 'chainId': 0, 'from': ''})['data'],
        'value': 0
    }, gas_limit=100000)
    if tx_hash:
        log_action("approve_self", tx_hash, "ok")
        tx_count += 1
    time.sleep(2)

    # ---- 5. Sign message ----
    print("\n[5/5] Sign Message")
    try:
        msg = f"Arc Testnet Quest - Hermes Agent - {int(time.time())}"
        sig = acct.sign_message(encode_defunct(text=msg)).signature.hex()
        print(f"  Signature: {sig[:40]}...")
        log_action("sign_message", "signed", "ok")
    except Exception as e:
        print(f"  Error: {e}")
        log_action("sign_message", None, str(e))

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Transactions sent: {tx_count}")
    usdc_bal_final = usdc_contract.functions.balanceOf(acct.address).call() / 10**usdc_dec
    print(f"USDC: {usdc_bal:.6f} → {usdc_bal_final:.6f}")
    print(f"Final Nonce: {w3.eth.get_transaction_count(acct.address)}")
    print(f"Log: {LOG_FILE}")

if __name__ == "__main__":
    main()

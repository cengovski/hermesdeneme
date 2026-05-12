import os
import sys
import time
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account

# Configuration (can be overridden by environment variables)
RPC_URL = os.environ.get('RPC_URL', 'https://rpc.testnet.arc.network')
PRIVATE_KEY_FILE = os.environ.get('PRIVATE_KEY_FILE', '/root/arc_wallet.key')
USDC_ADDRESS = os.environ.get('USDC_ADDRESS', '0x3600000000000000000000000000000000000000')
EURC_ADDRESS = os.environ.get('EURC_ADDRESS', '0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a')
REPO_PATH = os.environ.get('REPO_PATH', '/root/hermesdeneme')
LOG_FILE = os.environ.get('LOG_FILE', 'ARC_DAPP_STATS.md')

# Minimal ERC20 ABI for balanceOf and decimals
ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

def main():
    try:
        # Connect to RPC
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        # Inject PoA middleware for compatibility
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not w3.is_connected():
            print("ERROR: Failed to connect to RPC")
            sys.exit(1)
        
        # Load private key
        with open(PRIVATE_KEY_FILE, 'r') as f:
            private_key = f.read().strip()
        
        account = Account.from_key(private_key)
        address = account.address
        
        # Create contract instances
        usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        eurc_contract = w3.eth.contract(address=Web3.to_checksum_address(EURC_ADDRESS), abi=ERC20_ABI)
        
        # Get balances and decimals
        usdc_balance_raw = usdc_contract.functions.balanceOf(address).call()
        usdc_decimals = usdc_contract.functions.decimals().call()
        usdc_balance = usdc_balance_raw / (10 ** usdc_decimals)
        
        eurc_balance_raw = eurc_contract.functions.balanceOf(address).call()
        eurc_decimals = eurc_contract.functions.decimals().call()
        eurc_balance = eurc_balance_raw / (10 ** eurc_decimals)
        
        # Timestamp
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        
        # Log entry
        log_entry = f"""## {timestamp}
- Wallet: {address}
- USDC Balance: {usdc_balance:,.6f} USDC
- EURC Balance: {eurc_balance:,.6f} EURC

"""
        
        # Ensure repo path exists
        os.chdir(REPO_PATH)
        
        # Append to log file
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
        
        print(f"Appended log entry to {LOG_FILE}")
        
        # Git operations
        os.system('git add {}'.format(LOG_FILE))
        # Check if there are changes to commit
        diff = os.system('git diff --cached --quiet')
        if diff != 0:
            commit_msg = f"Update Arc DApp stats log: {timestamp}"
            os.system('git commit -m "{}"'.format(commit_msg))
            print("Committed changes")
            # Push to remote
            push_result = os.system('git push')
            if push_result == 0:
                print("Pushed to remote")
            else:
                print("WARNING: Git push failed")
        else:
            print("No changes to commit")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

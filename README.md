# Arc Testnet DApp

This repository contains a simple Flask-based DApp for interacting with the Arc Testnet using a wallet private key stored on the VPS.

## Features
- View wallet address and USDC/EURC balances
- Send USDC or EURC to any address (small test amounts)
- View total supply of USDC and EURC
- Sign arbitrary messages with the wallet (agentic identity proof)

## How to Use (Locally via SSH Tunnel)

1. **Ensure you have SSH access to the VPS** (IP: 107.175.85.233) via your `Baglan.bat` or similar script.
2. **Start the DApp on the VPS** (if not already running):
   ```bash
   cd /root/arc_dapp
   /root/arc_env/bin/python3 app.py &
   ```
   The app will listen on `0.0.0.0:5000`.
3. **Set up local port forwarding** using your existing SSH tunnel (or modify `Baglan.bat` to include):
   ```
   ssh -L 5000:localhost:5000 root@107.175.85.233
   ```
   If your `Baglan.bat` already forwards other ports (e.g., 7860 for a dashboard), you can add another `-L 5000:localhost:5000` line.
4. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```
5. **Interact with the DApp** using the wallet whose private key is stored in `/root/arc_wallet.key` on the VPS.
   - You can send small amounts of USDC/EURC (e.g., 0.001) to test transactions.
   - You can sign messages to prove agentic identity.
   - All transaction hashes and results are shown in the browser.

## Notes
- The wallet private key is **never exposed** in the web interface; all signing and transaction sending happens server-side.
- This DApp is for **testnet only**. Do not use with mainnet funds.
- For security, consider restricting access via firewall or using HTTPS reverse proxy in production.

## Repository
This README and the `last_updated.txt` (updated every 30 minutes by an automated cron job) are tracked in this GitHub repository.

Last updated: {{ last_updated }}

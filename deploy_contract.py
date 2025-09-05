import json
import argparse
from web3 import Web3

def deploy_contract(api_key, private_key):
    """
    Deploys the SafaCoin smart contract to the Sepolia testnet.
    """
    # 1. Connect to the Sepolia testnet
    w3 = Web3(Web3.HTTPProvider(f'https://eth-sepolia.g.alchemy.com/v2/{api_key}'))
    if not w3.is_connected():
        raise ConnectionError("Could not connect to the Ethereum network.")
    print("Connected to Sepolia testnet.")

    # 2. Load the deployer's account
    deployer_account = w3.eth.account.from_key(private_key)
    w3.eth.default_account = deployer_account.address
    print(f"Using deployer account: {deployer_account.address}")

    # 3. Load contract ABI and bytecode
    with open("contracts/SafaCoin.abi", "r") as f:
        abi = json.load(f)
    with open("contracts/SafaCoin.bin", "r") as f:
        bytecode = f.read()
    print("Loaded contract ABI and bytecode.")

    # 4. Create contract instance
    SafaCoin = w3.eth.contract(abi=abi, bytecode=bytecode)

    # 5. Build the deployment transaction
    # The constructor requires the initialOwner address
    constructor_args = [deployer_account.address]
    print("Building deployment transaction...")
    tx = SafaCoin.constructor(*constructor_args).build_transaction({
        'from': deployer_account.address,
        'nonce': w3.eth.get_transaction_count(deployer_account.address),
    })
    print("Deployment transaction built.")

    # 6. Sign the transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    print("Transaction signed.")

    # 7. Send the transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent. TX Hash: {tx_hash.hex()}")

    # 8. Wait for the transaction to be mined
    print("Waiting for transaction to be mined...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction mined.")

    # 9. Get and print the contract address
    contract_address = tx_receipt['contractAddress']
    print(f"✅ Contract deployed successfully at address: {contract_address}")
    
    # Save the address for later use
    address_file = "contracts/contract_address.txt"
    with open(address_file, "w") as f:
        f.write(contract_address)
    print(f"Contract address saved to {address_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy the SafaCoin smart contract.")
    parser.add_argument("api_key", help="Your Alchemy API key.")
    parser.add_argument("private_key", help="The private key of your deployment wallet.")
    args = parser.parse_args()

    deploy_contract(args.api_key, args.private_key)

#!/usr/bin/env python3
"""
Deployment script for the Carpool smart contract
This script deploys the compiled Carpool contract to an Ethereum network
"""

import os
import json
import time
import logging
import argparse
from pathlib import Path
from web3 import Web3, HTTPProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine the directory where this script is located
script_dir = Path(__file__).parent.resolve()

# Smart contract file paths
compiled_contract_path = script_dir / "carpool_contract.json"

def load_contract_data():
    """Load the compiled contract data from JSON file"""
    try:
        if not compiled_contract_path.exists():
            logger.error(f"Compiled contract file not found: {compiled_contract_path}")
            return None
        
        with open(compiled_contract_path, 'r') as f:
            contract_data = json.load(f)
        
        return contract_data
    except Exception as e:
        logger.error(f"Error loading contract data: {e}")
        return None

def connect_to_ethereum(rpc_url):
    """Connect to Ethereum network using Web3"""
    try:
        web3 = Web3(HTTPProvider(rpc_url))
        if web3.is_connected():
            network_id = web3.eth.chain_id
            block_number = web3.eth.block_number
            logger.info(f"Connected to Ethereum network. Chain ID: {network_id}, Latest block: {block_number}")
            return web3
        else:
            logger.error(f"Failed to connect to Ethereum network at {rpc_url}")
            return None
    except Exception as e:
        logger.error(f"Error connecting to Ethereum network: {e}")
        return None

def deploy_contract(web3, contract_data, deployer_address, private_key=None):
    """Deploy the contract to the Ethereum network"""
    try:
        # Get contract elements
        abi = contract_data['abi']
        bytecode = contract_data['bytecode']
        
        # Create contract instance
        contract = web3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Get deployer's account information
        nonce = web3.eth.get_transaction_count(deployer_address)
        gas_price = web3.eth.gas_price
        
        # Estimate gas for deployment
        gas_estimate = contract.constructor().estimate_gas({'from': deployer_address})
        logger.info(f"Estimated gas for deployment: {gas_estimate}")
        
        # Create deployment transaction
        deploy_txn = contract.constructor().build_transaction({
            'from': deployer_address,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        
        # Sign transaction if private key is provided
        if private_key:
            signed_txn = web3.eth.account.sign_transaction(deploy_txn, private_key)
            # Send the transaction
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        else:
            # Send the transaction using the connected node's accounts
            tx_hash = web3.eth.send_transaction(deploy_txn)
        
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        logger.info("Waiting for transaction receipt...")
        
        # Wait for the transaction receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        contract_address = tx_receipt.contractAddress
        
        logger.info(f"Contract deployed at address: {contract_address}")
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        logger.info(f"Gas used: {tx_receipt.gasUsed}")
        
        # Update the contract JSON with deployment info
        contract_data['address'] = contract_address
        contract_data['network'] = {
            'chainId': web3.eth.chain_id,
            'deployedAt': int(time.time()),
        }
        
        # Save updated contract data
        with open(compiled_contract_path, 'w') as f:
            json.dump(contract_data, f, indent=2)
        
        logger.info(f"Updated contract data saved to {compiled_contract_path}")
        
        return {
            'address': contract_address,
            'hash': tx_hash.hex(),
            'gasUsed': tx_receipt.gasUsed
        }
    
    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        return None

def main():
    """Main function to deploy the contract"""
    parser = argparse.ArgumentParser(description='Deploy Carpool smart contract to Ethereum')
    parser.add_argument('--rpc', default='http://127.0.0.1:7545', help='Ethereum RPC URL (default: http://127.0.0.1:7545)')
    parser.add_argument('--address', required=True, help='Deployer Ethereum address')
    parser.add_argument('--key', help='Private key for the deployer (optional, only needed if the node does not manage the account)')
    
    args = parser.parse_args()
    
    logger.info("Starting contract deployment")
    
    # Load contract data
    contract_data = load_contract_data()
    if not contract_data:
        logger.error("Failed to load contract data")
        return False
    
    # Connect to Ethereum
    web3 = connect_to_ethereum(args.rpc)
    if not web3:
        logger.error("Failed to connect to Ethereum network")
        return False
    
    # Validate deployer address
    if not web3.is_address(args.address):
        logger.error(f"Invalid Ethereum address: {args.address}")
        return False
    
    # Check if we have enough balance
    balance = web3.eth.get_balance(args.address)
    balance_eth = web3.from_wei(balance, 'ether')
    logger.info(f"Deployer balance: {balance_eth} ETH")
    
    if balance_eth < 0.01:
        logger.warning(f"Low balance ({balance_eth} ETH). Deployment might fail.")
    
    # Deploy the contract
    result = deploy_contract(web3, contract_data, args.address, args.key)
    if not result:
        logger.error("Contract deployment failed")
        return False
    
    logger.info("Contract deployment completed successfully")
    logger.info(f"Contract address: {result['address']}")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

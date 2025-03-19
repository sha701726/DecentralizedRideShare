#!/usr/bin/env python3
"""
Compile script for the Carpool smart contract
This script compiles the Carpool.sol contract and writes the ABI and bytecode to a JSON file
"""

import os
import json
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine the directory where this script is located
script_dir = Path(__file__).parent.resolve()

# Smart contract file
contract_file = script_dir / "Carpool.sol"
output_json_file = script_dir / "carpool_contract.json"

def check_solc():
    """Check if solc (Solidity compiler) is installed"""
    try:
        # Check if solc is installed and get its version
        result = subprocess.run(['solc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Found solc: {result.stdout.splitlines()[0]}")
            return True
        else:
            logger.error("solc check returned non-zero exit code")
            return False
    except Exception as e:
        logger.error(f"Error checking solc: {e}")
        return False

def compile_contract():
    """Compile the smart contract and extract ABI and bytecode"""
    if not contract_file.exists():
        logger.error(f"Contract file not found: {contract_file}")
        return False
    
    try:
        # Compile contract
        logger.info(f"Compiling contract: {contract_file}")
        
        # Use subprocess to run solc compiler
        result = subprocess.run([
            'solc',
            '--optimize',  # Enable optimization
            '--combined-json', 'abi,bin',  # Get ABI and binary
            str(contract_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Compilation failed: {result.stderr}")
            return False
        
        # Parse the JSON output
        output = json.loads(result.stdout)
        
        # Get contract name (assumes Carpool.sol contains only one contract named "Carpool")
        contract_path = f"{contract_file}:Carpool"
        if contract_path not in output['contracts']:
            contract_paths = list(output['contracts'].keys())
            if not contract_paths:
                logger.error("No contracts found in compiler output")
                return False
            # Take the first contract if the expected name is not found
            contract_path = contract_paths[0]
            logger.warning(f"Expected contract 'Carpool' not found, using '{contract_path}' instead")
        
        contract_data = output['contracts'][contract_path]
        
        # Extract ABI and bytecode
        abi = json.loads(contract_data['abi'])
        bytecode = contract_data['bin']
        
        # Create contract JSON data
        contract_json = {
            "contractName": "Carpool",
            "abi": abi,
            "bytecode": bytecode,
            "address": None,  # Will be filled after deployment
            "network": None,  # Will be filled after deployment
        }
        
        # Write to output file
        with open(output_json_file, 'w') as f:
            json.dump(contract_json, f, indent=2)
        
        logger.info(f"Contract compiled successfully. Output written to {output_json_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error compiling contract: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting contract compilation")
    
    # Check if solc is installed
    if not check_solc():
        logger.error("solc (Solidity compiler) not found. Please install solc.")
        logger.error("You can install it with: npm install -g solc")
        return False
    
    # Compile the contract
    if not compile_contract():
        logger.error("Contract compilation failed")
        return False
    
    logger.info("Contract compilation completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

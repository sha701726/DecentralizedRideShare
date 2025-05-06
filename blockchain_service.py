import os
import json
import logging
from web3 import Web3
from config import get_config

logger = logging.getLogger(__name__)

class BlockchainService:
    """Service for interacting with the Ethereum blockchain"""
    
    def __init__(self):
        """Initialize the blockchain connection"""
        # Get configuration
        config = get_config()
        
        # Check if we should use real blockchain or dev mode
        self.dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
        
        if self.dev_mode:
            logger.info("Running in development mode, blockchain operations will be simulated")
            self.w3 = None
            self.contract = None
            return
            
        # Use Infura or other Ethereum nodes
        ethereum_url = config.ETHEREUM_NODE_URL
        if ethereum_url.endswith('/'):
            # Append Infura project ID if using Infura
            if 'infura.io' in ethereum_url and config.INFURA_PROJECT_ID:
                ethereum_url += config.INFURA_PROJECT_ID
        
        try:
            # If we don't have an Infura Project ID and the URL requires it, run in dev mode
            if 'infura.io' in ethereum_url and not config.INFURA_PROJECT_ID:
                logger.warning("No Infura Project ID provided, running in development mode")
                self.dev_mode = True
                self.w3 = None
                self.contract = None
                return
                
            self.w3 = Web3(Web3.HTTPProvider(ethereum_url))
            
            # Check connection
            if self.w3.is_connected():
                logger.info(f"Connected to Ethereum node at {ethereum_url}")
                logger.info(f"Current block number: {self.w3.eth.block_number}")
            else:
                logger.error(f"Failed to connect to Ethereum node at {ethereum_url}")
                logger.warning("Running in development mode due to connection failure")
                self.dev_mode = True
                self.w3 = None
                
            # Load smart contract
            self._load_contract()
            
        except Exception as e:
            logger.error(f"Error initializing blockchain service: {str(e)}")
            logger.warning("Running in development mode due to initialization error")
            # Initialize with None values instead of raising an exception
            self.dev_mode = True
            self.w3 = None
            self.contract = None
    
    def _load_contract(self):
        """Load the compiled smart contract"""
        if not self.w3:
            logger.warning("Web3 connection not established. Cannot load contract.")
            self.contract = None
            return
            
        try:
            # Path to the contract ABI
            carpool_contract_path = 'smart_contracts/carpool_contract.json'
            
            # Check if contract file exists
            if not os.path.exists(carpool_contract_path):
                logger.warning(f"Contract file not found at {carpool_contract_path}")
                self.contract = None
                return
            
            # Load contract data
            with open(carpool_contract_path, 'r') as f:
                contract_data = json.load(f)
            
            contract_address = get_config().CONTRACT_ADDRESS or contract_data.get('address')
            contract_abi = contract_data.get('abi')
            
            if not contract_address or not contract_abi:
                logger.warning("Contract address or ABI not found")
                self.contract = None
                return
            
            # Create contract instance
            self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            logger.info(f"Loaded carpool contract at {contract_address}")
                
        except Exception as e:
            logger.error(f"Error loading contract: {str(e)}")
            self.contract = None
    
    def create_ride(self, driver_address, start_location, end_location, price, available_seats):
        """Create a new ride on the blockchain"""
        # In dev mode, simulate a successful transaction
        if self.dev_mode:
            import random
            # Generate mock transaction hash
            tx_hash = '0x' + ''.join(random.choice('0123456789abcdef') for _ in range(64))
            # Generate a mock ride ID
            ride_id = random.randint(1, 1000)
            
            logger.info(f"Dev mode: Simulated ride creation with ID: {ride_id}")
            return {
                'tx_hash': tx_hash,
                'ride_id': ride_id
            }
            
        # Normal blockchain operation
        if not self.w3 or not self.contract:
            logger.error("Blockchain service not properly initialized")
            return None
        
        try:
            # Convert price from ETH to Wei
            price_wei = self.w3.to_wei(price, 'ether')
            
            # Estimate gas
            gas_estimate = self.contract.functions.createRide(
                start_location, 
                end_location, 
                price_wei,
                available_seats
            ).estimate_gas({'from': driver_address})
            
            # Execute transaction
            tx_hash = self.contract.functions.createRide(
                start_location, 
                end_location, 
                price_wei,
                available_seats
            ).transact({
                'from': driver_address,
                'gas': gas_estimate
            })
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Ride created on blockchain. Transaction hash: {tx_hash.hex()}")
            
            # Get the ride ID from the event logs
            ride_created_event = self.contract.events.RideCreated().process_receipt(tx_receipt)
            ride_id = ride_created_event[0]['args']['rideId']
            
            return {
                'tx_hash': tx_hash.hex(),
                'ride_id': ride_id
            }
            
        except Exception as e:
            logger.error(f"Error creating ride on blockchain: {str(e)}")
            return None
    
    def book_ride(self, passenger_address, ride_id, price):
        """Book a ride on the blockchain"""
        # In dev mode, simulate a successful transaction
        if self.dev_mode:
            import random
            # Generate mock transaction hash
            tx_hash = '0x' + ''.join(random.choice('0123456789abcdef') for _ in range(64))
            
            logger.info(f"Dev mode: Simulated ride booking for ride ID: {ride_id}")
            return {
                'tx_hash': tx_hash,
                'status': 'success'
            }
            
        # Normal blockchain operation
        if not self.w3 or not self.contract:
            logger.error("Blockchain service not properly initialized")
            return None
        
        try:
            # Convert price from ETH to Wei
            price_wei = self.w3.to_wei(price, 'ether')
            
            # Book the ride (sending ETH)
            tx_hash = self.contract.functions.bookRide(ride_id, 1).transact({
                'from': passenger_address,
                'value': price_wei
            })
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Ride booked on blockchain. Transaction hash: {tx_hash.hex()}")
            
            return {
                'tx_hash': tx_hash.hex(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error booking ride on blockchain: {str(e)}")
            return None
    
    def complete_ride(self, driver_address, ride_id):
        """Mark a ride as completed on the blockchain"""
        # In dev mode, simulate a successful transaction
        if self.dev_mode:
            import random
            # Generate mock transaction hash
            tx_hash = '0x' + ''.join(random.choice('0123456789abcdef') for _ in range(64))
            
            logger.info(f"Dev mode: Simulated ride completion for ride ID: {ride_id}")
            return {
                'tx_hash': tx_hash,
                'status': 'success'
            }
            
        # Normal blockchain operation
        if not self.w3 or not self.contract:
            logger.error("Blockchain service not properly initialized")
            return None
        
        try:
            # Complete the ride
            tx_hash = self.contract.functions.completeRide(ride_id).transact({
                'from': driver_address
            })
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Ride completed on blockchain. Transaction hash: {tx_hash.hex()}")
            
            return {
                'tx_hash': tx_hash.hex(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error completing ride on blockchain: {str(e)}")
            return None
    
    def get_ride(self, ride_id):
        """Get ride details from the blockchain"""
        # In dev mode, return mock ride data
        if self.dev_mode:
            logger.info(f"Dev mode: Returning mock ride data for ride ID: {ride_id}")
            return {
                'driver': '0x' + ''.join(['0' for _ in range(40)]),
                'start_location': 'Mock Start Location',
                'end_location': 'Mock End Location',
                'price': 0.1,  # Mock price in ETH
                'available_seats': 3,
                'is_available': True
            }
            
        # Normal blockchain operation
        if not self.w3 or not self.contract:
            logger.error("Blockchain service not properly initialized")
            return None
        
        try:
            # Call the contract to get ride details
            ride = self.contract.functions.getRide(ride_id).call()
            
            return {
                'driver': ride[0],
                'start_location': ride[1],
                'end_location': ride[2],
                'price': self.w3.from_wei(ride[3], 'ether'),
                'available_seats': ride[4],
                'is_available': ride[5]
            }
            
        except Exception as e:
            logger.error(f"Error getting ride from blockchain: {str(e)}")
            return None

    def get_active_rides(self, offset=0, limit=10):
        """Get active rides from the blockchain"""
        # In dev mode, return mock ride data
        if self.dev_mode:
            import random
            
            # Create a list of mock rides
            ride_list = []
            for i in range(min(limit, 5)):  # Return up to 5 mock rides
                ride_id = offset + i + 1
                ride_list.append({
                    'id': ride_id,
                    'driver': '0x' + ''.join(['0' for _ in range(40)]),
                    'start_location': f'Mock Start Location {ride_id}',
                    'end_location': f'Mock End Location {ride_id}',
                    'price': round(random.uniform(0.05, 0.5), 3),  # Random price between 0.05 and 0.5 ETH
                    'available_seats': random.randint(1, 4)  # Random seats between 1 and 4
                })
                
            logger.info(f"Dev mode: Returning {len(ride_list)} mock active rides")
            return ride_list
            
        # Normal blockchain operation
        if not self.w3 or not self.contract:
            logger.error("Blockchain service not properly initialized")
            return None
        
        try:
            # Call the contract to get active rides
            rides = self.contract.functions.getActiveRides(offset, limit).call()
            
            # Format the results
            ride_list = []
            for i in range(len(rides[0])):
                ride_list.append({
                    'id': rides[0][i],
                    'driver': rides[1][i],
                    'start_location': rides[2][i],
                    'end_location': rides[3][i],
                    'price': self.w3.from_wei(rides[4][i], 'ether'),
                    'available_seats': rides[5][i]
                })
            
            return ride_list
            
        except Exception as e:
            logger.error(f"Error getting active rides from blockchain: {str(e)}")
            return None

# Create a singleton instance
blockchain_service = BlockchainService()

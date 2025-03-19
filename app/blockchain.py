import os
import json
import logging
from web3 import Web3

logger = logging.getLogger(__name__)

class BlockchainService:
    """Service for interacting with the Ethereum blockchain"""
    
    def __init__(self):
        """Initialize the blockchain connection"""
        # For development, connect to a local Ethereum node (like Ganache)
        # In production, use Infura or other Ethereum nodes
        ethereum_url = os.environ.get('ETHEREUM_NODE_URL', 'http://127.0.0.1:7545')
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(ethereum_url))
            
            # Check connection
            try:
                if self.w3.is_connected():
                    logger.info(f"Connected to Ethereum node at {ethereum_url}")
                    logger.info(f"Current block number: {self.w3.eth.block_number}")
                else:
                    logger.error(f"Failed to connect to Ethereum node at {ethereum_url}")
            except Exception as e:
                logger.error(f"Error checking Ethereum connection: {str(e)}")
                self.w3 = None
                
            # Load smart contract
            self._load_contract()
            
        except Exception as e:
            logger.error(f"Error initializing blockchain service: {str(e)}")
            # Initialize with None values instead of raising an exception
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
            carpool_contract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'smart-contracts', 'carpool_contract.json')
            
            # Check if contract file exists
            if not os.path.exists(carpool_contract_path):
                logger.warning(f"Contract file not found at {carpool_contract_path}")
                self.contract = None
                return
            
            # Load contract data
            with open(carpool_contract_path, 'r') as f:
                contract_data = json.load(f)
            
            contract_address = os.environ.get('CONTRACT_ADDRESS', contract_data.get('address'))
            contract_abi = contract_data.get('abi')
            
            if not contract_address or not contract_abi:
                logger.warning("Contract address or ABI not found")
                self.contract = None
                return
            
            # Create contract instance
            try:
                self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
                logger.info(f"Loaded carpool contract at {contract_address}")
            except Exception as e:
                logger.error(f"Error creating contract instance: {str(e)}")
                self.contract = None
                
        except Exception as e:
            logger.error(f"Error loading contract: {str(e)}")
            self.contract = None
    
    def create_ride(self, driver_address, start_location, end_location, price, available_seats):
        """Create a new ride on the blockchain"""
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
        if not self.w3 or not self.contract:
            logger.error("Blockchain service not properly initialized")
            return None
        
        try:
            # Convert price from ETH to Wei
            price_wei = self.w3.to_wei(price, 'ether')
            
            # Book the ride (sending ETH)
            tx_hash = self.contract.functions.bookRide(ride_id).transact({
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

# Create a singleton instance
blockchain_service = BlockchainService()

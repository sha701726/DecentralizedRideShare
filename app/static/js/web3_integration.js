// web3_integration.js - Handles integration with Web3.js for Ethereum blockchain interaction

class Web3Integration {
    constructor() {
        this.web3 = null;
        this.accounts = [];
        this.carpool_contract = null;
        this.initialized = false;
        
        // Try to initialize on creation
        this.init();
    }
    
    async init() {
        try {
            // Check if MetaMask is installed
            if (window.ethereum) {
                console.log("Modern web3 provider detected.");
                this.web3 = new Web3(window.ethereum);
                
                // We don't automatically request accounts on page load as it's better practice
                // to request them when user clicks a specific button
                
                // Try loading contract if we have the necessary global variables
                if (window.CONTRACT_ADDRESS && window.CONTRACT_ABI) {
                    this.carpool_contract = new this.web3.eth.Contract(
                        window.CONTRACT_ABI,
                        window.CONTRACT_ADDRESS
                    );
                    console.log("Carpool contract loaded successfully");
                } else {
                    console.warn("Contract address or ABI not provided");
                }
                
                this.initialized = true;
                console.log("Web3 integration initialized");
                
                // Listen for account changes
                window.ethereum.on('accountsChanged', (accounts) => {
                    console.log('Account changed:', accounts[0]);
                    this.accounts = accounts;
                    this.triggerEvent('accountChanged', { account: accounts[0] });
                });
                
                // Listen for chain changes
                window.ethereum.on('chainChanged', (chainId) => {
                    console.log('Network changed:', chainId);
                    // Reload the page when the chain changes
                    window.location.reload();
                });
                
            } else if (window.web3) {
                // Legacy web3 provider
                console.log("Legacy web3 provider detected. Consider upgrading.");
                this.web3 = new Web3(window.web3.currentProvider);
                this.initialized = true;
            } else {
                console.warn("No web3 provider detected. Please install MetaMask or similar.");
                this.triggerEvent('noProvider', {});
            }
        } catch (error) {
            console.error("Error initializing Web3:", error);
            this.initialized = false;
        }
    }
    
    async connectWallet() {
        if (!this.web3) {
            console.error("Web3 not initialized");
            return { success: false, error: "Web3 not initialized. Please install MetaMask." };
        }
        
        try {
            // Request account access
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            this.accounts = accounts;
            console.log("Connected account:", accounts[0]);
            
            this.triggerEvent('walletConnected', { account: accounts[0] });
            return { success: true, account: accounts[0] };
        } catch (error) {
            console.error("Error connecting wallet:", error);
            return { success: false, error: error.message };
        }
    }
    
    async getAccount() {
        if (!this.web3) {
            return null;
        }
        
        if (this.accounts.length > 0) {
            return this.accounts[0];
        }
        
        try {
            const accounts = await this.web3.eth.getAccounts();
            this.accounts = accounts;
            return accounts.length > 0 ? accounts[0] : null;
        } catch (error) {
            console.error("Error getting account:", error);
            return null;
        }
    }
    
    async getBalance(address) {
        if (!this.web3) {
            return null;
        }
        
        try {
            const balance = await this.web3.eth.getBalance(address);
            return this.web3.utils.fromWei(balance, 'ether');
        } catch (error) {
            console.error("Error getting balance:", error);
            return null;
        }
    }
    
    /**
     * Create a ride on the blockchain
     */
    async createRide(startLocation, endLocation, price, availableSeats) {
        if (!this.carpool_contract || !this.web3) {
            return { success: false, error: "Contract or Web3 not initialized" };
        }
        
        const account = await this.getAccount();
        if (!account) {
            return { success: false, error: "No account connected" };
        }
        
        try {
            // Convert price to wei
            const priceWei = this.web3.utils.toWei(price.toString(), 'ether');
            
            // Create transaction
            const result = await this.carpool_contract.methods.createRide(
                startLocation,
                endLocation,
                priceWei,
                availableSeats
            ).send({
                from: account,
                gas: 3000000 // Gas limit
            });
            
            console.log("Ride created:", result);
            return { 
                success: true, 
                transactionHash: result.transactionHash,
                events: result.events
            };
        } catch (error) {
            console.error("Error creating ride:", error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Book a ride on the blockchain
     */
    async bookRide(rideId, price) {
        if (!this.carpool_contract || !this.web3) {
            return { success: false, error: "Contract or Web3 not initialized" };
        }
        
        const account = await this.getAccount();
        if (!account) {
            return { success: false, error: "No account connected" };
        }
        
        try {
            // Convert price to wei
            const priceWei = this.web3.utils.toWei(price.toString(), 'ether');
            
            // Book the ride
            const result = await this.carpool_contract.methods.bookRide(rideId).send({
                from: account,
                value: priceWei,
                gas: 3000000 // Gas limit
            });
            
            console.log("Ride booked:", result);
            return { 
                success: true, 
                transactionHash: result.transactionHash,
                events: result.events
            };
        } catch (error) {
            console.error("Error booking ride:", error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Complete a ride (called by the driver)
     */
    async completeRide(rideId) {
        if (!this.carpool_contract || !this.web3) {
            return { success: false, error: "Contract or Web3 not initialized" };
        }
        
        const account = await this.getAccount();
        if (!account) {
            return { success: false, error: "No account connected" };
        }
        
        try {
            // Complete the ride
            const result = await this.carpool_contract.methods.completeRide(rideId).send({
                from: account,
                gas: 3000000 // Gas limit
            });
            
            console.log("Ride completed:", result);
            return { 
                success: true, 
                transactionHash: result.transactionHash,
                events: result.events
            };
        } catch (error) {
            console.error("Error completing ride:", error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Get ride details from the blockchain
     */
    async getRide(rideId) {
        if (!this.carpool_contract || !this.web3) {
            return { success: false, error: "Contract or Web3 not initialized" };
        }
        
        try {
            const ride = await this.carpool_contract.methods.rides(rideId).call();
            
            // Format the data
            return {
                success: true,
                ride: {
                    driver: ride.driver,
                    startLocation: ride.startLocation,
                    endLocation: ride.endLocation,
                    price: this.web3.utils.fromWei(ride.price, 'ether'),
                    priceWei: ride.price,
                    availableSeats: ride.availableSeats,
                    isAvailable: ride.isAvailable
                }
            };
        } catch (error) {
            console.error("Error getting ride:", error);
            return { success: false, error: error.message };
        }
    }
    
    // Utility method to trigger custom events
    triggerEvent(eventName, data) {
        const event = new CustomEvent('web3-' + eventName, { detail: data });
        document.dispatchEvent(event);
    }
}

// Create a global instance
const web3Integration = new Web3Integration();

// Export for module usage
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = web3Integration;
}

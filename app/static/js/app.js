// Main application JavaScript

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DeCarpooling app initialized');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Listen for Web3 events
    document.addEventListener('web3-walletConnected', function(e) {
        console.log('Wallet connected event received', e.detail);
        updateWalletUI(e.detail.account);
    });
    
    document.addEventListener('web3-accountChanged', function(e) {
        console.log('Account changed event received', e.detail);
        updateWalletUI(e.detail.account);
    });
    
    document.addEventListener('web3-noProvider', function(e) {
        console.log('No provider event received');
        showWalletWarning();
    });
    
    // Connect wallet buttons
    const connectButtons = document.querySelectorAll('.connect-wallet-btn');
    if (connectButtons) {
        connectButtons.forEach(button => {
            button.addEventListener('click', async function() {
                await connectWallet();
            });
        });
    }
    
    // Handle form submissions with AJAX if needed
    setupFormHandlers();
});

// Connect to Web3 wallet
async function connectWallet() {
    // Check if web3Integration is available (loaded from web3_integration.js)
    if (typeof web3Integration !== 'undefined') {
        try {
            const result = await web3Integration.connectWallet();
            
            if (result.success) {
                console.log('Wallet connected:', result.account);
                // Update UI to show connected wallet
                updateWalletUI(result.account);
                
                // If we have an ethereum_address input field, fill it
                const addressInput = document.getElementById('ethereum_address');
                if (addressInput) {
                    addressInput.value = result.account;
                }
                
                return result.account;
            } else {
                showError('Wallet Connection Error', result.error);
                return null;
            }
        } catch (error) {
            console.error('Error connecting wallet:', error);
            showError('Wallet Connection Error', error.message);
            return null;
        }
    } else {
        showError('Web3 Not Available', 'Web3 integration is not available. Please ensure you have MetaMask or another wallet installed.');
        return null;
    }
}

// Update wallet UI elements
function updateWalletUI(account) {
    // Update any wallet display elements
    const walletAddressElements = document.querySelectorAll('.wallet-address');
    walletAddressElements.forEach(el => {
        el.textContent = formatAddress(account);
    });
    
    // Show any hidden wallet-connected elements
    const walletConnectedElements = document.querySelectorAll('.wallet-connected');
    walletConnectedElements.forEach(el => {
        el.style.display = 'block';
    });
    
    // Hide any wallet-disconnected elements
    const walletDisconnectedElements = document.querySelectorAll('.wallet-disconnected');
    walletDisconnectedElements.forEach(el => {
        el.style.display = 'none';
    });
    
    // Update connect wallet buttons
    const connectButtons = document.querySelectorAll('.connect-wallet-btn');
    connectButtons.forEach(button => {
        button.innerHTML = `<i class="fas fa-check-circle me-2"></i>Connected: ${formatAddress(account)}`;
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
    });
}

// Format Ethereum address for display
function formatAddress(address) {
    if (!address) return '';
    return address.substring(0, 6) + '...' + address.substring(address.length - 4);
}

// Show wallet warning
function showWalletWarning() {
    const warningContainer = document.getElementById('wallet-warning');
    if (warningContainer) {
        warningContainer.innerHTML = `
            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Web3 Wallet Required</strong> - Please install MetaMask or another Ethereum wallet to use all features.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }
}

// Show error message
function showError(title, message) {
    // Create a Bootstrap alert
    const alertHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <strong>${title}</strong> - ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Find error container or create one
    let errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-container';
        errorContainer.className = 'container mt-3';
        document.body.insertBefore(errorContainer, document.body.firstChild);
    }
    
    // Show error
    errorContainer.innerHTML = alertHTML;
}

// Setup form handlers for AJAX submissions
function setupFormHandlers() {
    // Booking form handler
    const bookingForm = document.querySelector('.booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Get form data
            const rideId = this.dataset.rideId;
            const priceEth = parseFloat(document.getElementById('total_price').value);
            
            if (!rideId || isNaN(priceEth)) {
                showError('Form Error', 'Invalid ride data');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
            submitBtn.disabled = true;
            
            try {
                // Submit the form normally - the backend will handle the blockchain transaction
                this.submit();
            } catch (error) {
                console.error('Error submitting form:', error);
                showError('Booking Error', error.message);
                
                // Reset button
                submitBtn.innerHTML = originalBtnText;
                submitBtn.disabled = false;
            }
        });
    }
}

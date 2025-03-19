# DeCarpooling - Decentralized Carpooling Platform

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [Smart Contract](#smart-contract)
6. [API Reference](#api-reference)
7. [Installation and Setup](#installation-and-setup)
8. [User Guide](#user-guide)
9. [Development Guide](#development-guide)
10. [External Services](#external-services)
11. [Deployment Guide](#deployment-guide)
12. [Future Enhancements](#future-enhancements)

## Introduction

DeCarpooling is a decentralized carpooling platform that combines traditional web technologies with blockchain capabilities. The system handles ride creation, booking, payments, and decentralized storage of user profiles and ride information.

The platform aims to solve the following problems:
- **Trust issues** in traditional carpooling by using blockchain to verify transactions
- **Payment processing** using cryptocurrency for secure and immediate payments
- **User reputation** stored in a decentralized manner
- **Ride verification** through smart contracts
- **Decentralized storage** of user profiles via IPFS

## System Architecture

DeCarpooling follows a hybrid architecture with both centralized and decentralized components:

### Centralized Components
- **Web Application**: Flask-based web server providing the user interface and API endpoints
- **Database**: PostgreSQL database for storing user accounts, ride details, and booking information
- **Authentication System**: Traditional username/password authentication with Flask-Login

### Decentralized Components
- **Blockchain Integration**: Ethereum blockchain for payment processing and ride verification
- **Smart Contracts**: Solidity smart contract for ride creation, booking, and completion
- **IPFS Storage**: Decentralized file storage for user profiles and extra information

### System Flow
1. Users register through the web interface, creating both a database account and blockchain identity
2. Drivers can create ride offers, which are stored in both the database and smart contract
3. Passengers can book rides, with payments processed through the smart contract
4. Upon ride completion, the smart contract handles the payment to the driver
5. Users can leave reviews, which affect the reputation score stored in the system

## Technology Stack

### Backend
- **Python 3.11**: Core programming language
- **Flask**: Web framework for the application
- **Flask-SQLAlchemy**: ORM for database interactions
- **Flask-Login**: User authentication management
- **Web3.py**: Ethereum blockchain interface
- **Gunicorn**: WSGI HTTP Server for production

### Database
- **PostgreSQL**: Relational database for data storage

### Blockchain
- **Ethereum**: Blockchain platform for smart contracts
- **Solidity**: Smart contract programming language
- **Web3.js**: Frontend JavaScript library for blockchain interaction

### Frontend
- **HTML/CSS/JavaScript**: Frontend technologies
- **Bootstrap**: CSS framework for responsive design
- **jQuery**: JavaScript library for DOM manipulation
- **Web3.js**: Ethereum JavaScript API

### Storage
- **IPFS**: InterPlanetary File System for decentralized storage

## Database Schema

### User
- **id**: Integer (Primary Key)
- **username**: String (64 characters, unique)
- **email**: String (120 characters, unique)
- **password_hash**: String (256 characters)
- **ethereum_address**: String (42 characters, ETH address)
- **ipfs_profile_hash**: String (IPFS hash)
- **created_at**: DateTime
- **reputation**: Float (average rating from 1-5)
- Relationships:
  - **rides_offered**: One-to-many relationship with Ride
  - **bookings**: One-to-many relationship with Booking

### Ride
- **id**: Integer (Primary Key)
- **driver_id**: Integer (Foreign Key to User)
- **start_location**: String (128 characters)
- **end_location**: String (128 characters)
- **departure_time**: DateTime
- **price**: Float (in ETH)
- **available_seats**: Integer
- **created_at**: DateTime
- **smart_contract_id**: Integer (ride ID in the smart contract)
- **is_active**: Boolean
- Relationships:
  - **driver**: Many-to-one relationship with User
  - **bookings**: One-to-many relationship with Booking

### Booking
- **id**: Integer (Primary Key)
- **ride_id**: Integer (Foreign Key to Ride)
- **passenger_id**: Integer (Foreign Key to User)
- **status**: String (pending, confirmed, completed, cancelled)
- **created_at**: DateTime
- **transaction_hash**: String (Ethereum transaction hash)
- **seats_booked**: Integer
- Relationships:
  - **ride**: Many-to-one relationship with Ride
  - **passenger**: Many-to-one relationship with User

### Review
- **id**: Integer (Primary Key)
- **reviewer_id**: Integer (Foreign Key to User)
- **reviewee_id**: Integer (Foreign Key to User)
- **ride_id**: Integer (Foreign Key to Ride)
- **rating**: Integer (1-5 star rating)
- **comment**: Text
- **created_at**: DateTime
- Relationships:
  - **reviewer**: Many-to-one relationship with User
  - **reviewee**: Many-to-one relationship with User

## Smart Contract

The Carpool smart contract (`Carpool.sol`) is written in Solidity and manages the decentralized aspects of the carpooling system:

### Structs
- **Ride**: Stores information about a ride (driver, locations, price, seats, etc.)
- **Booking**: Stores information about a booking (passenger, ride, seats, payment)

### Functions
- **createRide**: Creates a new ride on the blockchain
- **bookRide**: Books a ride and sends payment to the driver
- **completeRide**: Marks a ride as completed
- **cancelRide**: Cancels a ride and handles refunds
- **getRide**: Gets ride details from the blockchain
- **getRideBookings**: Gets all bookings for a ride
- **getActiveRides**: Gets a list of active rides for UI display

### Events
- **RideCreated**: Emitted when a new ride is created
- **RideBooked**: Emitted when a ride is booked
- **RideCompleted**: Emitted when a ride is completed
- **RideCancelled**: Emitted when a ride is cancelled
- **BookingCancelled**: Emitted when a booking is cancelled

## API Reference

### Public Endpoints

#### User Authentication
- **POST /login**: User login
  - Params: username, password
  - Returns: Redirects to home page with session cookie

- **POST /register**: User registration
  - Params: username, email, password, confirm_password, ethereum_address
  - Returns: Redirects to home page with session cookie

- **GET /logout**: User logout
  - Returns: Redirects to home page

#### Ride Management
- **GET /**: Home page with latest rides
  - Returns: HTML page with ride listings

- **GET /search-ride**: Search for rides
  - Params: start_location, end_location, date
  - Returns: HTML page with search results

- **GET /ride/<ride_id>**: View ride details
  - Params: ride_id (URL parameter)
  - Returns: HTML page with ride details

- **POST /book-ride/<ride_id>**: Book a ride
  - Params: ride_id (URL parameter), seats
  - Returns: Redirects to ride details page

- **GET /offer-ride**: Form to offer a ride
  - Returns: HTML page with form

- **POST /offer-ride**: Create a new ride
  - Params: start_location, end_location, departure_time, price, available_seats
  - Returns: Redirects to home page

- **GET /profile**: User profile page
  - Returns: HTML page with user details and rides/bookings

### API Endpoints

- **GET /api/rides**: Get all active rides
  - Returns: JSON array of ride objects

- **GET /api/ride/<ride_id>**: Get ride details
  - Params: ride_id (URL parameter)
  - Returns: JSON object with ride details

## Installation and Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Node.js and npm (for Web3.js)
- Access to Ethereum network (local node, testnet, or mainnet)
- IPFS node or service (such as Infura)

### Environment Variables
- **DATABASE_URL**: PostgreSQL connection string
- **SESSION_SECRET**: Secret key for session management
- **ETHEREUM_NODE_URL**: URL of Ethereum node
- **CONTRACT_ADDRESS**: Address of the deployed Carpool contract
- **IPFS_API_URL**: URL of IPFS API
- **IPFS_GATEWAY**: URL of IPFS gateway
- **IPFS_API_KEY**: API key for IPFS service (optional)
- **IPFS_API_SECRET**: API secret for IPFS service (optional)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/decarpooling.git
   cd decarpooling
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   # Create PostgreSQL database
   createdb decarpooling
   
   # Set DATABASE_URL in environment or .env file
   export DATABASE_URL=postgresql://username:password@localhost/decarpooling
   ```

5. Initialize the database:
   ```
   # Database tables will be created automatically on first run
   python main.py
   ```

6. Compile and deploy the smart contract:
   ```
   # Install Solidity compiler and Web3 dependencies
   pip install py-solc-x web3
   
   # Compile the contract
   python smart-contracts/compile.py
   
   # Deploy the contract (requires Ethereum access)
   python smart-contracts/deploy.py
   
   # Set CONTRACT_ADDRESS in environment or .env file
   export CONTRACT_ADDRESS=0x...
   ```

7. Run the development server:
   ```
   python main.py
   ```

8. For production deployment, use Gunicorn:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## User Guide

### Registration and Profile Setup
1. Visit the DeCarpooling website and click "Register"
2. Fill in your details including:
   - Username
   - Email
   - Password
   - Ethereum wallet address (if you have one)
3. After registration, you can update your profile with additional information
4. Connect your Ethereum wallet using the "Connect Wallet" button

### Offering a Ride
1. Log in to your account
2. Click "Offer a Ride" in the navigation menu
3. Fill in the ride details:
   - Start location
   - End location
   - Departure time
   - Price per seat (in ETH)
   - Number of available seats
4. Submit the form
5. Confirm the transaction in your Ethereum wallet when prompted

### Finding and Booking a Ride
1. Log in to your account
2. Use the search form on the home page or the "Search Rides" page
3. Enter your desired:
   - Start location
   - End location
   - Date of travel
4. Browse the search results
5. Click on a ride to view details
6. Click "Book Ride" and specify the number of seats
7. Confirm the payment in your Ethereum wallet when prompted

### Managing Your Rides and Bookings
1. Log in to your account
2. Go to your Profile page
3. View your:
   - Offered rides
   - Booked rides
4. For rides you've offered:
   - View passenger details
   - Complete rides
   - Cancel rides (if no bookings)
5. For rides you've booked:
   - View ride details
   - Cancel bookings (subject to policies)

### Rating and Reviews
1. After a ride is completed, both driver and passenger can leave reviews
2. Go to your Profile page and find the completed ride
3. Click "Leave Review" and provide:
   - Rating (1-5 stars)
   - Written feedback (optional)
4. These reviews contribute to the user's reputation score

## Development Guide

### Project Structure
```
decarpooling/
├── app/
│   ├── __init__.py
│   ├── app.py              # Flask app initialization
│   ├── blockchain.py       # Blockchain integration service
│   ├── ipfs_storage.py     # IPFS storage service
│   ├── models.py           # Database models
│   ├── routes.py           # Application routes
│   ├── static/
│   │   ├── css/
│   │   │   └── custom.css  # Custom styles
│   │   ├── js/
│   │   │   ├── app.js           # Main application logic
│   │   │   └── web3_integration.js # Web3 integration
│   │   └── img/            # Image assets
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       ├── home.html       # Home page
│       ├── login.html      # Login page
│       ├── register.html   # Registration page
│       ├── profile.html    # User profile page
│       ├── offer_ride.html # Ride offering form
│       ├── search_ride.html # Ride search page
│       └── ride_details.html # Ride details page
├── smart-contracts/
│   ├── Carpool.sol              # Solidity smart contract
│   ├── compile.py               # Contract compilation script
│   ├── deploy.py                # Contract deployment script
│   └── carpool_contract.json    # Compiled contract ABI and address
├── main.py                # Main entry point
├── pyproject.toml         # Python project configuration
├── requirements.txt       # Python dependencies
└── .env.example           # Example environment variables
```

### Frontend Development
The frontend uses Bootstrap for styling and Web3.js for blockchain interaction:

1. **Templates**: Located in `app/templates/`
   - Base template with common elements
   - Page-specific templates extending the base

2. **Static Assets**: Located in `app/static/`
   - CSS: Custom styles in `custom.css`
   - JavaScript: Main application logic in `app.js`
   - Web3 Integration: Blockchain interactions in `web3_integration.js`

3. **Web3 Integration**:
   - Connecting user's wallet
   - Creating and signing transactions
   - Reading blockchain data

### Backend Development
The backend is built with Flask and uses SQL databases and blockchain services:

1. **Routes**: URL endpoints in `app/routes.py`
   - Each endpoint handles specific functionality
   - Authentication and authorization checks

2. **Models**: Database models in `app/models.py`
   - SQLAlchemy ORM for database interactions
   - User, Ride, Booking, and Review models

3. **Services**:
   - Blockchain service in `app/blockchain.py`
   - IPFS storage service in `app/ipfs_storage.py`

4. **Database Migrations**:
   - Database schema is automatically created from models
   - Manual migrations may be needed for major changes

### Smart Contract Development
The smart contract is written in Solidity:

1. **Contract File**: `smart-contracts/Carpool.sol`
   - Defines the contract structure and functions
   - Events for frontend interaction

2. **Compilation**: Using `smart-contracts/compile.py`
   - Compiles the contract to ABI and bytecode
   - Generates `carpool_contract.json`

3. **Deployment**: Using `smart-contracts/deploy.py`
   - Deploys the contract to the Ethereum network
   - Updates `carpool_contract.json` with the contract address

4. **Testing**: Manual testing via Remix or automated tests

## External Services

### Ethereum Network
The application connects to the Ethereum blockchain for ride management and payments:

1. **Development**:
   - Local Ethereum node like Ganache for testing
   - Test networks (Ropsten, Rinkeby, etc.) for staging

2. **Production**:
   - Ethereum mainnet for real transactions
   - Managed nodes via Infura or similar services

3. **Configuration**:
   - Set `ETHEREUM_NODE_URL` in environment variables
   - Set `CONTRACT_ADDRESS` after deployment

### IPFS
The application uses IPFS for decentralized storage of user profiles:

1. **Development**:
   - Local IPFS node for testing
   - Test IPFS networks for staging

2. **Production**:
   - IPFS pinning services like Infura or Pinata
   - Dedicated IPFS nodes

3. **Configuration**:
   - Set `IPFS_API_URL` in environment variables
   - Set `IPFS_GATEWAY` for accessing stored content
   - Set `IPFS_API_KEY` and `IPFS_API_SECRET` if using authenticated services

## Deployment Guide

### Local Deployment (Development)
1. Follow the installation steps in the Installation section
2. Use the built-in Flask development server:
   ```
   python main.py
   ```
3. Access the application at `http://localhost:5000`

### Server Deployment (Production)
1. Set up a server with Python 3.11 and PostgreSQL
2. Clone the repository and install dependencies
3. Set up environment variables in a `.env` file or server environment
4. Use Gunicorn as the WSGI server:
   ```
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```
5. Set up a reverse proxy with Nginx or Apache:
   ```nginx
   # Nginx example configuration
   server {
       listen 80;
       server_name decarpooling.example.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
6. Obtain an SSL certificate via Let's Encrypt or similar service

### Docker Deployment
1. Build the Docker image:
   ```
   docker build -t decarpooling .
   ```
2. Run the container:
   ```
   docker run -d --name decarpooling -p 5000:5000 \
       -e DATABASE_URL=postgresql://username:password@db/decarpooling \
       -e SESSION_SECRET=your_secret_key \
       -e ETHEREUM_NODE_URL=https://your-ethereum-node.com \
       -e CONTRACT_ADDRESS=0x... \
       decarpooling
   ```
3. Use Docker Compose for multi-container setup with PostgreSQL

## Future Enhancements

The DeCarpooling platform has several potential enhancements for future development:

### Technical Enhancements
- **Mobile Application**: Native mobile apps for iOS and Android
- **Smart Contract Upgrades**: More sophisticated payment handling and escrow
- **Multi-chain Support**: Integration with multiple blockchain networks
- **Layer 2 Scaling**: Integration with Layer 2 solutions for lower gas fees
- **Advanced IPFS Integration**: More comprehensive decentralized data storage

### Feature Enhancements
- **DAO Governance**: Decentralized governance of the platform
- **Token Economics**: Platform-specific token for discounts and rewards
- **Advanced Matching Algorithm**: Better matching of drivers and passengers
- **Social Features**: Chat, groups, and social connections
- **Route Optimization**: Suggested routes and pickup points
- **Carbon Offset**: Tracking and offsetting carbon emissions
- **Insurance Integration**: Decentralized insurance for rides
- **Multi-leg Journeys**: Support for journeys with multiple segments

### Business Enhancements
- **Subscription Model**: Subscription tiers for regular users
- **Enterprise Accounts**: Features for business users
- **API Access**: Public API for third-party integration
- **Affiliate Program**: Rewards for referring new users
- **Advertising Platform**: Targeted advertising for relevant services
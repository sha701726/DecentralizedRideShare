# DeCarpooling - Decentralized Carpooling Platform

DeCarpooling is a web application that uses blockchain technology to create a secure and transparent platform for carpooling. It allows users to offer rides, book rides, and make payments using cryptocurrency.

## Table of Contents
1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Key Components](#key-components)
4. [Security Features](#security-features)
5. [Development Mode](#development-mode)
6. [Setup Instructions](#setup-instructions)

## Features

- **User Authentication**: Register, login, and manage your profile
- **Two-Factor Authentication**: Enhanced security with OTP verification
- **Offer Rides**: Drivers can offer rides with details (start/end location, price, seats)
- **Search Rides**: Passengers can search for available rides
- **Book Rides**: Secure booking process using smart contracts
- **Blockchain Integration**: Rides are stored on the Ethereum blockchain for transparency
- **IPFS Storage**: User profiles are stored on IPFS for decentralized data storage
- **Payment Processing**: Built-in cryptocurrency transactions

## Project Structure

The application follows a standard Flask web application structure:

- **Main App Files**:
  - `main.py`: Entry point for the application
  - `app.py`: Flask application setup and configuration
  - `config.py`: Configuration settings for different environments
  - `models.py`: Database models (User, Ride, Booking, Review)
  - `routes.py`: Web routes and controllers

- **Templates & Static Files**:
  - `templates/`: HTML templates using Jinja2
  - `static/`: CSS, JavaScript, and other static assets

- **Blockchain & IPFS Integration**:
  - `blockchain_service.py`: Service for interacting with Ethereum blockchain
  - `ipfs_service.py`: Service for storing and retrieving data from IPFS
  - `smart_contracts/`: Ethereum smart contracts

## Key Components

### 1. Database Models

The application uses several key database models:

- **User**: Stores user information including username, email, password hash, Ethereum address, and OTP settings for two-factor authentication.

- **Ride**: Represents a carpooling offer with details about the start/end locations, price, available seats, and connection to the blockchain.

- **Booking**: Records when a user books a ride, including transaction details and status.

- **Review**: Allows users to leave ratings and reviews for drivers or passengers after a ride.

### 2. Web Routes

The main routes in the application include:

- **Authentication**: `/login`, `/register`, `/logout`
- **Ride Management**: `/offer-ride`, `/search-ride`, `/ride/<id>`, `/book-ride/<id>`, `/complete-ride/<id>`
- **Profile Management**: `/profile`, `/update-profile`, `/setup-otp`, `/disable-otp`
- **API Endpoints**: `/api/rides`, `/api/ride/<id>`, `/api/blockchain/rides`

### 3. Blockchain Integration

The app uses Ethereum blockchain to:

- Record ride offers with smart contracts
- Process booking payments securely
- Track the status of rides (active, completed)

The `BlockchainService` class in `blockchain_service.py` handles all interactions with the Ethereum network, including creating rides, booking rides, and retrieving ride information.

### 4. IPFS Storage

User profile data is stored on IPFS (InterPlanetary File System), a decentralized storage network. This provides:

- Permanent, decentralized storage of user information
- Verified user profiles that can't be easily tampered with

The `IPFSStorage` class in `ipfs_service.py` manages uploading and retrieving data from IPFS.

## Security Features

### Two-Factor Authentication

The application includes Two-Factor Authentication (2FA) using time-based one-time passwords (TOTP):

- Users can enable 2FA from their profile page
- A QR code is provided to scan with authenticator apps (like Google Authenticator)
- Once enabled, login requires both password and a verification code

Implementation details:
- Uses the `pyotp` library to generate and verify codes
- OTP settings are stored in the User model (`otp_secret`, `otp_enabled`, `otp_verified`)
- Login process detects if 2FA is enabled and prompts for verification code

## Development Mode

The application includes a development mode that allows testing without actual blockchain or IPFS connections:

- Set `DEV_MODE=true` in the `.env` file to enable
- Blockchain transactions are simulated locally
- IPFS storage is replaced with local file storage

This makes development and testing easier without requiring actual cryptocurrency or external services.

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- For production: Ethereum wallet and Infura account

### Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

### Configuration

1. Copy `.env.example` to `.env`
2. Update the values in `.env`:
   - Set `SESSION_SECRET` for secure cookies
   - Configure database connection in `DATABASE_URL`
   - For development, set `DEV_MODE=true`
   - For production, add Ethereum and IPFS credentials

### Database Setup

1. Create a PostgreSQL database
2. Run the database migration: `python db_migrate_otp.py`

### Running the Application

- Development server: `flask run`
- Production server: `gunicorn --bind 0.0.0.0:5000 main:app`

Visit `http://localhost:5000` in your browser to access the application.

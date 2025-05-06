import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev_secret_key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///carpool.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ethereum node configuration
    ETHEREUM_NODE_URL = os.environ.get("ETHEREUM_NODE_URL", "https://sepolia.infura.io/v3/")
    ETHEREUM_NETWORK_ID = os.environ.get("ETHEREUM_NETWORK_ID", "11155111")  # Sepolia testnet
    
    # IPFS configuration
    IPFS_API_URL = os.environ.get("IPFS_API_URL", "https://ipfs.infura.io:5001/api/v0")
    IPFS_GATEWAY = os.environ.get("IPFS_GATEWAY", "https://ipfs.io/ipfs/")
    IPFS_API_KEY = os.environ.get("IPFS_API_KEY", "")
    IPFS_API_SECRET = os.environ.get("IPFS_API_SECRET", "")
    
    # Smart contract configuration
    CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "")
    
    # Infura project ID (needed for both Ethereum and IPFS)
    INFURA_PROJECT_ID = os.environ.get("INFURA_PROJECT_ID", "")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///carpool_dev.db")

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    
    # More secure configuration for production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

# Load the appropriate configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the appropriate configuration based on environment"""
    env = os.environ.get("FLASK_ENV", "development")
    return config.get(env, config['default'])

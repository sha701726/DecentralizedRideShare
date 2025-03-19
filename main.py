"""
Main entry point for the DeCarpooling application
This script sets up and runs the Flask application
"""

import os
import logging
from app.app import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the application"""
    logger.info("Starting DeCarpooling application")
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Print the URL where the app will be served
    logger.info(f"Application will be available at http://localhost:{port}")
    
    # Run the Flask application
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    main()

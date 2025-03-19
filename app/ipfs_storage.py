import os
import io
import json
import logging
import requests
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class IPFSStorage:
    """Service for storing files on IPFS"""
    
    def __init__(self):
        """Initialize IPFS connection"""
        # Use Infura's IPFS API for simplicity
        self.ipfs_api = os.environ.get('IPFS_API_URL', 'https://ipfs.infura.io:5001/api/v0')
        self.ipfs_gateway = os.environ.get('IPFS_GATEWAY', 'https://ipfs.io/ipfs/')
        self.ipfs_api_key = os.environ.get('IPFS_API_KEY', '')
        self.ipfs_api_secret = os.environ.get('IPFS_API_SECRET', '')
        
        # Test connection
        try:
            response = requests.get(f"{self.ipfs_api}/version")
            if response.status_code == 200:
                logger.info("Connected to IPFS node")
            else:
                logger.warning(f"IPFS connection test failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to IPFS: {str(e)}")
    
    def add_file(self, file_data, filename=None):
        """
        Upload a file to IPFS
        
        Args:
            file_data: The file data (bytes or file-like object)
            filename: Optional filename
            
        Returns:
            IPFS hash of the uploaded file
        """
        try:
            if filename:
                filename = secure_filename(filename)
            
            # Create a multipart form
            files = {
                'file': (filename, file_data) if filename else file_data
            }
            
            # Add authentication if provided
            auth = None
            if self.ipfs_api_key and self.ipfs_api_secret:
                auth = (self.ipfs_api_key, self.ipfs_api_secret)
            
            # Upload to IPFS
            response = requests.post(
                f"{self.ipfs_api}/add", 
                files=files,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result['Hash']
                logger.info(f"File uploaded to IPFS with hash: {ipfs_hash}")
                return ipfs_hash
            else:
                logger.error(f"IPFS upload failed: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading to IPFS: {str(e)}")
            return None
    
    def add_json(self, json_data):
        """
        Upload JSON data to IPFS
        
        Args:
            json_data: Dictionary to be uploaded as JSON
            
        Returns:
            IPFS hash of the uploaded JSON
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(json_data)
            
            # Upload as file
            return self.add_file(io.BytesIO(json_str.encode('utf-8')), 'data.json')
            
        except Exception as e:
            logger.error(f"Error uploading JSON to IPFS: {str(e)}")
            return None
    
    def get_file(self, ipfs_hash):
        """
        Get a file from IPFS
        
        Args:
            ipfs_hash: IPFS hash of the file
            
        Returns:
            File content as bytes
        """
        try:
            # Get file from IPFS gateway
            response = requests.get(f"{self.ipfs_gateway}{ipfs_hash}")
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Error getting file from IPFS: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading from IPFS: {str(e)}")
            return None
    
    def get_json(self, ipfs_hash):
        """
        Get JSON data from IPFS
        
        Args:
            ipfs_hash: IPFS hash of the JSON file
            
        Returns:
            Parsed JSON data as dictionary
        """
        try:
            # Get file content
            content = self.get_file(ipfs_hash)
            
            if content:
                # Parse JSON
                return json.loads(content.decode('utf-8'))
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting JSON from IPFS: {str(e)}")
            return None

# Create a singleton instance
ipfs_storage = IPFSStorage()

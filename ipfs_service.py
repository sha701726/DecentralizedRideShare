import os
import io
import json
import logging
import requests
import base64
import uuid
from werkzeug.utils import secure_filename
from config import get_config
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class IPFSStorage:
    """Service for storing files on IPFS"""
    
    def __init__(self):
        """Initialize IPFS connection"""
        # Get configuration
        config = get_config()
        
        # Check if we should use real IPFS or dev mode
        self.dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
        
        # Use Infura's IPFS API by default
        self.ipfs_api = config.IPFS_API_URL
        self.ipfs_gateway = config.IPFS_GATEWAY
        self.ipfs_api_key = config.IPFS_API_KEY
        self.ipfs_api_secret = config.IPFS_API_SECRET
        self.project_id = config.INFURA_PROJECT_ID
        
        # Local storage for dev mode
        self.storage = {}
        
        if self.dev_mode:
            logger.info("Running in development mode, IPFS operations will be simulated")
            return
            
        # Test connection
        try:
            # If API key credentials are not provided, switch to dev mode
            if not self.project_id and not (self.ipfs_api_key and self.ipfs_api_secret):
                logger.warning("No IPFS credentials provided, running in development mode")
                self.dev_mode = True
                return
                
            headers = {}
            # Setup authentication - either using project ID or API key
            if self.project_id:
                auth = (self.project_id, "")
                headers = {
                    "Authorization": f"Basic {self._get_basic_auth_header(self.project_id, '')}"
                }
            elif self.ipfs_api_key and self.ipfs_api_secret:
                auth = (self.ipfs_api_key, self.ipfs_api_secret)
            else:
                auth = None
                
            response = requests.get(f"{self.ipfs_api}/version", headers=headers, auth=auth)
            if response.status_code == 200:
                logger.info("Connected to IPFS node successfully")
            else:
                logger.warning(f"IPFS connection test failed: {response.status_code}")
                logger.warning("Running in development mode due to connection failure")
                self.dev_mode = True
        except Exception as e:
            logger.error(f"Error connecting to IPFS: {str(e)}")
            logger.warning("Running in development mode due to connection error")
            self.dev_mode = True
    
    def _get_basic_auth_header(self, username, password):
        """Create basic auth header string"""
        import base64
        auth_string = f"{username}:{password}"
        return base64.b64encode(auth_string.encode()).decode()
    
    def add_file(self, file_data, filename=None):
        """
        Upload a file to IPFS
        
        Args:
            file_data: The file data (bytes or file-like object)
            filename: Optional filename
            
        Returns:
            IPFS hash of the uploaded file
        """
        # Use dev mode implementation if in dev mode
        if self.dev_mode:
            try:
                # Generate a unique hash
                hash_key = f"dev-ipfs-{uuid.uuid4().hex[:16]}"
                
                # Store the file data
                if hasattr(file_data, 'read'):
                    content = file_data.read()
                    file_data.seek(0)  # Reset file pointer
                else:
                    content = file_data
                    
                # Store in our local dictionary
                self.storage[hash_key] = content
                logger.info(f"Dev mode: File stored with mock hash: {hash_key}")
                return hash_key
            except Exception as e:
                logger.error(f"Dev mode error: {str(e)}")
                return None
                
        # Use real IPFS implementation
        try:
            if filename:
                filename = secure_filename(filename)
            
            # Create a multipart form
            files = {
                'file': (filename, file_data) if filename else file_data
            }
            
            # Add authentication
            headers = {}
            if self.project_id:
                headers = {
                    "Authorization": f"Basic {self._get_basic_auth_header(self.project_id, '')}"
                }
                auth = None
            elif self.ipfs_api_key and self.ipfs_api_secret:
                auth = (self.ipfs_api_key, self.ipfs_api_secret)
            else:
                auth = None
            
            # Upload to IPFS
            response = requests.post(
                f"{self.ipfs_api}/add", 
                files=files,
                auth=auth,
                headers=headers
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
        # Use dev mode implementation if in dev mode
        if self.dev_mode:
            try:
                # Check if hash exists in our local storage
                if ipfs_hash in self.storage:
                    logger.info(f"Dev mode: Retrieved file with hash: {ipfs_hash}")
                    return self.storage[ipfs_hash]
                else:
                    # If not in our storage, generate dummy content for dev purposes
                    logger.warning(f"Dev mode: Hash {ipfs_hash} not found, returning dummy content")
                    dummy_content = {
                        "message": "This is a placeholder response in development mode",
                        "hash": ipfs_hash
                    }
                    return json.dumps(dummy_content).encode('utf-8')
            except Exception as e:
                logger.error(f"Dev mode error: {str(e)}")
                return None
                
        # Use real IPFS implementation
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

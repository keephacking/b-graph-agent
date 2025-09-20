"""
Configuration settings for API Chat Bot Application
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for the application"""
    
    def __init__(self):
        # API Configuration
        self.api_url: str = self._get_required_env("API_URL")
        self.temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
        self.top_k: float = float(os.getenv("TOP_K", "0.1"))
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "2048"))
        
        # Directory Configuration
        self.output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
        self.template_dir: Path = Path(os.getenv("HTML_TEMPLATE_DIR", "templates"))
        
        # Application Settings
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.verbose: bool = os.getenv("VERBOSE", "true").lower() == "true"
        
        # Ensure directories exist
        try:
            self.output_dir.mkdir(exist_ok=True)
            self.template_dir.mkdir(exist_ok=True)
        except (OSError, PermissionError) as e:
            if self.verbose:
                print(f"⚠️ Warning: Could not create directories: {e}")
            # Continue execution - directories will be created on demand
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not found. Please check your .env file.")
        return value
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        try:
            # Check if API URL is set
            if not self.api_url or self.api_url == "your_api_url_here":
                raise ValueError("Please set a valid API_URL in your .env file")
            
            # Validate numeric values
            if self.temperature < 0 or self.temperature > 2:
                raise ValueError("Temperature must be between 0 and 2")
            
            if self.top_k < 0 or self.top_k > 1:
                raise ValueError("Top K must be between 0 and 1")
            
            if self.max_tokens < 1:
                raise ValueError("Max tokens must be positive")
            
            return True
            
        except ValueError as e:
            if self.verbose:
                print(f"❌ Configuration error: {e}")
            return False


# Global configuration instance - initialized lazily
_config_instance = None

def get_config() -> Config:
    """Get the global configuration instance (lazy initialization)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# For backward compatibility - but don't initialize at import time
def config():
    return get_config()

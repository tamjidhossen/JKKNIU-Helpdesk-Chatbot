"""
API Key Rotation Manager
========================

Rotates through multiple Google API keys to avoid rate limits.
Reads GOOGLE_API_KEY as a JSON array from .env file.

Usage:
    from api_keys import get_next_api_key, create_model_with_rotation
    
    # Get next API key
    api_key = get_next_api_key()
    
    # Or create a model directly
    model = create_model_with_rotation()
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Parse API keys from environment
_api_keys_raw = os.getenv("GOOGLE_API_KEY", "")
_api_keys = []
_current_key_index = 0

def _parse_api_keys():
    """Parse API keys from environment variable."""
    global _api_keys
    
    raw = os.getenv("GOOGLE_API_KEY", "")
    
    if not raw:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    # Try parsing as JSON array
    if raw.startswith("["):
        try:
            _api_keys = json.loads(raw)
            if isinstance(_api_keys, list) and len(_api_keys) > 0:
                print(f"✓ Loaded {len(_api_keys)} API keys for rotation")
                return
        except json.JSONDecodeError:
            pass
    
    # Fallback: treat as single key
    _api_keys = [raw]
    print("✓ Using single API key (no rotation)")

# Parse on module load
try:
    _parse_api_keys()
except Exception as e:
    print(f"Warning: Could not parse API keys: {e}")
    _api_keys = []


def get_next_api_key() -> str:
    """Get the next API key in rotation."""
    global _current_key_index
    
    if not _api_keys:
        raise ValueError("No API keys available")
    
    key = _api_keys[_current_key_index]
    _current_key_index = (_current_key_index + 1) % len(_api_keys)
    return key


def get_current_key_index() -> int:
    """Get the current key index (for debugging)."""
    return _current_key_index


def get_total_keys() -> int:
    """Get total number of API keys."""
    return len(_api_keys)


def create_model_with_rotation(model_name: Optional[str] = None):
    """Create a ChatGoogleGenerativeAI model with the next API key."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from config import GEMINI_MODEL
    
    api_key = get_next_api_key()
    model = model_name or GEMINI_MODEL
    
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key
    )


def create_embeddings_with_rotation(model_name: Optional[str] = None):
    """Create GoogleGenerativeAIEmbeddings with the next API key."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from config import GOOGLE_EMBEDDING_MODEL
    
    api_key = get_next_api_key()
    model = model_name or GOOGLE_EMBEDDING_MODEL
    
    return GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=api_key
    )

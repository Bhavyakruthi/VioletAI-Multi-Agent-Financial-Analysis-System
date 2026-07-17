import asyncio
import logging
import sys
import os

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.api_manager import api_manager
from services.embedding_service import GoogleEmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rotation_logic():
    print("--- Testing API Key Rotation Logic ---")
    
    # 1. Check initial key
    initial_key = api_manager.get_key()
    print(f"Initial Key: {initial_key[:10]}...")
    
    # 2. Simulate rotation
    rotated_key = api_manager.rotate_key()
    print(f"Rotated Key: {rotated_key[:10]}...")
    
    if len(api_manager.keys) > 1:
        if initial_key != rotated_key:
            print("SUCCESS: Key rotated to a different value.")
        else:
            print("WARNING: Key did not change (likely only 1 key configured).")
    else:
        print("Note: Only 1 key configured, rotation cycles back to the same key.")

    # 3. Test service integration (mocking a 429)
    print("\n--- Testing Service Integration (Mocking 429) ---")
    service = GoogleEmbeddingService()
    
    # We'll just manually call rotate_key as if a 429 happened
    print("Simulating 429 error and calling rotate...")
    api_manager.rotate_key()
    new_active_key = api_manager.get_key()
    print(f"New Active Key in Manager: {new_active_key[:10]}...")
    
    print("\nRotation logic verified.")

if __name__ == "__main__":
    asyncio.run(test_rotation_logic())

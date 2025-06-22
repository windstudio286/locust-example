# shared_state_manager.py (using Redis)
import redis
import os
# Install redis-py: pip install redis
# Configure your Redis connection
# Replace with your Redis server's IP and port
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

# Key for our boolean flag
FLAG_KEY = "test_active_flag"

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
            _redis_client.ping() # Test connection
            print(f"[{os.getpid()}] Connected to Redis: {REDIS_HOST}:{REDIS_PORT}")
        except redis.exceptions.ConnectionError as e:
            print(f"[{os.getpid()}] Could not connect to Redis: {e}")
            _redis_client = None # Reset to prevent further attempts with broken client
            raise e # Re-raise to indicate connection failure
    return _redis_client

def write_flag(value: bool):
    """Writes the boolean value to Redis."""
    client = get_redis_client()
    if client:
        try:
            client.set(FLAG_KEY, str(value))
            print(f"[{os.getpid()}] Flag written to Redis: {value}")
        except Exception as e:
            print(f"[{os.getpid()}] Error writing flag to Redis: {e}")

def read_flag() -> bool:
    """Reads the boolean value from Redis."""
    client = get_redis_client()
    if client:
        try:
            content = client.get(FLAG_KEY)
            if content is None:
                # If key doesn't exist, initialize it and return default
                write_flag(False)
                return False
            return content.lower() == "true"
        except Exception as e:
            print(f"[{os.getpid()}] Error reading flag from Redis: {e}")
            return False # Default to False on error
    return False # Default to False if no Redis client

def initialize_flag(initial_value: bool = False):
    """Initializes the flag in Redis if it doesn't exist."""
    client = get_redis_client()
    if client:
        try:
            if not client.exists(FLAG_KEY):
                write_flag(initial_value)
                print(f"[{os.getpid()}] Initialized Redis flag with: {initial_value}")
        except Exception as e:
            print(f"[{os.getpid()}] Error initializing Redis flag: {e}")

# Example cleanup function (optional)
def cleanup_flag():
    client = get_redis_client()
    if client:
        try:
            client.delete(FLAG_KEY)
            print(f"[{os.getpid()}] Cleaned up Redis flag: {FLAG_KEY}")
        except Exception as e:
            print(f"[{os.getpid()}] Error cleaning up Redis flag: {e}")
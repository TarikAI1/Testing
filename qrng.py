# qrng.py
import requests
import random
import secrets # Cryptographically strong PRNG for fallback

ANU_API_URL = "https://qrng.anu.edu.au/API/jsonI.php"

def get_quantum_random_bytes(length):
    """
    Fetches random bytes from the ANU QRNG API.
    Returns bytes or None if fetching fails.
    """
    try:
        # ANU API returns uint16 (2 bytes each), so request length/2
        # Max block size is 1024 for uint16
        num_uint16 = (length + 1) // 2 # Round up
        if num_uint16 > 1024:
             print("Warning: Requesting large amount of QRNG data, multiple API calls would be needed (not implemented here for simplicity). Requesting max 1024.")
             num_uint16 = 1024 # Request max for this example

        params = {
            'length': num_uint16,
            'type': 'uint16',
            'size': 1 # Block size - keep small for this usage
        }
        response = requests.get(ANU_API_URL, params=params, timeout=10) # 10 second timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        if data.get("success"):
            random_uint16s = data.get("data", [])
            byte_list = []
            for num in random_uint16s:
                # Convert uint16 to 2 bytes (big-endian)
                byte_list.extend(num.to_bytes(2, byteorder='big'))

            # Truncate to the exact length requested
            return bytes(byte_list[:length])
        else:
            print(f"ANU QRNG API reported failure: {data.get('message', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching quantum random numbers: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during QRNG fetch: {e}")
        return None

def get_random_bytes(length):
    """
    Tries to get quantum random bytes, falls back to cryptographically secure PRNG.
    """
    print("Attempting to fetch quantum random numbers...")
    q_bytes = get_quantum_random_bytes(length)
    if q_bytes:
        print("Successfully fetched quantum random numbers.")
        return q_bytes
    else:
        print("Falling back to secure pseudo-random number generator.")
        return secrets.token_bytes(length)

# Example usage (optional - for testing)
if __name__ == "__main__":
    test_bytes = get_random_bytes(16)
    if test_bytes:
        print(f"Generated {len(test_bytes)} bytes: {test_bytes.hex()}")
    else:
        print("Failed to generate random bytes.")
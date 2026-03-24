# broker/replication.py
import requests
import time

# How many seconds to wait before retrying an unhealthy follower.
REPLICATION_RETRY_SECONDS = 15

# A dictionary to track unhealthy followers and the last time they failed.
# Format: { 'follower_address': last_failure_timestamp }
unhealthy_followers = {}

def replicate_to_follower(follower_address, message):
    """
    Sends a message to a follower for replication.
    If a follower failed recently, it temporarily skips attempts to avoid log spam.
    It will automatically retry after REPLICATION_RETRY_SECONDS.
    """
    # Check if the follower is in the unhealthy dictionary.
    if follower_address in unhealthy_followers:
        last_failure_time = unhealthy_followers[follower_address]
        
        # If it failed less than our retry period ago, skip it.
        if time.time() - last_failure_time < REPLICATION_RETRY_SECONDS:
            return False
        else:
            # The retry period has passed, so remove it from the dict and try again.
            print(f"\n--- Retrying Unhealthy Follower ---")
            print(f"Attempting to replicate to {follower_address} again after timeout.")
            print(f"---------------------------------\n")
            unhealthy_followers.pop(follower_address)

    url = f"{follower_address}/internal/replicate"
    try:
        response = requests.post(url, json=message, timeout=2)
        response.raise_for_status()

        # If a request succeeds, we definitely know the follower is healthy.
        # This handles the case where it was marked unhealthy but came back online.
        if follower_address in unhealthy_followers:
            unhealthy_followers.pop(follower_address)
        
        print(f"Successfully replicated to {follower_address}")
        return True

    except requests.exceptions.RequestException as e:
        # On the VERY FIRST failure (or first after a retry), print a detailed error.
        if follower_address not in unhealthy_followers:
            print(f"\n--- Follower Unreachable ---")
            print(f"Failed to replicate to {follower_address}. Marking as unhealthy for {REPLICATION_RETRY_SECONDS}s.")
            print(f"Error: {e}")
            print(f"--------------------------\n")
        
        # Mark the follower as unhealthy with the current timestamp.
        unhealthy_followers[follower_address] = time.time()
        return False
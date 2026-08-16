# broker/state_manager.py
import redis
import time
import threading
from . import config

class StateManager:
    """
    Manages the broker's state (leader/follower) and handles leader election.
    """
    def __init__(self, broker_address, peer_brokers):
        self.broker_address = broker_address
        self.peer_brokers = peer_brokers
        self.role = "follower"  # Start as a follower
        self.leader_address = None
        self.redis_client = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
        self.stop_thread = threading.Event()

    def start(self):
        """Starts the background thread for managing state."""
        self.redis_client.setnx(config.HWM_KEY, 0)
        
        thread = threading.Thread(target=self._manage_state_loop)
        thread.daemon = True
        thread.start()

    def stop(self):
        """Stops the background thread."""
        self.stop_thread.set()

    def _manage_state_loop(self):
        """The main loop for leader election and lease renewal."""
        while not self.stop_thread.is_set():
            if self.role == "leader":
                # If I am the leader, I must renew my lease
                self._renew_lease()
                time.sleep(config.LEASE_TIMEOUT_SECONDS / 2)
            else:
                # If I am a follower, I must watch for lease expiration
                self._try_to_become_leader()
                time.sleep(1) # Check every second

    def _renew_lease(self):
        """Renew the leader lease only if we still own it."""

        renew_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call(
                "SET",
                KEYS[1],
                ARGV[1],
                "EX",
                ARGV[2]
            )
        else
            return nil
        end
        """

        result = self.redis_client.eval(
            renew_script,
            1,
            config.LEADER_LEASE_KEY,
            self.broker_address,
            config.LEASE_TIMEOUT_SECONDS
        )

        if result:
            print(f"[{self.broker_address}] Leader lease renewed.")
        else:
            # We no longer own the lease.
            print(
                f"[{self.broker_address}] "
                "Lease renewal failed! Demoting to follower."
            )

            self.role = "follower"
            self.leader_address = self.redis_client.get(
                config.LEADER_LEASE_KEY
            )


    def _try_to_become_leader(self):
        """Attempt to acquire the leader lease if it's available."""
        if self.redis_client.set(config.LEADER_LEASE_KEY, self.broker_address, nx=True, ex=config.LEASE_TIMEOUT_SECONDS):
            self._promote_to_leader()
        else:
            self.leader_address = self.redis_client.get(config.LEADER_LEASE_KEY)

    def _promote_to_leader(self):
        """Promote this broker to the leader role."""
        print("\n" + "="*60)
        print(f"!!!!!!!!!!!!!! [{self.broker_address}] Promoting to LEADER !!!!!!!!!!!!!!")
        print("="*60 + "\n")
        self.role = "leader"
        self.leader_address = self.broker_address

    def get_hwm(self):
        """Get the High Water Mark from Redis."""
        return int(self.redis_client.get(config.HWM_KEY) or 0)

    def update_hwm(self, offset):
        """Update the High Water Mark in Redis."""
        self.redis_client.set(config.HWM_KEY, offset)

    def get_leader(self):
        """Get the current leader address from Redis."""
        return self.redis_client.get(config.LEADER_LEASE_KEY)

    def is_leader(self):
        return self.role == "leader"

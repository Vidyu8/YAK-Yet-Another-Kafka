# broker/config.py

# Configuration for the Redis metadata store
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Redis Keys
LEADER_LEASE_KEY = "yak:leader_lease"  # The key holding the address of the current leader
HWM_KEY = "yak:hwm"                    # The key holding the High Water Mark offset

# Lease configuration
LEASE_TIMEOUT_SECONDS = 10  # How long the leader lease is valid for

# client/client_logic.py
import requests
import time

class ClientLogic:
    def __init__(self, broker_list):
        self.broker_list = broker_list
        self.leader = None
        self.find_leader()

    def find_leader(self):
        """Queries brokers to find the current leader."""
        print("Attempting to find the leader...")
        for broker in self.broker_list:
            try:
                url = f"{broker}/metadata/leader"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    self.leader = response.json()['leader']
                    print(f"Leader found: {self.leader}")
                    return self.leader
            except requests.exceptions.RequestException:
                print(f"Could not connect to {broker}")
        
        # We only print this if the loop finishes without finding a leader
        print("Could not find a leader from any known broker.")
        return None

    def resilient_request(self, method, endpoint, **kwargs):
        """
        A wrapper around requests that handles failover with a patient backoff mechanism.
        """
        if not self.leader:
            self.find_leader()
            if not self.leader:
                raise Exception("Cannot operate without a leader.")

        url = f"{self.leader}{endpoint}"
        
        while True:
            try:
                response = requests.request(method, url, **kwargs)

                if response.status_code == 421:
                    print("Misdirected request. Server is not the leader.")
                    self.leader = response.json().get('leader')
                    if not self.leader:
                        self.find_leader()
                    
                    print(f"New leader is {self.leader}. Retrying...")
                    url = f"{self.leader}{endpoint}"
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                # ===================== THIS IS THE UPDATED SECTION =====================
                failed_leader = self.leader
                print(f"\nRequest to leader {failed_leader} failed: {e}. Assuming leader is down.\n")
                
                # Reset leader and start a more patient discovery loop
                self.leader = None
                while self.leader is None:
                    time.sleep(2) # Wait before starting discovery to let system settle
                    self.find_leader() # Tries to find a new leader
                    
                    # If discovery returns the same dead leader, the lease hasn't expired.
                    # We must wait patiently instead of spamming requests.
                    if self.leader == failed_leader:
                        print(f"Leader {self.leader} is still registered but unresponsive. Waiting for failover...")
                        self.leader = None # Force the discovery loop to continue
                    
                print(f"Discovered new leader: {self.leader}. Retrying request.")
                url = f"{self.leader}{endpoint}"
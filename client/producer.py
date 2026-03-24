# client/producer.py
import time
from .client_logic import ClientLogic

BROKERS = ["http://localhost:5001", "http://localhost:5002"]

def run_producer():
    client = ClientLogic(BROKERS)
    msg_count = 1
    
    print("Producer started. Sending messages every 2 seconds...")
    print("Press Ctrl+C to stop.")

    while True:
        try:
            message = {"payload": f"This is message number {msg_count}"}
            
            response = client.resilient_request('post', '/produce', json=message)
            
            if response.status_code == 200:
                offset = response.json().get('offset')
                print(f"Successfully sent message {msg_count}. Offset: {offset}")
                msg_count += 1
            else:
                print(f"Failed to send message. Status: {response.status_code}")
            
            time.sleep(2)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nProducer shutting down.")
            break

if __name__ == "__main__":
    run_producer()
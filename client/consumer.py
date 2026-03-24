# client/consumer.py
import time
from .client_logic import ClientLogic

BROKERS = ["http://localhost:5001", "http://localhost:5002"]

def run_consumer():
    client = ClientLogic(BROKERS)
    # The consumer is responsible for tracking its own offset
    current_offset = 1 
    
    print("Consumer started. Polling for messages every 3 seconds...")
    print("Press Ctrl+C to stop.")

    while True:
        try:
            params = {'offset': current_offset}
            response = client.resilient_request('get', '/consume', params=params)

            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                if messages:
                    for msg in messages:
                        print(f"Consumed message at offset {current_offset}: {msg['payload']}")
                        current_offset += 1
                else:
                    print("No new messages.")
            
            time.sleep(3)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nConsumer shutting down.")
            break

if __name__ == "__main__":
    run_consumer()
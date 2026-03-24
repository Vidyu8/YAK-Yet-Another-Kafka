# broker/main.py
import sys
from broker.app import initialize_app

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python -m broker.main <broker_id> <host:port> <peer_host:port>")
        sys.exit(1)

    broker_id = sys.argv[1]
    my_address = f"http://{sys.argv[2]}"
    peer_address = f"http://{sys.argv[3]}"
    
    host, port = sys.argv[2].split(':')

    print(f"Starting Broker {broker_id} at {my_address}")
    print(f"Peer address: {peer_address}")

    peer_brokers = [peer_address]

    app = initialize_app(broker_id, my_address, peer_brokers)
    app.run(host=host, port=int(port), debug=False)
# broker/app.py
from flask import Flask, request, jsonify
from .log_manager import LogManager
from .state_manager import StateManager
from .replication import replicate_to_follower
# This version contains the follower endpoints only.
state_manager = None
log_manager = None
app = Flask(__name__)

def initialize_app(broker_id, broker_address, peer_brokers):
    """Initializes the global state for the Flask app."""
    global state_manager, log_manager
    log_manager = LogManager(broker_id)
    state_manager = StateManager(broker_address, peer_brokers)
    state_manager.start()
    return app

@app.route('/produce', methods=['POST'])
def produce():
    if not state_manager.is_leader():
        leader_address = state_manager.get_leader()
        # Return 421 Misdirected Request, pointing to the correct leader
        return jsonify({"error": "Not the leader", "leader": leader_address}), 421

    message = request.get_json()
    if not message or 'payload' not in message:
        return jsonify({"error": "Invalid message format"}), 400

    # 1. Leader writes to its own log
    offset = log_manager.write_message(message)
    print(f"[Leader] Wrote message to local log at offset {offset}")

    # ===================== THIS IS THE UPDATED SECTION =====================
    # 2. Replicate to all followers (in this case, one)
    follower_address = state_manager.peer_brokers[0] # Assuming one follower
    replication_successful = replicate_to_follower(follower_address, message)

    if not replication_successful:
        # This is the key change: Log a warning that we can't replicate, 
        # but DON'T fail the request. This allows the new leader to operate
        # alone after the old leader has died.
        print(f"[Leader] WARNING: Failed to replicate to follower {follower_address}. "
              "Proceeding without replication as cluster is degraded.")

    # 3. Update the High Water Mark and return success.
    # In a degraded state, the HWM simply reflects the leader's own log.
    state_manager.update_hwm(offset)
    print(f"[Leader] Updated HWM to {offset}")
    return jsonify({"status": "success", "offset": offset}), 200
    # ===================== END OF UPDATED SECTION ==========================

@app.route('/internal/replicate', methods=['POST'])
def internal_replicate():
    if state_manager.is_leader():
        return jsonify({"error": "I am the leader, cannot replicate"}), 400

    message = request.get_json()
    log_manager.write_message(message)
    print(f"[Follower] Replicated message to local log")
    return jsonify({"status": "ack"}), 200

@app.route('/consume', methods=['GET'])
def consume():
    try:
        start_offset = int(request.args.get('offset', 1))
    except ValueError:
        return jsonify({"error": "Invalid offset format"}), 400

    hwm = state_manager.get_hwm()
    all_messages = log_manager.read_messages(start_offset)
    
    # Only return messages that are "committed" (i.e., up to the HWM)
    # The offset is the line number, which is index + 1
    committed_messages = [msg for i, msg in enumerate(all_messages) if start_offset + i <= hwm]

    return jsonify({"messages": committed_messages, "hwm": hwm}), 200

@app.route('/metadata/leader', methods=['GET'])
def get_leader_info():
    leader = state_manager.get_leader()
    if leader:
        return jsonify({"leader": leader}), 200
    else:
        return jsonify({"error": "No leader elected yet"}), 503

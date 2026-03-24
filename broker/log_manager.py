# broker/log_manager.py
import os
import json

class LogManager:
    """
    Manages a simple file-based log. Each message is stored as a JSON object on a new line.
    The offset is simply the line number (1-indexed).
    """
    def __init__(self, broker_id):
        self.log_file = f"broker_{broker_id}_log.log"
        # Clear the log file on start for a clean demo
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def write_message(self, message_data):
        """Appends a message to the log file and returns its offset."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(message_data) + '\n')
        
        with open(self.log_file, 'r') as f:
            offset = len(f.readlines())
        
        return offset

    def read_messages(self, start_offset):
        """Reads all messages from the log starting from a given offset."""
        messages = []
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                if start_offset > len(lines):
                    return []
                
                for line in lines[start_offset-1:]:
                    messages.append(json.loads(line))
        except FileNotFoundError:
            return []
        return messages
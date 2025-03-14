import time
import hashlib
import json
import logging


MAX_NONCE = 2 ** 32
CURR_TARGET = 4 # Number of leading zeroes required
BLOCK_GENERATION_INTERVAL = 60  # 60 seconds per block


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Block:
    def __init__(self, block_number: int, transactions, prev_hash, nonce = None, timestamp = None, curr_hash = None):
        self.block_number = block_number
        if not transactions:
            raise ValueError("Transactions cannot be null or empty.")
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.timestamp = timestamp
        self.curr_hash = curr_hash

        # Only compute hash if not provided
        if self.curr_hash is None:
            self.compute_and_set_hash()


    def compute_and_set_hash(self):
        for nonce in range(MAX_NONCE):
            timestamp = time.time()  # timestamp in float
            self.timestamp = int(timestamp)  # timestamp in seconds
            self.nonce = nonce
            self.curr_hash = self.calculate_hash()
            if (self.is_valid_hash()):
                logging.info(f"Block {self.block_number}: Valid hash found with nonce {nonce}.")
                break


    def calculate_hash(self):
        block_data = {
            "block_number": self.block_number,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }

        # Convert block data to JSON with sorted keys
        encoded_block = json.dumps(block_data, sort_keys=True).encode() # Converts the JSON string into a byte representation
        return hashlib.sha256(encoded_block).hexdigest()
    

    def is_valid_hash(self):
        return self.curr_hash.startswith("0" * CURR_TARGET)
    

    def print_block(self):
        print(f"Block No: {self.block_number}, Transactions: {self.transactions}, Nonce: {self.nonce}, Timestamp: {self.timestamp}, PrevHash: {self.prev_hash}, CurrHash: {self.curr_hash}")


    def to_dict(self):
        return {
            "block_number": self.block_number,
            "transactions": self.transactions,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "curr_hash": self.curr_hash
        }
    

    @classmethod
    def from_dict(cls, data):
        return cls(
            block_number = data['block_number'],
            transactions = data['transactions'],
            nonce = data['nonce'],
            timestamp = data['timestamp'],
            prev_hash = data['prev_hash'],
            curr_hash = data['curr_hash']
        )
    

    def adjust_difficulty(self, prev_block_timestamp, new_block_timestamp):
        time_taken = new_block_timestamp - prev_block_timestamp
        global CURR_TARGET
        if time_taken < BLOCK_GENERATION_INTERVAL:
            CURR_TARGET += 1  # Increase difficulty
        elif time_taken > BLOCK_GENERATION_INTERVAL:
            CURR_TARGET = max(1, CURR_TARGET - 1)
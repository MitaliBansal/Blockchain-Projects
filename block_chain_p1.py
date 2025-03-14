import time
import json
import hashlib
from flask import Flask, jsonify, request

MAX_NONCE = 2 ** 32
CURR_TARGET = '0000'


class Block:
    def __init__(self, block_number: int, transactions, prev_hash):
        self.block_number = block_number
        if not transactions or not transactions.strip():
            raise ValueError("Transactions cannot be null or empty.")
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.compute_and_set_hash()


    def compute_and_set_hash(self):
        for nonce in range(MAX_NONCE):
            timestamp = time.time()  # Timestamp in float
            self.timestamp = int(timestamp)  # Timestamp in seconds
            self.nonce = nonce
            self.curr_hash = self.calculate_hash()
            if (self.is_valid_hash()):
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
        return hashlib.sha256(encoded_block).hexdigest() # SHA-256 operate on bytes, not strings
    

    def is_valid_hash(self):
        return self.curr_hash.startswith(CURR_TARGET)
    

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
    

class BlockChain:
    def __init__(self):
        self.chain = []


    def add_block(self, transactions):
        if (len(self.chain) > 0):
            block = Block(len(self.chain) + 1, transactions, self.chain[-1].curr_hash)
        else:
            block = Block(1, transactions, "0" * 64)
        
        self.chain.append(block)


    def is_chain_valid(self):
        if not self.chain[0].is_valid_hash():
            return False
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.prev_hash != previous_block.curr_hash:
                return False
            if not current_block.is_valid_hash():
                return False
        return True


# Create a Flask instance
app = Flask(__name__)
blockChain = BlockChain()


# Define routes and their logic
@app.route('/')  # Root URL
def home():
    return "Ping-Pong"


@app.route('/api/block/<number>', methods=['GET'])
def get_block(number):
    try:
        number = int(number)
        if number < 1 or number > len(blockChain.chain):
            return jsonify({"error": f"Block number {number} is out of range."}), 400

        block = blockChain.chain[number - 1]
        return jsonify(block.to_dict())
    except ValueError:
        return jsonify({"error": "Invalid block number. Must be an integer."}), 400


@app.route('/api/add/block', methods=['POST'])  # POST route
def add_block():
    try:
        data = request.json  # Parse JSON body
        if not data:
            raise ValueError("Invalid JSON body.")

        transactions = data.get('transaction')
        if not transactions:  # Validate the 'transaction' field
            return jsonify({"error": "Transaction field is required."}), 400

        blockChain.add_block(transactions)
        return jsonify({"message": "Block added successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/api/validate/chain')
def validate_chain():
    if len(blockChain.chain) == 0 or blockChain.is_chain_valid():
        return jsonify({"message":"Chain validated successfully"})
    else:
        return jsonify({"message":"Chain contains invalid blocks."})


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
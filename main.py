from flask import Flask, jsonify, request
import logging
import socket
import asyncio
from blockchain import BlockChain
from node import Node
from server import Server
import threading
import sys


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Create a Flask instance
app = Flask(__name__)
hostname = socket.gethostname()
node = Node(socket.gethostbyname(hostname), BlockChain([]), [], set(), set())


# Define routes and their logic
@app.route('/')  # Root URL
def home():
    return "Ping-Pong"


@app.route('/api/add/block', methods=['POST'])  # POST route
def add_block():
    try:
        node.add_block()
        return jsonify({"message": "Block added successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/api/validate/chain')
def validate_chain():
    try:
        if node.blockchain.is_chain_valid(node.blockchain.chain):
            return jsonify({"message": "Chain validated successfully"})
        else:
            return jsonify({"message": "Chain is empty or it contains invalid blocks."})
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@app.route('/api/add/transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        if not data:
            raise ValueError("Invalid JSON body.")
        
        sender_wallet_address = data['sender_wallet_address']
        receiver_wallet_address = data['receiver_wallet_address']
        amount = data['amount']
        signature = data['signature']
        sender_public_key = data['public_key']
        if not sender_wallet_address or not receiver_wallet_address or amount<=0 or not signature or not sender_public_key:
            return jsonify({"error": "Sender, receiver, amount, signature and publicKey fields are required."}), 400
        
        node.add_transaction(sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key)
        return jsonify({"message": "Transaction added successfully."}), 201
    except KeyError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@app.route('/api/add/node', methods=['POST'])
def add_node():
    try:
        data = request.json
        if not data:
            raise ValueError("Invalid JSON body")
        
        node_address = data['node_address']
        if not node_address:
            return jsonify({"error": "node_address is required for adding new node"}), 400
        
        node.add_node(node_address)
        return jsonify({"message": f"Node added successfully: {node_address}"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/api/add/user', methods=['POST'])
def add_user():
    try:
        data = request.json
        if not data:
            raise ValueError("Invalid JSON body.")
        
        name = data['name']
        wallet_address = node.add_user(name)
        return jsonify({"wallet_address": wallet_address}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    

@app.route('/api/fetch/chain')
def fetch_chain():
    data = node.fetch_chain()
    return jsonify(data), 200


@app.route('/api/fetch/peers')
def fetch_peers():
    data = list(node.peers)
    return jsonify(data), 200


@app.route('/api/fetch/users')
def fetch_users():
    data = list(node.users)
    return jsonify(data), 200


def run_websocket(ws_port):
    server_instance = Server()
    asyncio.run(server_instance.start_server(node, ws_port))
        

# Run the Flask app
if __name__ == "__main__":
    try:
        websocket_port = int(sys.argv[1])
        node.peers.add(sys.argv[2])

        # Start WebSocket server thread
        websocket_thread = threading.Thread(target=run_websocket, args=(websocket_port,))
        websocket_thread.start()

        # Start Flask app without reloader
        app.run(debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logging.info("Server stopped.")
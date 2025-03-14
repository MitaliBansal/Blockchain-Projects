from block import Block
from user import User
from transaction import Transaction
from urllib.parse import urlparse
import websockets
import requests
import logging
import json
import asyncio


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Node:
    def __init__(self, node_address, blockchain, pending_transactions, peers, users):
        self.node_address = node_address
        self.blockchain = blockchain
        self.pending_transactions = pending_transactions
        self.peers = peers
        self.users = users


    def add_block(self):
        self.sync_chain_from_peers()
        if (len(self.blockchain.chain) == 0):
            block = Block(1, self.pending_transactions, "0" * 64)
        else:
            block = Block(len(self.blockchain.chain) + 1, self.pending_transactions, self.blockchain.chain[-1].curr_hash)
        
        self.blockchain.add_block(block)
        self.pending_transactions = []
        logging.info("Block added successfully")
        asyncio.run(self.broadcast_event("new_block", block.to_dict()))
        asyncio.run(self.broadcast_event("empty_transactions", ""))
        

    def sync_chain_from_peers(self):
        longest_chain = None
        chain_length = len(self.blockchain.chain)

        for peer in self.peers:
            try:
                logging.info(f"Syncing chain from peer: {peer}")
                response = requests.get(f"http://{peer}/api/fetch/chain")
                peer_chain_data = response.json()
                peer_chain = [Block.from_dict(block_data) for block_data in peer_chain_data]
                logging.info(f"Response from peer: {peer}, chain: {[block.to_dict() for block in peer_chain]}")

                if (len(peer_chain) > chain_length and self.blockchain.is_chain_valid(peer_chain)):
                    chain_length = len(peer_chain)
                    longest_chain = peer_chain
            except:
                logging.warning(f"Failed to sync with {peer}.")
        
        if longest_chain:
            self.blockchain.chain = longest_chain
            logging.info("Blockchain updated from peer.")
        

    def add_node(self, node_address):
        parsed_url = urlparse(node_address) #e.g. node_address = http://127.0.0.1:5000, then parsed_url=(scheme='http', netloc='127.0.0.1:5000', path='/', params = '', query='')
        self.peers.add(parsed_url.netloc)
        logging.info(f"Node added successfully: {parsed_url.netloc}")
        asyncio.run(self.broadcast_event("new_node", parsed_url.netloc))


    def add_user(self, name):
        user = User(name)
        self.users.add(user.get_wallet_address())
        logging.info("User added successfully")
        asyncio.run(self.broadcast_event("new_user", user.get_wallet_address()))
        return user.get_wallet_address()


    def add_transaction(self, sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key):
        self.validate_and_add_transaction(sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key)
        logging.info("Transaction added successfully")
        transaction = {
            "sender_wallet_address": sender_wallet_address,
            "receiver_wallet_address": receiver_wallet_address,
            "amount": amount,
            "signature": signature,
            "sender_public_key": sender_public_key
        }
        asyncio.run(self.broadcast_event("new_transaction", transaction))
        

    async def broadcast_event(self, event_name, data):
        logging.info(f"Broadcasting event: {event_name}, data: {data}, peers: {self.peers}")
        tasks = [self.send_event(peer, event_name, data) for peer in self.peers]
        await asyncio.gather(*tasks)


    def fetch_chain(self):
        return [block.to_dict() for block in self.blockchain.chain]
    

    def process_add_transaction_event(self, sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key):
        self.validate_and_add_transaction(sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key)


    def validate_and_add_transaction(self, sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key):
        if not sender_wallet_address in self.users or not receiver_wallet_address in self.users:
            raise KeyError("sender or receiver wallet address are not correct")

        transaction = Transaction(sender_wallet_address, receiver_wallet_address, amount, None, signature)
        is_signature_valid = transaction.verify_signature(sender_wallet_address, receiver_wallet_address, amount, signature, sender_public_key)
        if not is_signature_valid:
            raise KeyError("invalid signature")
        
        self.pending_transactions.append(transaction.to_dict())


    def process_add_block_event(self, block_number, block):
        logging.info(f"Process add block event: {block}")
        if (len(self.blockchain.chain) == block_number - 1):
            self.blockchain.add_block(Block.from_dict(block))


    def process_add_node_event(self, node_address):
        logging.info(f"Process add node event: {node_address}")
        if (self.node_address != node_address):
            self.peers.add(node_address)


    def process_add_user_event(self, user_wallet_address):
        logging.info(f"Process add user event: {user_wallet_address}")
        self.users.add(user_wallet_address)


    def process_empty_transactions_event(self):
        logging.info("Process empty transactions event")
        self.pending_transactions = []

        
    def sync_peers(self):
        for peer in self.peers.copy():
            try:
                logging.info(f"Syncing peer from node: {peer}")
                response = requests.get(f"http://{peer}/api/fetch/peers", timeout=5)
                response.raise_for_status()  # Raise exception for bad HTTP responses
                peers_data = response.json()
                
                if isinstance(peers_data, list):
                    self.peers.update(peers_data)
                    logging.info(f"Response from node: {peer}, peers: {peers_data}")
                else:
                    logging.warning(f"Invalid peers data from {peer}: {peers_data}")

            except requests.exceptions.Timeout:
                logging.warning(f"Timeout while syncing with {peer}.")
            except requests.exceptions.ConnectionError:
                logging.warning(f"Connection error while syncing with {peer}.")
            except requests.exceptions.HTTPError as http_err:
                logging.warning(f"HTTP error while syncing with {peer}: {http_err}")
            except ValueError:
                logging.warning(f"Invalid JSON received from {peer}.")
            except Exception as e:
                logging.warning(f"Unexpected error while syncing with {peer}: {e}")

    
    def sync_users(self):
        for peer in self.peers:
            try:
                logging.info(f"Syncing users from peer: {peer}")
                response = requests.get(f"http://{peer}/api/fetch/users")
                users_data = response.json()
                logging.info(f"Response from peer: {peer}, users: {users_data}")
                self.users.update(users_data)
            except:
                logging.warning(f"Failed to sync with {peer}.")


    async def send_event(self, node_address, event, payload):
        try:
            parsed_url = urlparse(node_address)
            host = parsed_url.hostname
            port = int(parsed_url.path)
            uri = f"ws://{host}:{port}"
            async with websockets.connect(uri) as websocket:
                message = json.dumps({"event": event, "data": payload})
                await websocket.send(message)  # Send event
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logging.info(f"Received from {node_address}: {response}")
        except Exception as e:
            logging.warning(f"Failed to send event {event} to {node_address}: {e}")
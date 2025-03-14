import websockets
import json
import logging


clients = set()
node = None


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Server:

    @staticmethod
    async def handle_connection(websocket, path=None):
        global clients, node
        clients.add(websocket.remote_address)  # Store the new client connection
        logging.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                logging.info(f"Received: {message}")
                
                try:
                    data = json.loads(message)  # Parse JSON
                    event_type = data.get("event")
                    payload = data.get("data")
                    
                    logging.info(f"Event: {event_type}, Payload: {payload}")

                    if event_type == "new_block":
                        node.process_add_block_event(payload['block_number'], payload)

                    elif event_type == "new_transaction":
                        node.process_add_transaction_event(
                            payload['sender_wallet_address'],
                            payload['receiver_wallet_address'],
                            payload['amount'],
                            payload['signature'],
                            payload['sender_public_key']
                        )

                    elif event_type == "new_node":
                        node.process_add_node_event(payload)

                    elif event_type == "new_user":
                        node.process_add_user_event(payload)

                    elif event_type == "empty_transactions":
                        node.process_empty_transactions_event()

                    else:
                        await websocket.send(json.dumps({"event": "error", "data": "Unknown event"}))

                except json.JSONDecodeError:
                    logging.error("Invalid JSON format")
                    await websocket.send(json.dumps({"event": "error", "data": "Invalid JSON"}))
                
        except websockets.exceptions.ConnectionClosed:
            logging.info("Client disconnected")
            clients.remove(websocket)  # Remove client when disconnected


    async def start_server(self, blockchain_node, ws_port):
        global node, clients
        node = blockchain_node
        clients.update(node.peers)
        node.sync_peers()
        node.sync_users()
        node.sync_chain_from_peers()
        server = await websockets.serve(Server.handle_connection, "0.0.0.0", ws_port)
        logging.info(f"WebSocket server started on ws://0.0.0.0:{ws_port}")
        await server.wait_closed() # The function pauses here, keeps the server running until it's explicitly closed.
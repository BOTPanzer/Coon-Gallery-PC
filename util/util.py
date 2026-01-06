import json
import pathlib
import os
import asyncio
import websockets

# Util functions
class Util:

    @staticmethod
    def save_json(path: str, data, pretty: bool = False):
        with open(path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=4)
            else:
                json.dump(data, f, ensure_ascii=False) # Uglyer but faster and smaller size

    @staticmethod
    def load_json(path: str):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    @staticmethod
    def join(p1, p2):
        return os.path.join(p1, p2)

    @staticmethod
    def get_data_path():
        return Util.join(pathlib.Path().resolve(), 'data')

# WebSocket server
class Server:

    # Constructor
    def __init__(self):
        self.is_running = False
        self.current_connection: websockets.ServerConnection = None

    # Server logic
    async def start(self, HOST: str = '0.0.0.0', PORT: int = 6969):
        # Start server
        try:
            async with websockets.serve(self.handler, HOST, PORT) as server:
                # Mark as running
                self.is_running = True
                self.on_state_changed(self.is_running)
                
                # Wait until the server is closed
                await server.wait_closed()

        # Error    
        except Exception as e:
            self.on_error(f"Server crashed: {e}")

        # Finished
        finally:
            # Mark as not running
            self.is_running = False
            self.on_state_changed(self.is_running)

    async def handler(self, websocket: websockets.ServerConnection):
        # Only allow 1 connection
        if self.current_connection is not None:
            await websocket.send('Only 1 connection allowed at a time')
            await websocket.close()
            return

        # Save connection
        self.current_connection = websocket
        client_ip = websocket.remote_address[0]
        self.on_connection_state_changed(True, client_ip)

        # Listen for messages
        try:
            # Wait for data received
            async for message in websocket:
                if isinstance(message, str):
                    self.on_string_received(websocket, message)
                else:
                    self.on_binary_received(websocket, message)

        # Error
        except websockets.ConnectionClosed as e:
            self.on_error(f"Connection closed: {e}")

        # Finished
        finally:
            # Free connection
            self.current_connection = None
            self.on_connection_state_changed(False, client_ip)

    # Events
    def on_error(self, error: str):
        print(error)

    def on_state_changed(self, is_running: bool):
        if is_running:
            print(f'Server is now running')
        else:
            print(f'Server is now not running')

    def on_connection_state_changed(self, is_open: bool, client_ip: str):
        if is_open:
            print(f'Connection opened with {client_ip}')
        else:
            print(f'Connection closed with {client_ip}')

    def on_string_received(self, message: str):
        print(f'Text received: {message}')

    def on_binary_received(self, data: bytes):
        print(f'Binary received: {len(data)} bytes')
import json
import pathlib
import os
import websockets
import socket

# Util functions
class Util:

    # JSON
    @staticmethod
    def save_json(path: str, data, pretty: bool = False):
        with open(path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=4)
            else:
                json.dump(data, f, ensure_ascii=False) # Uglyer but faster and smaller size

    @staticmethod
    def load_json(path: str) -> dict:
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    # Paths
    @staticmethod
    def join_path(parent, child):
        return os.path.join(parent, child)

    @staticmethod
    def exists_path(path):
        return os.path.exists(path)

    @staticmethod
    def get_last_modified(path):
        return os.path.getmtime(path)

    @staticmethod
    def set_last_modified(path, last_modified):
        return os.utime(path, (last_modified, last_modified))

    @staticmethod
    def get_data_path():
        return Util.join_path(pathlib.Path().resolve(), 'data')

    # Network
    @staticmethod
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # We don't actually connect, but this identifies the right interface
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            # Fallback to localhost if no network
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

# WebSocket server
class Server:

    # Constructor
    def __init__(self):
        # Server
        self.logs = []
        self.is_running = False
        self.connection: websockets.ServerConnection = None

    # Server logic
    async def start(self, HOST: str = '0.0.0.0', PORT: int = 6969):
        # Log starting
        self.log_message(f'Starting server in {Util.get_local_ip()}:{PORT}...')

        # Start server
        try:
            async with websockets.serve(self.handler, HOST, PORT) as server:
                # Mark as running
                self.is_running = True
                self.on_server_state_changed(self.is_running)
                
                # Wait until the server is closed
                await server.wait_closed()

        # Error
        except Exception as e:
            self.on_error(f"Internal error: {e}")

        # Finished
        finally:
            # Mark as not running
            self.is_running = False
            self.on_server_state_changed(self.is_running)

    async def handler(self, websocket: websockets.ServerConnection):
        # Get IP
        client_ip = websocket.remote_address[0]

        # Only allow 1 connection
        if self.connection is not None:
            self.log_message(f'Connection from {client_ip} refused, only 1 connection is allowed')
            await websocket.send('Only 1 connection allowed at a time')
            await websocket.close()
            return

        # Save connection
        self.connection = websocket
        self.on_connection_state_changed(True, client_ip)

        # Listen for messages
        try:
            # Wait for data received
            async for message in websocket:
                if isinstance(message, str):
                    self.on_received_string(message)
                else:
                    self.on_received_binary(message)

        # Errors
        except websockets.ConnectionClosed as e:
            self.on_error(f"Connection closed: {e}")
        except Exception as e:
            self.on_error(f"Internal error: {e}")

        # Finished
        finally:
            # Free connection
            self.connection = None
            self.on_connection_state_changed(False, client_ip)

    # Events
    def log_message(self, message: str):
        # Log
        self.logs.append(message)

    def on_error(self, error: str):
        # Log
        self.log_message(error)

    def on_server_state_changed(self, is_running: bool):
        # Log
        if is_running:
            self.log_message(f'Server is now running')
        else:
            self.log_message(f'Server is now not running')

    def on_connection_state_changed(self, is_open: bool, client_ip: str):
        # Log
        if is_open:
            self.log_message(f'Connected to client {client_ip}')
        else:
            self.log_message(f'Disconnected from client {client_ip}')

    def on_received_string(self, message: str):
        # Log
        self.log_message(f'Received string: {len(message)} chars')

    def on_received_binary(self, data: bytes):
        # Log
        self.log_message(f'Received bytes: {len(data)} bytes')

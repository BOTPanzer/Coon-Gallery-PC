import json
import pathlib
import os
import websockets
import socket

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

    # Singleton
    current: "Server" = None


    # Constructor
    def __init__(self):
        # Server
        self.logs = []
        self.is_running = False
        self.current_connection: websockets.ServerConnection = None

        # Events
        self.events_on_log_message = set()
        self.events_on_error = set()
        self.events_on_server_state_changed = set()
        self.events_on_connection_state_changed = set()
        self.events_on_received_string = set()
        self.events_on_received_bytes = set()

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
            self.on_error(f"Server crashed: {e}")

        # Finished
        finally:
            # Mark as not running
            self.is_running = False
            self.on_server_state_changed(self.is_running)

    async def handler(self, websocket: websockets.ServerConnection):
        # Get IP
        client_ip = websocket.remote_address[0]

        # Only allow 1 connection
        if self.current_connection is not None:
            self.log_message(f'Connection from {client_ip} refused, only 1 connection is allowed')
            await websocket.send('Only 1 connection allowed at a time')
            await websocket.close()
            return

        # Save connection
        self.current_connection = websocket
        self.on_connection_state_changed(True, client_ip)

        # Listen for messages
        try:
            # Wait for data received
            async for message in websocket:
                if isinstance(message, str):
                    self.on_received_string(websocket, message)
                else:
                    self.on_received_binary(websocket, message)

        # Error
        except websockets.ConnectionClosed as e:
            self.on_error(f"Connection closed: {e}")

        # Finished
        finally:
            # Free connection
            self.current_connection = None
            self.on_connection_state_changed(False, client_ip)

    # Events
    def register_events(self, log_message = None, error = None, server_state_changed = None, connection_state_changed = None, received_string = None, received_bytes = None):
        if log_message is not None: 
            self.events_on_log_message.add(log_message)
        if error is not None: 
            self.events_on_error.add(error)
        if server_state_changed is not None: 
            self.events_on_server_state_changed.add(server_state_changed)
        if connection_state_changed is not None: 
            self.events_on_connection_state_changed.add(connection_state_changed)
        if received_string is not None: 
            self.events_on_received_string.add(received_string)
        if received_bytes is not None: 
            self.events_on_received_bytes.add(received_bytes)

    def unregister_events(self, log_message = None, error = None, server_state_changed = None, connection_state_changed = None, received_string = None, received_bytes = None):
        if log_message is not None: 
            self.events_on_log_message.discard(log_message)
        if error is not None: 
            self.events_on_error.discard(error)
        if server_state_changed is not None: 
            self.events_on_server_state_changed.discard(server_state_changed)
        if connection_state_changed is not None: 
            self.events_on_connection_state_changed.discard(connection_state_changed)
        if received_string is not None: 
            self.events_on_received_string.discard(received_string)
        if received_bytes is not None: 
            self.events_on_received_bytes.discard(received_bytes)

    def log_message(self, message: str):
        # Log
        self.logs.append(message)

        # Call event
        for callback in self.events_on_log_message: callback(message)

    def on_error(self, error: str):
        # Log
        self.log_message(error)

        # Call event
        for callback in self.events_on_error: callback(error)

    def on_server_state_changed(self, is_running: bool):
        # Log
        if is_running:
            self.log_message(f'Server is now running')
        else:
            self.log_message(f'Server is now not running')

        # Call event
        for callback in self.events_on_server_state_changed: callback(is_running)

    def on_connection_state_changed(self, is_open: bool, client_ip: str):
        # Log
        if is_open:
            self.log_message(f'Connection opened with {client_ip}')
        else:
            self.log_message(f'Connection closed with {client_ip}')

        # Call event
        for callback in self.events_on_connection_state_changed: callback(is_open, client_ip)

    def on_received_string(self, message: str):
        # Call event
        for callback in self.events_on_received_string: callback(message)

    def on_received_binary(self, data: bytes):
        # Call event
        for callback in self.events_on_received_bytes: callback(data)

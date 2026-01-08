import json
import pathlib
import os
import websockets
import socket
import tkinter as tk
from tkinter import filedialog

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
    def join_path(parent: str, child: str) -> str:
        return os.path.join(parent, child)

    @staticmethod
    def exists_path(path: str) -> bool:
        return os.path.exists(path)

    @staticmethod
    def get_last_modified(path: str) -> float:
        return os.path.getmtime(path)

    @staticmethod
    def set_last_modified(path: str, last_modified: int):
        os.utime(path, (last_modified, last_modified))

    @staticmethod
    def get_data_path() -> str:
        return Util.join_path(pathlib.Path().resolve(), 'data')

    # Explorer
    @staticmethod
    def ask_for_folder(title: str = None) -> str:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) # Bring to front
        folder_path = filedialog.askdirectory(title=title)
        root.destroy()
        return folder_path

    @staticmethod
    def ask_for_file(title: str = None) -> str:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) # Bring to front
        file_path = filedialog.askopenfilename(title=title)
        root.destroy()
        return file_path

    # Network
    @staticmethod
    def get_local_ip() -> str:
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
        self.is_connected = False
        self.connection: websockets.ServerConnection = None

    # Server logic
    async def start(self, HOST: str = '0.0.0.0', PORT: int = 6969):
        # Check if already running
        if self.is_running:
            self.log_message('Server is already running')
            return

        # Save connection address
        self.IP = Util.get_local_ip()
        self.PORT = PORT

        # Log starting
        self.log_message(f'Starting server in {self.IP}:{self.PORT}...')

        # Start server
        try:
            async with websockets.serve(
                self.handler, 
                HOST, 
                PORT, 
                max_size=10_485_760  # 10 MB limit
            ) as server:
                # Mark as running
                self.is_running = True
                self.on_server_state_changed(self.is_running)
                
                # Wait until the server is closed
                await server.wait_closed()

        # Error
        except Exception as e:
            self.log_message(f"Internal error: {e}")

        # Finished
        finally:
            # Mark as not running
            self.is_running = False
            self.on_server_state_changed(self.is_running)

    async def handler(self, websocket: websockets.ServerConnection):
        # Get IP
        client_ip = websocket.remote_address[0]

        # Only allow 1 connection
        if self.is_connected:
            self.log_message(f'Connection from {client_ip} refused, only 1 connection is allowed')
            await websocket.close()
            return

        # Save connection
        self.is_connected = True
        self.connection = websocket
        self.on_connection_state_changed(True, client_ip)

        # Listen for messages
        try:
            # Wait for data received
            async for message in websocket:
                if isinstance(message, str):
                    await self.on_received_string(message)
                else:
                    await self.on_received_binary(message)

        # Errors
        except websockets.ConnectionClosed as e:
            self.log_message(f"Connection closed: {e}")
        except Exception as e:
            self.log_message(f"Internal error: {e}")

        # Finished
        finally:
            # Free connection
            self.is_connected = False
            self.connection = None
            self.on_connection_state_changed(False, client_ip)

    # Logs
    def log_message(self, message: str):
        # Log
        self.logs.append(message)

    # State
    def on_server_state_changed(self, is_running: bool):
        # Log
        if is_running:
            self.log_message(f'Server is now running')
        else:
            self.log_message(f'Server is now not running')

    def on_connection_state_changed(self, is_open: bool, client_ip: str):
        # Log
        if is_open:
            self.log_message(f'Connected to client with IP {client_ip}')
        else:
            self.log_message(f'Disconnected from client with IP {client_ip}')

    # Data
    async def on_received_string(self, message: str):
        # Log
        self.log_message(f'Received string: {len(message)} chars')

    async def on_received_binary(self, data: bytes):
        # Log
        self.log_message(f'Received bytes: {len(data)} bytes')

    # Helpers
    async def send(self, data):
        # Send data to client
        if self.is_connected:
            await self.connection.send(data)

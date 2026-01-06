from util.library import Album, Library
from util.util import Server
from dataclasses import dataclass, field
from os.path import getmtime
from pathlib import Path
import json

# Sync server
class SyncServer(Server):

    # Singleton
    current: "SyncServer" = None


    # Constructor
    def __init__(self):
        # Info
        self.reset_info()

        # Events
        self.events_on_log_message = set()
        self.events_on_error = set()
        self.events_on_server_state_changed = set()
        self.events_on_connection_state_changed = set()

        # Init parent
        super().__init__()

    def reset_info(self):
        # App info (this pc)
        self.app = SyncAppInfo()

        # Client info (the connected phone)
        self.client = SyncClientInfo()

    # Events
    def register_events(self, log_message = None, error = None, server_state_changed = None, connection_state_changed = None):
        if log_message is not None: 
            self.events_on_log_message.add(log_message)
        if error is not None: 
            self.events_on_error.add(error)
        if server_state_changed is not None: 
            self.events_on_server_state_changed.add(server_state_changed)
        if connection_state_changed is not None: 
            self.events_on_connection_state_changed.add(connection_state_changed)

    def unregister_events(self, log_message = None, error = None, server_state_changed = None, connection_state_changed = None):
        if log_message is not None: 
            self.events_on_log_message.discard(log_message)
        if error is not None: 
            self.events_on_error.discard(error)
        if server_state_changed is not None: 
            self.events_on_server_state_changed.discard(server_state_changed)
        if connection_state_changed is not None: 
            self.events_on_connection_state_changed.discard(connection_state_changed)

    def log_message(self, message: str):
        # Call parent function
        super().log_message(message)

        # Call event
        for callback in self.events_on_log_message: callback(message)

    def on_error(self, error: str):
        # Call parent function
        super().on_error(error)

        # Call event
        for callback in self.events_on_error: callback(error)

    def on_server_state_changed(self, is_running: bool):
        # Call parent function
        super().on_server_state_changed(is_running)

        # Call event
        for callback in self.events_on_server_state_changed: callback(is_running)

    def on_connection_state_changed(self, is_open: bool, client_ip: str):
        # Call parent function
        super().on_connection_state_changed(is_open, client_ip)

        # Reset info if connection was closed
        if not is_open: self.reset_info()

        # Call event
        for callback in self.events_on_connection_state_changed: callback(is_open, client_ip)

    def on_received_string(self, message: str):
        # Parse JSON from string
        try:
            # Parse JSON
            data = json.loads(message)

            # Get action
            if not 'action' in data: return
            action = data['action']

            # Check action
            match action:
                # End sync
                case 'endSync':
                    self.action_end_sync(data)

                # Received client albums
                case 'albums':
                    self.action_received_albums(data)

                # Received file info
                case 'fileInfo':
                    self.action_received_file_info(data)

                # Received metadata info
                case 'metadataInfo':
                    self.action_received_metadata_info(data)

                # Send metadata info
                case 'requestMetadataInfo':
                    self.action_send_metadata_info(data)

                # Send metadata data
                case 'requestMetadataData':
                    self.action_send_metadata_data(data)

        except json.JSONDecodeError as e:
            # Failed to parse json
            self.on_error(f'Failed to parse JSON: {e}')

    # Syncing
    def toggle_syncing(self, new_syncing: bool):
        self.app.is_syncing = new_syncing

    # Actions
    def action_end_sync(self, data):
        # Stop syncing
        self.toggle_syncing(False)

        # Log
        if 'message' in data: self.log_message(data['message'])

    def action_received_albums(self, data):
        # Save albums list
        self.client.albums = data['albums']

        # Log
        self.log_message('Received client albums list')

    def action_received_file_info(self, data):
        # Check if info is for the current request
        request = self.app.request
        if request.albumIndex is not data['albumIndex'] or request.fileIndex is not data['fileIndex']: return

        # Check if info is valid
        if 'lastModified' not in data: 
            # Invalid info -> Request next
            ''' galleryRequestQueueFiles() '''
            return

        # Save info
        request.lastModified = data['lastModified']
        request.size = data['size']
        request.parts = data['parts']
        request.maxPartSize = data['maxPartSize']

        # Request data
        self.connection.send(json.dumps({
            'action': 'requestFileData',
            'albumIndex': request.albumIndex,
            'fileIndex': request.fileIndex,
            'part': request.partIndex
        }))

    def action_received_metadata_info(self, data):
        # Check if info is for the current request
        request = self.app.request
        if request.albumIndex is not data['albumIndex']: return

        # Check if info is valid
        if 'lastModified' not in data: 
            # Invalid info -> Request next
            ''' galleryRequestQueueFiles() '''
            return

        # Save info
        request.lastModified = data['lastModified']

        # Request data
        self.connection.send(json.dumps({
            'action': 'requestMetadataData',
            'albumIndex': request.albumIndex
        }))

    def action_send_metadata_info(self, data):
        # Get info
        albumIndex = data['albumIndex']

        # Get file
        metadataFile = Library.links[albumIndex].metadata_path

        # Send info
        self.connection.send(json.dumps({
            'action': 'metadataInfo',
            'albumIndex': albumIndex,
            'lastModified': getmtime(metadataFile)
        }))

    def action_send_metadata_data(self, data):
        # Get info
        albumIndex = data['albumIndex']

        # Get file
        metadataFile = Library.links[albumIndex].metadata_path

        # Send info
        self.connection.send(Path(metadataFile).read_bytes())

# Sync info (requests)
@dataclass
class SyncRequestInfo:
    # Indexes
    albumIndex: int = -1,
    fileIndex: int = -1,
    partIndex: int = 0

    # File info
    lastModified: int = -1,
    size: int = 0

    # Parts info
    parts: int = 0
    maxPartSize: int = 0

# Sync info (app)
@dataclass
class SyncAppInfo:
    # App
    is_syncing: bool = False

    # Albums
    albums: list[Album] = field(default_factory=list)

    # File request
    request: SyncRequestInfo = SyncRequestInfo()

    # Queue info
    queue: list = field(default_factory=list),
    queueSize: int = 0

# Sync info (client)
@dataclass
class SyncClientInfo:
    # Albums
    albums: list[list[str]] = field(default_factory=list)
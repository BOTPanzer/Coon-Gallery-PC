from util.library import Album, Library
from util.util import Util, Server
from dataclasses import dataclass, field
from pathlib import Path
import json

# Sync info (requests)
@dataclass
class SyncRequestInfo:
    # Album
    album_index: int = -1,
    item_index: int = -1,

    # File info
    last_modified: int = 0,
    size: int = 0

    # Parts info
    part_index: int = 0
    part_max_size: int = 0
    parts: int = 1

# Sync info (queue items)
@dataclass
class SyncQueueItem:
    album_index: int = -1
    item_index: int = -1

# Sync info (app)
@dataclass
class SyncAppInfo:
    # App
    is_syncing: bool = False

    # Albums
    albums: list[Album] = field(default_factory=list)

    # File request
    request: SyncRequestInfo = field(default_factory=SyncRequestInfo)

    # Queue info
    queue_index: int = -1
    queue: list[SyncQueueItem] = field(default_factory=list),

# Sync info (client)
@dataclass
class SyncClientInfo:
    # Albums
    albums: list[list[str]] = field(default_factory=list)

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

    def on_received_string(self, string: str):
        # Parse JSON from string
        try:
            # Parse JSON
            message = json.loads(string)

            # Check if message has action
            if not 'action' in message: 
                # No action -> Show error
                self.on_error(f'Missing JSON message action')
            else:
                # Has action -> Check it
                match message['action']:
                    # End sync
                    case 'endSync': self.action_end_sync(message)

                    # Received client albums
                    case 'albums': self.action_received_albums(message)

                    # Received item info
                    case 'fileInfo': self.action_received_item_info(message)

                    # Received metadata info
                    case 'metadataInfo': self.action_received_metadata_info(message)

                    # Send metadata info
                    case 'requestMetadataInfo': self.action_send_metadata_info(message)

                    # Send metadata data
                    case 'requestMetadataData': self.action_send_metadata_data(message)

        except json.JSONDecodeError as e:
            # Failed to parse json
            self.on_error(f'Failed to parse JSON: {e}')

    def on_received_binary(self, data):
        # Get request
        request = self.app.request

        # Check request type
        if request.item_index >= 0:
            # Has item index -> Is a file request
            self.action_received_item_data(request, data)
        else:
            # No item index _> Is a metadata request
            self.action_received_metadata_data(request, data)

    # Syncing
    def toggle_syncing(self, new_syncing: bool):
        self.app.is_syncing = new_syncing

    # Actions
    def action_end_sync(self, message: dict):
        # Stop syncing
        self.toggle_syncing(False)

        # Log
        if 'message' in message: self.log_message(message['message'])

    def action_received_albums(self, message: dict):
        # Save albums list
        self.client.albums = message['albums']

        # Log
        self.log_message('Received client albums list')

    # Actions (receive item)
    def action_received_item_info(self, message: dict):
        # Create new request info
        request = SyncRequestInfo()
        request.album_index = message['albumIndex']
        request.item_index = message['fileIndex']
        request.last_modified = message['lastModified']
        request.size = message['size']
        request.part_max_size = message['maxPartSize']
        request.parts = message['parts']
        self.app.request = request

        # Request data
        self.connection.send(json.dumps({
            'action': 'requestFileData',
            'albumIndex': request.album_index,
            'fileIndex': request.item_index,
            'part': request.part_index
        }))

    def action_received_item_data(self, request: SyncRequestInfo, data: bytes):
        # Get info
        album_index = request.album_index
        item_index = request.item_index
        part_index = request.part_index
        item_name = self.client.albums[album_index][item_index]
        item_path = Util.join_path(Library.links[album_index].album_path, item_name)

        # Manage write data
        finished: bool = self.manage_write_data(request, data, item_path)

        # Check if finished
        if finished:
            # Finished -> Request next
            self.request_next_queue_item()
        else:
            # Not finished -> Request next part
            self.connection.send(json.dumps({
                'action': 'requestFileData',
                'albumIndex': album_index,
                'fileIndex': item_index,
                'part': part_index
            }))

    # Actions (receive metadata)
    def action_received_metadata_info(self, message: dict):
        # Create new request info
        request = SyncRequestInfo()
        request.album_index = message['albumIndex']
        #request.item_index = message['fileIndex']
        request.last_modified = message['lastModified']
        #request.size = message['size']
        #request.part_max_size = message['maxPartSize']
        #request.parts = message['parts']
        self.app.request = request

        # Request data
        self.connection.send(json.dumps({
            'action': 'requestMetadataData',
            'albumIndex': request.album_index
        }))

    def action_received_metadata_data(self, request: SyncRequestInfo, data: bytes):
        # Get info
        album_index = request.album_index
        item_path = Library.links[album_index].metadata_path

        # Manage write data
        finished: bool = self.manage_write_data(request, data, item_path)

        # Check if finished
        if finished:
            # Finished -> Request next
            self.request_next_queue_metadata()
        else:
            # Not finished -> Request next part
            self.connection.send(json.dumps({
                'action': 'requestMetadataData',
                'albumIndex': album_index
            }))

    # Actions (send metadata)
    def action_send_metadata_info(self, message: dict):
        # Get info
        album_index = message['albumIndex']
        metadata_path = Library.links[album_index].metadata_path

        # Send info
        self.connection.send(json.dumps({
            'action': 'metadataInfo',
            'albumIndex': album_index,
            'lastModified': Util.get_last_modified(metadata_path)
        }))

    def action_send_metadata_data(self, message: dict):
        # Get info
        album_index = message['albumIndex']
        metadata_path = Library.links[album_index].metadata_path

        # Send info
        self.connection.send(Path(metadata_path).read_bytes())

    # Helpers
    def manage_write_data(self, request: SyncRequestInfo, data: bytes, item_path: str) -> bool:
        # Get info
        last_modified = request.last_modified
        size = max(request.size, len(data)) # Use data length in case size was not determined (metadata doesn't)

        part_index = request.part_index
        part_max_size = request.part_max_size
        parts = request.parts

        is_valid = len(data) > 0
        is_last = (part_index + 1) == parts

        # Log parts progress if composed of more than 1
        if parts != 1: 
            self.log_message(f'Received part ${part_index + 1}/${parts}')

        # Write file
        if is_valid:
            # File does not exist -> Create it & resize it to full size
            if not Util.exists_path(item_path):
                with open(item_path, 'wb') as f: 
                    f.truncate(size)

            # Write data on part offset
            with open(item_path, 'rb+') as f:
                offset = part_index * part_max_size
                f.seek(offset)
                f.write(data)

            # Mark part as complete
            request.part_index += 1

            # Check if is the last part 
            if is_last:
                # Is the last part -> Update last modified timestamp
                Util.set_last_modified(item_path, (last_modified, last_modified))

                # Log progress
                progress_current = (self.app.queue_index + 1)
                progress_size = len(self.app.queue)
                percent = round(progress_current / progress_size * 100, 2)
                self.log_message(f'({progress_current}/{progress_size}, {percent}%) {'Item received succesfully' if is_valid else 'Error receiving item'}')
            else:
                # Not the last part -> Mark as not finished
                return False
        else:
            # Log error
            self.log_message(f'Invalid data')

        # Mark as finished
        return True

    def request_next_queue_item(self):
        # Check if still connected
        if self.connection == None: return

        # Update queue index
        self.app.queue_index += 1
        queue_index = self.app.queue_index
        queue_size = len(self.app.queue)

        # Check if queue has remaining items
        if queue_index >= queue_size - 1:
            # No items left -> Finished sync
            self.toggle_syncing(False)
            self.log_message('Finished albums sync')
        else:
            # Items left -> Get next item
            next = self.app.queue[queue_index]

            # Request next
            self.connection.send(json.dumps({
                'action': 'requestFileInfo',
                'albumIndex': next.album_index,
                'fileIndex': next.item_index,
                'requestIndex': queue_index,
                'requestCount': queue_size
            }))

    def request_next_queue_metadata(self):
        # Check if still connected
        if self.connection == None: return

        # Update queue index
        self.app.queue_index += 1
        queue_index = self.app.queue_index
        queue_size = len(self.app.queue)

        # Check if queue has remaining items
        if queue_index >= queue_size - 1:
            # No items left -> Finished sync
            self.toggle_syncing(False)
            self.log_message('Finished metadata sync')
        else:
            # Items left -> Get next item
            next = self.app.queue[queue_index]

            # Request next
            self.connection.send(json.dumps({
                'action': 'requestMetadataInfo',
                'albumIndex': next.album_index
            }))
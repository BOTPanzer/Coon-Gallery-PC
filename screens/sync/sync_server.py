from util.library import Album, Library, Link
from util.util import Util, Server
from dataclasses import dataclass, field
from pathlib import Path
import json

# Sync info (requests)
@dataclass
class Request:
    # Album
    album_index: int = -1
    item_index: int = -1

    # File info
    last_modified: int = 0
    size: int = 0

    # Parts info
    part_index: int = 0
    part_max_size: int = 0
    parts: int = 1

# Sync info (queue items)
@dataclass
class QueueItem:
    album_index: int = -1
    item_index: int = -1

# Sync info (host)
@dataclass
class HostInfo:
    # Albums
    albums: list[Album] = field(default_factory=list)

    # File request
    request: Request = None

    # Queue info
    queue_index: int = -1
    queue: list[QueueItem] = field(default_factory=list)

# Sync info (client)
@dataclass
class ClientInfo:
    # Albums
    albums: list[list[str]] = field(default_factory=list)

# Sync server
class SyncServer(Server):

    # Singleton
    current: "SyncServer" = None


    # Constructor
    def __init__(self):
        # Info
        self.is_syncing = False
        self.reset_info()

        # Events
        self.events_on_log_message = set()
        self.events_on_error = set()
        self.events_on_server_state_changed = set()
        self.events_on_connection_state_changed = set()

        # Init parent
        super().__init__()

    def reset_info(self):
        # Host info (this pc)
        self.host = HostInfo()

        # Client info (the connected phone)
        self.client = ClientInfo()

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
        if not is_open: 
            self.set_syncing(False)
            self.reset_info()

        # Call event
        for callback in self.events_on_connection_state_changed: callback(is_open, client_ip)

    async def on_received_string(self, string: str):
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
                    case 'fileInfo': await self.action_received_item_info(message)

                    # Received metadata info
                    case 'metadataInfo': await self.action_received_metadata_info(message)

                    # Send metadata info
                    case 'requestMetadataInfo': await self.action_send_metadata_info(message)

                    # Send metadata data
                    case 'requestMetadataData': await self.action_send_metadata_data(message)

        except json.JSONDecodeError as e:
            # Failed to parse json
            self.on_error(f'Failed to parse JSON: {e}')

    async def on_received_binary(self, data: bytes):
        # Get request
        request = self.host.request

        # Check request type
        if request.item_index >= 0:
            # Has item index -> Is a file request
            await self.action_received_item_data(request, data)
        else:
            # No item index _> Is a metadata request
            await self.action_received_metadata_data(request, data)

    # Syncing
    def set_syncing(self, new_syncing: bool):
        self.is_syncing = new_syncing

    # Actions
    def action_end_sync(self, message: dict):
        # Stop syncing
        self.set_syncing(False)

        # Log
        if 'message' in message: self.log_message(message['message'])

    def action_received_albums(self, message: dict):
        # Save albums list
        self.client.albums = message['albums']

        # Log
        self.log_message('Received client albums list')

    # Actions (receive item)
    async def action_received_item_info(self, message: dict):
        # Create new request info
        request = Request()
        request.album_index = message['albumIndex']
        request.item_index = message['fileIndex']
        request.last_modified = message['lastModified']
        request.size = message['size']
        request.part_max_size = message['maxPartSize']
        request.parts = message['parts']
        self.host.request = request

        # Request data
        await self.send(json.dumps({
            'action': 'requestFileData',
            'albumIndex': request.album_index,
            'fileIndex': request.item_index,
            'part': request.part_index
        }))

    async def action_received_item_data(self, request: Request, data: bytes):
        # Get info
        album_index: int = request.album_index
        item_index: int = request.item_index
        part_index: int = request.part_index
        item_name: str = self.client.albums[album_index][item_index]
        item_path: str = Util.join_path(Library.links[album_index].album_path, item_name)

        # Manage write data
        finished: bool = self.manage_write_data(request, data, item_path)

        # Check if finished
        if finished:
            # Finished -> Request next
            await self.request_next_queue_item()
        else:
            # Not finished -> Request next part
            await self.send(json.dumps({
                'action': 'requestFileData',
                'albumIndex': album_index,
                'fileIndex': item_index,
                'part': part_index
            }))

    # Actions (receive metadata)
    async def action_received_metadata_info(self, message: dict):
        # Create new request info
        request = Request()
        request.album_index = message['albumIndex']
        #request.item_index = message['fileIndex']
        request.last_modified = message['lastModified']
        #request.size = message['size']
        #request.part_max_size = message['maxPartSize']
        #request.parts = message['parts']
        self.host.request = request

        # Request data
        await self.send(json.dumps({
            'action': 'requestMetadataData',
            'albumIndex': request.album_index
        }))

    async def action_received_metadata_data(self, request: Request, data: bytes):
        # Get info
        album_index: int = request.album_index
        item_path: str = Library.links[album_index].metadata_path

        # Manage write data
        finished: bool = self.manage_write_data(request, data, item_path)

        # Check if finished
        if finished:
            # Finished -> Request next
            await self.request_next_queue_metadata()
        else:
            # Not finished -> Request next part
            await self.send(json.dumps({
                'action': 'requestMetadataData',
                'albumIndex': album_index
            }))

    # Actions (send metadata)
    async def action_send_metadata_info(self, message: dict):
        # Get info
        album_index: int = message['albumIndex']
        metadata_path: str = Library.links[album_index].metadata_path

        # Log
        self.log_message(f'- Sending metadata for album {album_index}...')

        # Send info
        await self.send(json.dumps({
            'action': 'metadataInfo',
            'albumIndex': album_index,
            'lastModified': Util.get_last_modified(metadata_path)
        }))

    async def action_send_metadata_data(self, message: dict):
        # Get info
        album_index: int = message['albumIndex']
        metadata_path: str = Library.links[album_index].metadata_path

        # Send info
        await self.send(Path(metadata_path).read_bytes())

    # Helpers
    def manage_write_data(self, request: Request, data: bytes, item_path: str) -> bool:
        # Get info
        last_modified: int = request.last_modified
        size: int = max(request.size, len(data)) # Use data length in case size was not determined (metadata doesn't)

        part_index: int = request.part_index
        part_max_size: int = request.part_max_size
        parts: int = request.parts

        is_valid: bool = len(data) > 0
        is_last: bool = (part_index + 1) == parts

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
                Util.set_last_modified(item_path, last_modified)

                # Log progress
                progress_current = (self.host.queue_index + 1)
                progress_size = len(self.host.queue)
                percent = round(progress_current / progress_size * 100, 2)
                self.log_message(f'({progress_current}/{progress_size}, {percent}%) {'Success' if is_valid else 'Error, data is invalid'}')
            else:
                # Not the last part -> Log progress
                self.log_message(f'Received part {part_index + 1}/{parts}')

                # Mark as not finished
                return False
        else:
            # Log error
            self.log_message(f'Invalid data')

        # Mark as finished
        return True

    async def request_next_queue_item(self):
        # Check if still connected
        if not self.is_connected: return

        # Update queue index
        self.host.queue_index += 1
        queue_index = self.host.queue_index
        queue_size = len(self.host.queue)

        # Check if queue has remaining items
        if queue_index >= queue_size:
            # No items left -> Finished sync
            self.set_syncing(False)
            self.log_message('Finished downloading albums')
        else:
            # Items left -> Get next item
            next = self.host.queue[queue_index]

            # Request next
            self.log_message(f'- Requesting "{self.host.albums[next.album_index][next.item_index]}"...')
            await self.send(json.dumps({
                'action': 'requestFileInfo',
                'albumIndex': next.album_index,
                'fileIndex': next.item_index,
                'requestIndex': queue_index,
                'requestCount': queue_size
            }))

    async def request_next_queue_metadata(self):
        # Check if still connected
        if not self.is_connected: return

        # Update queue index
        self.host.queue_index += 1
        queue_index = self.host.queue_index
        queue_size = len(self.host.queue)

        # Check if queue has remaining items
        if queue_index >= queue_size:
            # No items left -> Finished sync
            self.set_syncing(False)
            self.log_message('Finished downloading metadata')
        else:
            # Items left -> Get next item
            next = self.host.queue[queue_index]

            # Request next
            self.log_message(f'- Requesting metadata for album {next.album_index}...')
            await self.send(json.dumps({
                'action': 'requestMetadataInfo',
                'albumIndex': next.album_index
            }))

    def can_use(self) -> bool:
        # Check if server is running
        if not self.is_running: 
            self.log_message('Server is not running')
            return False

        # Check if a client is connected
        if not self.is_connected: 
            self.log_message('Connect your phone first')
            return False

        # Check if server is syncing
        if self.is_syncing: 
            self.log_message('A sync is in progress')
            return False
        
        # Is free to use
        return True

    # Options
    async def download_albums(self):
        # Check if can use
        if not self.can_use(): return

        # Start syncing
        self.set_syncing(True)
        self.log_message('Starting to download albums...')

    async def download_metadata(self):
        # Check if can use
        if not self.can_use(): return

        # Start syncing
        self.set_syncing(True)
        self.log_message('Starting to download metadata...')

        # Create new queue
        queue = []

        # Check metadata files
        link: Link
        for index, link in enumerate(Library.links):
            # Get metadata path
            metadata_path = link.metadata_path

            # Check if metadata exists
            if not Util.exists_path(metadata_path):
                # Path does not exist -> Stop syncing
                self.set_syncing(False)
                self.log_message('Download cancelled, make sure all metadata files exist')
                return

            # Create item & add it to the queue
            item = QueueItem()
            item.album_index = index
            queue.append(item)

        # Update queue
        self.host.queue_index = -1
        self.host.queue = queue

        # Request next item
        await self.request_next_queue_metadata()

    async def upload_metadata(self):
        # Check if can use
        if not self.can_use(): return

        # Start syncing
        self.set_syncing(True)
        self.log_message('Starting to upload metadata...')

        # Check metadata files
        link: Link
        for link in Library.links:
            # Get metadata path
            metadata_path = link.metadata_path

            # Check if metadata exists
            if not Util.exists_path(metadata_path):
                # Path does not exist -> Stop syncing
                self.set_syncing(False)
                self.log_message('Upload cancelled, make sure all metadata files exist')
                return

        # Start metadata request
        await self.send(json.dumps({
            'action': 'startMetadataRequest'
        }))

from screens.sync.sync_server import SyncServer
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import Vertical, Horizontal, VerticalScroll

class SyncScreen(Screen):

    # Info
    TITLE = 'Sync'


    # Constructor
    def __init__(self):
        # Widgets
        self.w_info = None
        self.w_logs = None

        # Logs
        self.logs_count = 0

        # Init parent
        super().__init__()

    # State
    def on_mount(self):
        # Update server info
        self.update_info()

        # Show previous server logs
        for log in SyncServer.current.logs:
            self.log_message(log)

        # Register server events
        SyncServer.current.register_events(
            log_message=self.on_log_message, 
            server_state_changed=self.on_server_state_changed, 
            connection_state_changed=self.on_connection_state_changed
        )

    def on_unmount(self):
        # Unregister server events
        SyncServer.current.unregister_events(
            log_message=self.on_log_message, 
            server_state_changed=self.on_server_state_changed, 
            connection_state_changed=self.on_connection_state_changed
        )

    # Widgets
    def compose(self):
        # Create widgets
        self.w_info = Label(classes='box')
        self.w_logs = VerticalScroll(classes='box')

        # Create layout
        yield Header()
        with Horizontal():
            with Vertical():
                yield Button(classes='menu_button', id='back', label='Back', variant='error')
                with Vertical():
                    yield self.w_info
                    yield Button(classes='menu_button', id='start-server', label='Start server', tooltip='Starts the sync server if it\'s not running')
                    yield Label('Sync albums')
                    yield Button(classes='menu_button', id='download-albums', label='Download', tooltip='Updates the albums in this system with the ones in the client')
                    yield Label('Sync metadata')
                    yield Button(classes='menu_button', id='download-metadata', label='Download', tooltip='Updates the metadata in this system with the one in the client')
                    yield Button(classes='menu_button', id='upload-metadata', label='Upload', tooltip='Updates the metadata in the client with the one in this system')
            yield self.w_logs

    def update_info(self):
        # Get info
        is_running = '🟢' if SyncServer.current.is_running else '🔴'
        is_connected = '🟢' if SyncServer.current.is_connected else '🔴'
        connection_code = SyncServer.current.connection_code

        # Update info text
        self.w_info.content = f'· Server running: {is_running}\n· Client connected: {is_connected}\n· Code: {connection_code}'

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            # Back
            case 'back':
                self.app.pop_screen()
            # Start server
            case 'start-server':
                self.run_worker(SyncServer.current.start(), thread=True)
            # Download albums
            case 'download-albums':
                self.run_worker(SyncServer.current.download_albums, thread=True)
            # Download metadata
            case 'download-metadata':
                self.run_worker(SyncServer.current.download_metadata, thread=True)
            # Upload metadata
            case 'upload-metadata':
                self.run_worker(SyncServer.current.upload_metadata, thread=True)

    def on_log_message(self, error: str):
        # Log
        self.log_message_async(error)

    def on_server_state_changed(self, is_running: bool):
        self.update_info()

    def on_connection_state_changed(self, is_open: bool, client_ip: str):
        self.update_info()

    # Logs
    def log_message(self, message: str) -> Label:
        # Create label
        label = Label(message, classes='zebra_even' if self.logs_count % 2 == 0 else 'zebra_odd')
        self.logs_count += 1

        # Max logs
        if len(self.w_logs.children) >= 1000: self.w_logs.children[0].remove()

        # Add new log
        self.w_logs.mount(label)
        self.w_logs.scroll_end(animate=False)
        return label

    def log_message_async(self, message: str):
        self.app.call_from_thread(self.log_message, message)

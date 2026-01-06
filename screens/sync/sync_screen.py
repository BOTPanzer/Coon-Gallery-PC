from screens.sync.sync_server import SyncServer
from util.library import Library
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import Vertical, Horizontal, VerticalScroll

class SyncScreen(Screen):

    # Info
    TITLE = 'Sync'


    # Constructor
    def __init__(self):
        # Widgets
        self.w_content = None
        self.w_logs = None

        # Logs
        self.logs_count = 0

        # Options
        self.is_working = False

        # Init parent
        super().__init__()

    # State
    def on_mount(self):
        # Show previous server logs
        for log in SyncServer.current.logs:
            self.log_message(f'OLD: {log}')

        # Load albums
        self.load_albums()

        # Register server events
        SyncServer.current.register_events(log_message=self.on_log_message)

    def on_unmount(self):
        # Unregister server events
        SyncServer.current.unregister_events(log_message=self.on_log_message)

    # Screen
    def compose(self):
        # Create widgets
        self.w_content = Vertical()
        self.w_logs = VerticalScroll(classes='box')

        # Create layout
        yield Header()
        with Horizontal():
            with Vertical():
                yield Button(classes='menu_button', id='back', label='Back', variant='error')
                with self.w_content:
                    yield Label('Sync albums')
                    yield Button(classes='menu_button', id='download-albums', label='Download')
                    yield Label('Sync metadata')
                    yield Button(classes='menu_button', id='download-metadata', label='Download')
                    yield Button(classes='menu_button', id='upload-metadata', label='Upload')
            yield self.w_logs

    # Events (screen)
    def on_button_pressed(self, event: Button.Pressed):
        # Check if working
        if self.is_working: return

        # Check button
        match event.button.id:
            case 'back':
                self.app.pop_screen()

    def toggleContent(self, show: bool):
        # Toggle container
        self.w_content.visible = show

    # Events (server)
    def on_log_message(self, error: str):
        # Log
        self.log_message_async(error)

    # Albums
    def load_albums(self):
        # Load albums
        success: bool = Library.load_albums()

        # Check if success
        if success:
            self.log_message(f'Loaded {len(Library.albums)} albums successfully')
        else:
            self.log_message('Failed to load albums (please check all links in settings have existing paths)')
        self.toggleContent(success)

    # Logs
    def log_message(self, message: str) -> Label:
        # Create label
        label = Label(message, classes='log_even' if self.logs_count % 2 == 0 else 'log_odd')
        self.logs_count += 1

        # Max logs
        if len(self.w_logs.children) >= 1000: self.w_logs.children[0].remove()

        # Add new log
        self.w_logs.mount(label)
        self.w_logs.scroll_end(animate=False)
        return label

    def log_message_async(self, message: str):
        self.app.call_from_thread(self.log_message, message)

    # Options
    def set_working(self, working, message):
        self.is_working = working
        self.log_message(message)

    def set_working_async(self, working: bool, message: str):
        self.app.call_from_thread(self.set_working, working, message)

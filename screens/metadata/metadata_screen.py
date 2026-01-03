from util.album import Album
from util.filter import Filter
from util.dialog_input import InputDialog
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import Vertical, Horizontal, VerticalScroll

class MetadataScreen(Screen):

    # Info
    TITLE = 'Metadata'

    # Widgets
    w_content = None
    w_info = None
    w_logs = None

    # Albums
    albums: list[Album] = []


    # Init
    def on_mount(self):
        self.load_albums()

    # Screen
    def compose(self):
        # Create widgets
        self.w_content = Vertical()
        self.w_info = Label(classes='box')
        self.w_logs = VerticalScroll(classes='box')

        # Create layout
        yield Header()
        with Horizontal():
            with Vertical():
                yield Button(id='back', label='Back', variant='error')
                with self.w_content:
                    yield self.w_info
                    yield Button(id='search', label='Search')
                    yield Button(id='create', label='Create')
                    yield Button(id='clean', label='Clean')
                    yield Button(id='fix', label='Fix')
            yield self.w_logs

    def toggleContent(self, show: bool):
        # Toggle container
        self.w_content.visible = show

    # Events
    def on_button_pressed(self, event):
        match event.button.id:
            case 'back':
                self.app.pop_screen()
            case 'search':
                self.search()

    # Albums
    def load_albums(self):
        # Items info
        items_with_metadata = 0
        items_without_metadata = 0

        # Create albums from links
        for link in self.app.links:
            # Check if link is valid
            if not link.isValid(): 
                # Not valid -> Notify & hide content
                self.log_message('Failed to load albums (please check all link paths exist)')
                self.toggleContent(False)
                return

            # Create album
            album = Album(link, Filter.images)

            # Update items info & save album
            items_with_metadata += album.items_with_metadata
            items_without_metadata += album.items_without_metadata
            self.albums.append(album)

        # Update info
        self.w_info.content = f'· Items with metadata: {items_with_metadata}\n· Items without metadata: {items_without_metadata}'

        # Notify & show content
        self.log_message('Albums loaded succesfully')
        self.toggleContent(True)

    def search(self):
        # Create dialog event
        def handle_result(value: str):
            # Check value
            if value.strip() == '': return

            # Create found items count
            items_found = 0

            # Start search
            self.log_message(f'Searching for "{value}"...')
            
            # Create item found event
            def on_item_found(path):
                nonlocal items_found
                items_found += 1
                self.log_message(path)

            # Search albums
            for album in self.albums:
                # Search album
                album.search(value, on_item_found)

            # End search
            self.log_message(f'Found {items_found} items')

        # Create dialog
        self.app.push_screen(InputDialog(f'What do you wanna search?'), handle_result)

    # Logs
    def log_message(self, message: str) -> Label:
        label = Label(message)
        self.w_logs.mount(label)
        label.scroll_visible()
        return label

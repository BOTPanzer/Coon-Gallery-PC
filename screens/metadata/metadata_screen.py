from util.album import Album
from util.filter import Filter
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import Vertical

class MetadataScreen(Screen):

    # Info
    TITLE = 'Metadata'

    # Albums
    albums = []

    # Widgets
    content_container = None
    info_label = None


    # Init
    def on_mount(self):
        self.init_albums()

    # Screen
    def compose(self):
        # Create widgets
        self.content_container = Vertical()
        self.info_label = Label(classes='box')

        # Create layout
        yield Header()
        yield Button(id='back', label='Back', variant='error')
        with self.content_container:
            yield self.info_label
            yield Button(id='search', label='Search')
            yield Button(id='create', label='Create')
            yield Button(id='clean', label='Clean')
            yield Button(id='fix', label='Fix')

    def toggleContent(self, show: bool, error: str = ''):
        # Toggle container
        self.content_container.visible = show

        # Show error notification
        if error != '': self.app.notify(error)

    # Events
    def on_button_pressed(self, event):
        match event.button.id:
            case 'back':
                self.app.pop_screen()

    # Albums
    def init_albums(self):
        # Items info
        items_with_metadata = 0
        items_without_metadata = 0

        # Create albums from links
        for link in self.app.links:
            # Create album
            album = Album(link, Filter.images)

            # Check if is valid
            if not album.isValid: 
                # Not valid -> Show notification & stop
                self.toggleContent(False, 'Invalid paths, please check link paths exist')
                return

            # Update items info & save album
            items_with_metadata += len(album.items_with_metadata)
            items_without_metadata += len(album.items_without_metadata)
            self.albums.append(album)

        # Update info
        self.info_label.content = f'· Items with metadata: {items_with_metadata}\n· Items without metadata: {items_without_metadata}'

        # Show content
        self.toggleContent(True)

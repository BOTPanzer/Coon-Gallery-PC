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
    w_content = None
    w_info = None


    # Init
    def on_mount(self):
        self.load_albums()

    # Screen
    def compose(self):
        # Create widgets
        self.w_content = Vertical()
        self.w_info = Label(classes='box')

        # Create layout
        yield Header()
        yield Button(id='back', label='Back', variant='error')
        with self.w_content:
            yield self.w_info
            yield Button(id='search', label='Search')
            yield Button(id='create', label='Create')
            yield Button(id='clean', label='Clean')
            yield Button(id='fix', label='Fix')

    def toggleContent(self, show: bool, error: str = ''):
        # Toggle container
        self.w_content.visible = show

        # Show error notification
        if error != '': self.app.notify(error)

    # Events
    def on_button_pressed(self, event):
        match event.button.id:
            case 'back':
                self.app.pop_screen()

    # Albums
    def load_albums(self):
        # Items info
        items_with_metadata = 0
        items_without_metadata = 0

        # Create albums from links
        for link in self.app.links:
            # Check if link is valid
            if not link.isValid(): 
                # Not valid -> Notify & stop loading
                self.toggleContent(False, 'Please check all link paths exist')
                return

            # Create album
            album = Album(link, Filter.images)

            # Update items info & save album
            items_with_metadata += album.items_with_metadata
            items_without_metadata += album.items_without_metadata
            self.albums.append(album)

        # Update info
        self.w_info.content = f'· Items with metadata: {items_with_metadata}\n· Items without metadata: {items_without_metadata}'

        # Show content
        self.toggleContent(True)

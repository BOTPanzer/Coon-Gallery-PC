from util.link import Link
from textual.widgets import Static, Label, Button, Input
from textual.containers import Horizontal, Vertical
from collections.abc import Callable

class LinkItem(Static):

    # Constructor
    def __init__(self, link: Link, index: int, on_modify: Callable[[], None], on_remove: Callable[["LinkItem"], None]):
        super().__init__()
        # Save info
        self.link = link
        self.index = index
        self.on_modify = on_modify
        self.on_remove = on_remove

        # Save widgets
        self.w_name = None
        self.w_remove = None
        self.w_album = None
        self.w_metadata = None

    # Widget
    def compose(self):
        # Create widgets
        self.w_name = Label(f'Link {self.index}')
        self.w_remove = Button(id='remove-link', label='Remove', variant='error')
        self.w_album = Input(id='album', placeholder="Album folder path", value=self.link.album_path)
        self.w_metadata = Input(id='metadata', placeholder='Metadata file path', value=self.link.metadata_path)

        # Create layout
        with Vertical():
            yield self.w_name
            with Horizontal():
                yield self.w_remove
                with Vertical():
                    yield self.w_album
                    yield self.w_metadata

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        event.stop()            # Stop the event from bubbling up to the screen
        self.removed = True     # Mark as removed
        self.on_remove(self)    # Call on remove

    def on_input_changed(self, event: Input.Changed) -> None:
        match event.input.id:
            case 'album':
                self.link.album_path = event.value
            case 'metadata':
                self.link.metadata_path = event.value
        self.on_modify()

    # Updating index
    def update_index(self, new_index: int):
        self.index = new_index
        self.w_name.content = f'Link {self.index}'
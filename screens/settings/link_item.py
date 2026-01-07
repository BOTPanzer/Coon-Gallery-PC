from util.library import Link
from textual.widgets import Static, Label, Button, Input
from textual.containers import Horizontal, Vertical
from collections.abc import Callable
import tkinter as tk
from tkinter import filedialog

class LinkItem(Static):

    # Constructor
    def __init__(self, link: Link, index: int, on_modify: Callable[[], None], on_remove: Callable[["LinkItem"], None]):
        # Init info
        self.link: Link = link
        self.index: int = index
        self.on_modify: Callable[[], None] = on_modify
        self.on_remove: Callable[[LinkItem], None] = on_remove

        # Init parent
        super().__init__()

    # Widget
    def compose(self):
        # Create widgets
        self.w_name = Label(f'Link {self.index}')
        self.w_input_album = Input(id='album', classes='path', placeholder="Album folder path", value=self.link.album_path)
        self.w_input_metadata = Input(id='metadata', classes='path', placeholder='Metadata file path', value=self.link.metadata_path)

        # Create layout
        with Vertical():
            yield self.w_name
            with Horizontal():
                yield Button(id='remove-link', label='Remove', variant='error')
                with Vertical():
                    with Horizontal():
                        yield self.w_input_album
                        yield Button(id='select-album', classes='folder', label='📁')
                    with Horizontal():
                        yield self.w_input_metadata
                        yield Button(id='select-metadata', classes='folder', label='📁')

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case 'remove-link':
                event.stop()            # Stop the event from bubbling up to the screen
                self.removed = True     # Mark as removed
                self.on_remove(self)    # Call on remove
            case 'select-album':
                # Open explorer
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True) # Bring to front
                folder_path = filedialog.askdirectory()
                root.destroy()

                # Update input
                if folder_path: self.w_input_album.value = folder_path
            case 'select-metadata':
                # Open explorer
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True) # Bring to front
                file_path = filedialog.askopenfilename()
                root.destroy()

                # Update input
                if file_path: self.w_input_metadata.value = file_path

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
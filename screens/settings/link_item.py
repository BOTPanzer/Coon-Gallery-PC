from util.dialogs import ConfirmDialog, InputDialog
from util.library import Link
from util.util import Util
from textual.widgets import Static, Label, Button, Input
from textual.containers import Horizontal, Vertical
from collections.abc import Callable

class LinkItem(Static):

    # Constructor
    def __init__(self, link: Link, index: int, on_modify: Callable[[], None], on_remove: Callable[["LinkItem"], None]):
        # Init info
        self.link: Link = link
        self.index: int = index
        self.on_modify: Callable[[], None] = on_modify
        self.on_remove: Callable[[LinkItem], None] = on_remove
        self.is_removed: bool = False

        # Init parent
        super().__init__()

    # Widget
    def compose(self):
        # Create widgets
        self.w_container = Vertical()
        self.w_name = Label(content=f'Link {self.index}')
        self.w_input_album = Input(id='album', classes='link_path', placeholder="Album folder path", value=self.link.album_path)
        self.w_input_metadata = Input(id='metadata', classes='link_path', placeholder='Metadata file path', value=self.link.metadata_path)

        # Create layout
        with self.w_container:
            yield self.w_name
            with Horizontal():
                yield Button(id='remove-link', classes='link_button', label='X', variant='error', tooltip='Delete link')
                with Vertical():
                    with Horizontal():
                        yield Button(id='select-album', classes='link_button link_folder', label='📁', tooltip='Select album folder')
                        yield self.w_input_album
                    with Horizontal():
                        yield Button(id='select-metadata', classes='link_button link_folder', label='📁', tooltip='Select metadata file')
                        yield self.w_input_metadata

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            # Delete link
            case 'remove-link':
                self.on_remove(self)
            # Select album folder
            case 'select-album':
                self.folder_album()
            # Create/Select metadata file
            case 'select-metadata':
                self.folder_metadata()

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

    # Folders
    def folder_album(self):
        # Ask for a folder
        folder_path = Util.ask_for_folder('Select an album folder')

        # Update input
        if folder_path: self.w_input_album.value = folder_path

    def folder_metadata(self):
        # Create result event
        def on_result(select: bool):
            # Check if should create or select
            if select:
                # Ask for a file
                file_path = Util.ask_for_file('Select a metadata file')

                # Update input
                if file_path: self.w_input_metadata.value = file_path
            else:
                # Ask for file name
                def on_result(file_name: str):
                    # Check if canceled
                    if file_name == None: 
                        return

                    # Check if value is empty
                    if len(file_name) <= 0: 
                        self.app.notify('Name can\'t be empty')
                        return

                    # Ask for a folder
                    folder_path = Util.ask_for_folder('Where do you want to save your file?')

                    # Check if folder is valid
                    if not folder_path: return

                    # Create file path
                    file_path = Util.join_path(folder_path, f'{file_name}.json')

                    # Check if file path exists
                    if Util.exists_path(file_path):
                        self.app.notify('A file with that name already exists')
                        return

                    # Create file
                    with open(file_path, 'w') as f:
                        f.write('{}')

                    # Update input
                    self.w_input_metadata.value = file_path

                # Create dialog
                self.app.push_screen(InputDialog(placeholder='Name your file', confirm='Create'), on_result)

        # Create dialog
        self.app.push_screen(ConfirmDialog(title='Would you like to create or select a metadata file?', cancel='Create', confirm='Select'), on_result)

        
from util.album import Album
from util.filter import Filter
from util.dialog_input import InputDialog
from util.metadata import Metadata
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

    # Logs
    logs_count = 0

    # Albums
    albums: list[Album] = []

    # Options
    is_working = False


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
                yield Button(classes='menu_button', id='back', label='Back', variant='error')
                with self.w_content:
                    yield self.w_info
                    yield Button(classes='menu_button', id='search', label='Search albums', tooltip='Searches for items whose metadata contains a specified input')
                    yield Button(classes='menu_button', id='clean', label='Clean metadata', tooltip='Removes metadata keys whose file does not exist & sorts the remaining by modified date')
                    yield Button(classes='menu_button', id='fix', label='Fix metadata', tooltip='Creates metadata for all missing files or fields')
            yield self.w_logs

    def toggleContent(self, show: bool):
        # Toggle container
        self.w_content.visible = show

    # Events
    async def on_button_pressed(self, event: Button.Pressed):
        # Check if working
        if self.is_working: return

        # Check button
        match event.button.id:
            case 'back':
                self.app.pop_screen()
            case 'search':
                await self.option_search()
            case 'clean':
                await self.option_clean()
            case 'fix':
                await self.option_fix()

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

    # Albums
    def load_albums(self):
        # Reset albums
        self.albums = []

        # Create items info
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

    # Options
    def set_working(self, working, message):
        self.is_working = working
        self.log_message(message)

    async def option_search(self):
        # Create result event
        def on_result(value: str):
            # Check if canceled
            if value.strip() == '': 
                return

            # Check if value is long enough
            if len(value) <3: 
                self.log_message('Search must be at least 3 characters long')
                return

            # Start search
            self.set_working(True, f'Searching for "{value}"...')

            # Execute in another thread to not block UI
            self.run_worker(self.execute_option_search(value), thread=True)

        # Create dialog
        self.app.push_screen(InputDialog(f'What do you wanna search?'), on_result)

    async def execute_option_search(self, value: str):
        # Create found items count
        items_found = 0

        # Create item found event
        def on_item_found(path):
            nonlocal items_found
            items_found += 1
            self.app.call_from_thread(self.log_message, path)

        # Search albums
        for album in self.albums:
            # Search album
            album.search(value, on_item_found)

        # Finish search
        self.app.call_from_thread(self.set_working, False, f'Found {items_found} items')

    async def option_clean(self):
        # Start cleaning
        self.set_working(True, 'Cleaning albums metadata...')

        # Execute in another thread to not block UI
        self.run_worker(self.execute_option_clean, thread=True)

    async def execute_option_clean(self):
        # Sort & save albums metadata
        for album_index, album in enumerate(self.albums):
            # Clean album metadata
            self.app.call_from_thread(self.log_message, f'Album {album_index}: Cleaning...')
            album.clean_metadata()

            # Save album metadata
            self.app.call_from_thread(self.log_message, f'Album {album_index}: Saving...')
            album.save_metadata()

        # Finish cleaning
        self.app.call_from_thread(self.set_working, False, 'Finished cleaning albums metadata')

    async def option_fix(self):
        # Start fixing
        self.set_working(True, 'Fixing albums metadata...')

        # Execute in another thread to not block UI
        self.run_worker(self.execute_option_fix, thread=True)

    async def execute_option_fix(self):
        # Loop albums
        for album_index, album in enumerate(self.albums):
            self.app.call_from_thread(self.log_message, f'Album {album_index}: Checking...')
            album_metadata_modified = False

            # Loop album items
            for item_name in album.items:
                # Get metadata
                item_metadata = album.get_item_metadata(item_name)
                item_metadata_modified = False

                # Check if metadata has caption
                if not Metadata.has_valid_caption(item_metadata):
                    # Generate caption
                    self.app.call_from_thread(self.log_message, f'{item_name}: Generating caption...')

                    # Mark item metadata as modified
                    item_metadata_modified = True

                # Check if metadata has labels
                if not Metadata.has_valid_labels(item_metadata):
                    # Generate labels
                    self.app.call_from_thread(self.log_message, f'{item_name}: Generating labels...')

                    # Mark item metadata as modified
                    item_metadata_modified = True

                # Check if metadata has text
                if not Metadata.has_valid_text(item_metadata):
                    # Generate text
                    self.app.call_from_thread(self.log_message, f'{item_name}: Generating text...')

                    # Mark item metadata as modified
                    item_metadata_modified = True

                # Check if item metadata was modified
                if item_metadata_modified:
                    # Save item metadata
                    album.metadata[item_name] = item_metadata

                    # Mark album metadata as modified
                    album_metadata_modified = True

            # Check if album metadata was modified
            if album_metadata_modified:
                # Save album metadata
                self.app.call_from_thread(self.log_message, f'Album {album_index}: Saving...')
                album.save_metadata()

        # Finish fixing
        self.app.call_from_thread(self.set_working, False, 'Finished fixing albums metadata')
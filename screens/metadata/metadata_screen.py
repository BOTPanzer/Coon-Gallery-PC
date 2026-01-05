from util.metadata import Metadata, Album, Item, Filter
from util.dialogs import InputDialog
from util.ai import DescriptionModel, TextModel
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import Vertical, Horizontal, VerticalScroll
from PIL import Image

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
                self.log_message('Failed to load albums (please check all links in settings have existing paths)')
                self.toggleContent(False)
                return

            # Create album
            album = Album(link, Filter.images)

            # Update items info & save album
            items_with_metadata += album.items_with_metadata
            items_without_metadata += album.items_without_metadata
            self.albums.append(album)

        # Update albums info
        self.update_albums_info(items_with_metadata, items_without_metadata)

        # Notify & show content
        self.log_message('Albums loaded succesfully')
        self.toggleContent(True)

    def update_albums_info(self, items_with_metadata, items_without_metadata):
        # Update info text
        self.w_info.content = f'· Items with metadata: {items_with_metadata}\n· Items without metadata: {items_without_metadata}'

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
        # Stats
        items_total = 0
        items_fixed = 0

        # Models
        description_model = None
        text_model = None

        def init_description_model():
            # Check if is init
            nonlocal description_model
            if description_model != None: return

            # Load
            self.app.call_from_thread(self.log_message, 'Loading description model...')
            description_model = DescriptionModel()

        def init_text_model():
            # Check if is init
            nonlocal text_model
            if text_model != None: return

            # Load
            self.app.call_from_thread(self.log_message, 'Loading text model...')
            text_model = TextModel()

        # Loop albums
        for album_index, album in enumerate(self.albums):
            self.app.call_from_thread(self.log_message, f'Album {album_index}: Checking...')
            items_total += len(album.items)
            album_metadata_modified = False

            # Loop album items
            item: Item
            for item in album.items:
                # Get info
                item_metadata = album.get_item_metadata(item.name)
                item_metadata_modified = False

                # Image
                item_image = None

                def init_item_image():
                    # Check if is init
                    nonlocal item_image
                    if item_image != None: return

                    # Load
                    item_image = Image.open(item.path)

                # Check if metadata has caption
                if not Metadata.has_valid_caption(item_metadata):
                    # Make sure description model & image are init
                    init_description_model()
                    init_item_image()

                    # Generate caption
                    self.app.call_from_thread(self.log_message, f'{item.name}: Generating caption...')
                    item_metadata['caption'] = description_model.generate_caption(item_image)

                    # Mark item metadata as modified
                    item_metadata_modified = True

                # Check if metadata has labels
                if not Metadata.has_valid_labels(item_metadata):
                    # Make sure description model & image are init
                    init_description_model()
                    init_item_image()

                    # Generate labels
                    self.app.call_from_thread(self.log_message, f'{item.name}: Generating labels...')
                    item_metadata['labels'] = description_model.generate_labels(item_image)

                    # Mark item metadata as modified
                    item_metadata_modified = True

                # Check if metadata has text
                if not Metadata.has_valid_text(item_metadata):
                    # Make sure text model & image are init
                    init_text_model()
                    init_item_image()

                    # Generate text
                    self.app.call_from_thread(self.log_message, f'{item.name}: Generating text...')
                    item_metadata['text'] = text_model.detect_text(item_image)

                    # Mark item metadata as modified
                    item_metadata_modified = True

                # Check if item metadata was modified
                if item_metadata_modified:
                    # Save item metadata
                    album.set_item_metadata(item.name, item_metadata)

                    # Mark item as fixed
                    items_fixed += 1

                    # Mark album metadata as modified
                    album_metadata_modified = True

            # Check if album metadata was modified
            if album_metadata_modified:
                # Clean album metadata
                self.app.call_from_thread(self.log_message, f'Album {album_index}: Cleaning...')
                album.clean_metadata() # Cleaning sorts the keys too

                # Save album metadata
                self.app.call_from_thread(self.log_message, f'Album {album_index}: Saving...')
                album.save_metadata()

        # Update albums info
        self.update_albums_info(items_total, 0)

        # Finish fixing
        self.app.call_from_thread(self.set_working, False, f'Finished fixing albums metadata (fixed {items_fixed})')
from util.ai import DescriptionModel, TextModel
from util.dialogs import InputDialog
from util.library import MetadataUtil, Item, Filter, Album, Library
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import Vertical, Horizontal, VerticalScroll
from PIL import Image, ImageFile

class MetadataScreen(Screen):

    # Info
    TITLE = 'Metadata'


    # Constructor
    def __init__(self):
        # Widgets
        self.w_content = None
        self.w_info = None
        self.w_logs = None

        # Albums
        self.albums: list[Album] = []

        # Logs
        self.logs_count = 0

        # Options
        self.is_working = False

        # Init parent
        super().__init__()

    # State
    def on_mount(self):
        # Load albums
        self.load_albums()

    # Widgets
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

    def toggle_content(self, show: bool):
        # Toggle container
        self.w_content.visible = show

    def update_info(self, items_with_metadata, items_without_metadata):
        # Update info text
        self.w_info.content = f'· Items with metadata: {items_with_metadata}\n· Items without metadata: {items_without_metadata}'

    # Events
    async def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            # Back
            case 'back':
                if self.is_working: 
                    self.app.notify('Can\'t exit until the current action finishes')
                else:
                    self.app.pop_screen()
            # Search albums
            case 'search':
                if self.is_working: 
                    self.app.notify('Wait until the current action finishes')
                else:
                    await self.option_search()
            # Clean metadata
            case 'clean':
                if self.is_working: 
                    self.app.notify('Wait until the current action finishes')
                else:
                    await self.option_clean()
            # Fix metadata
            case 'fix':
                if self.is_working: 
                    self.app.notify('Wait until the current action finishes')
                else:
                    await self.option_fix()

    # Albums
    def load_albums(self):
        # Load albums
        success: bool
        (success, self.albums) = Library.load_albums(Filter.images)

        # Check if success
        if success:
            self.log_message(f'Loaded {len(self.albums)} albums successfully')
        else:
            self.log_message('Failed to load albums (please check all links in settings have existing paths)')
        self.toggle_content(success)

        # Update albums info
        items_with_metadata: int = 0
        items_without_metadata: int = 0
        for album in self.albums:
            items_with_metadata += album.items_with_metadata
            items_without_metadata += album.items_without_metadata
        self.update_info(items_with_metadata, items_without_metadata)

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

    # Options
    def set_working(self, working: bool, message: str):
        self.is_working = working
        self.log_message(message)

    def set_working_async(self, working: bool, message: str):
        self.app.call_from_thread(self.set_working, working, message)

    async def option_search(self):
        # Create result event
        def on_result(value: str):
            # Check if canceled
            if value == None: 
                return

            # Check if value is long enough
            if len(value) <3: 
                self.app.notify('Search must be at least 3 characters long')
                return

            # Start search
            self.set_working(True, f'Searching for "{value}"...')

            # Execute in another thread to not block UI
            self.run_worker(self.execute_option_search(value), thread=True)

        # Create dialog
        self.app.push_screen(InputDialog(placeholder='What do you want to search?', confirm='Search'), on_result)

    async def execute_option_search(self, value: str):
        # Create found items count
        items_found: int = 0

        # Create item found event
        def on_item_found(path):
            nonlocal items_found
            items_found += 1
            self.log_message_async(path)

        # Search albums
        for album in self.albums:
            # Search album
            album.search(value, on_item_found)

        # Finish search
        self.set_working_async(False, f'Found {items_found} items')

    async def option_clean(self):
        # Start cleaning
        self.set_working(True, 'Cleaning albums metadata...')

        # Execute in another thread to not block UI
        self.run_worker(self.execute_option_clean, thread=True)

    async def execute_option_clean(self):
        # Clean & save albums metadata
        album: Album
        for album_index, album in enumerate(self.albums):
            # Clean & save album metadata
            self.log_message_async(f'Album {album_index}: Cleaning & saving...')
            album.clean_metadata()
            album.save_metadata()

        # Finish cleaning
        self.set_working_async(False, 'Finished cleaning albums metadata')

    async def option_fix(self):
        # Start fixing
        self.set_working(True, 'Fixing albums metadata...')

        # Execute in another thread to not block UI
        self.run_worker(self.execute_option_fix, thread=True)

    async def execute_option_fix(self):
        # Stats
        total_items_count: int = 0
        total_items_fixed: int = 0

        # Saving
        save_every: int = 5

        # Models
        description_model: DescriptionModel = None
        text_model: TextModel = None

        def init_description_model():
            # Check if is init
            nonlocal description_model
            if description_model != None: return

            # Load
            self.log_message_async('Loading description model (this may take a while)...')
            description_model = DescriptionModel()

        def init_text_model():
            # Check if is init
            nonlocal text_model
            if text_model != None: return

            # Load
            self.log_message_async('Loading text model...')
            text_model = TextModel()

        # Loop albums
        album: Album
        for album_index, album in enumerate(self.albums):
            self.log_message_async(f'Album {album_index}: Checking...')

            # Stats
            album_items_count: int = len(album.items)
            album_items_fixed: int = 0
            total_items_count += album_items_count

            # Saving
            was_album_modified: bool = False
            was_album_saved: bool = False

            # Loop album items
            item: Item
            for item_index, item in enumerate(album.items):
                # Metadata
                was_item_modified: bool = False
                item_metadata: dict = album.get_item_metadata(item.name)

                # Check if item needs fixing
                fix_caption: bool = not MetadataUtil.has_valid_caption(item_metadata)
                fix_labels: bool = not MetadataUtil.has_valid_labels(item_metadata)
                fix_text: bool = not MetadataUtil.has_valid_text(item_metadata)

                if not fix_caption and not fix_labels and not fix_text: continue

                # Check if description model is needed
                if fix_caption or fix_labels:
                    # Is needed -> Make sure its init
                    init_description_model()

                    # Load image
                    item_image: ImageFile = Image.open(item.path).convert("RGB")

                    # Fix caption
                    if fix_caption:
                        # Generate caption
                        self.log_message_async(f'{item.name}: Generating caption...')
                        item_metadata['caption'] = description_model.generate_caption(item_image)

                    # Fix labels
                    if fix_labels:
                        # Generate labels
                        self.log_message_async(f'{item.name}: Generating labels...')
                        item_metadata['labels'] = description_model.generate_labels(item_image)

                    # Mark item as modified
                    was_item_modified = True

                # Check if text model is needed
                if fix_text:
                    # Is needed -> Make sure its init
                    init_text_model()

                    # Generate text
                    self.log_message_async(f'{item.name}: Generating text...')
                    item_metadata['text'] = text_model.detect_text(item.path)

                    # Mark item as modified
                    was_item_modified = True

                # Check if item was modified
                if was_item_modified:
                    # Update item metadata
                    album.set_item_metadata(item.name, item_metadata)

                    # Mark item as fixed
                    album_items_fixed += 1
                    total_items_fixed += 1

                    # Mark album as modified
                    was_album_modified = True

                    # Save every x items and if item isn't the last of the album
                    if (album_items_fixed % save_every == 0) and (item_index < album_items_count - 1):
                        # Save album metadata
                        self.log_message_async(f'Album {album_index}: Saving (fast save)...')
                        album.save_metadata(backup=not was_album_saved) # Create backup only first save

                        # Mark album as saved
                        was_album_saved = True

            # Check if album was modified
            if was_album_modified:
                # Clean & save album metadata
                self.log_message_async(f'Album {album_index}: Cleaning & saving...')
                album.clean_metadata() # Cleaning sorts the keys too
                album.save_metadata(backup=not was_album_saved) # Create backup only first save

        # Update albums info
        self.update_info(total_items_count, 0)

        # Finish fixing
        self.set_working_async(False, f'Finished fixing albums metadata (fixed {total_items_fixed})')
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

    # Logs
    logs_count = 0

    # Metadata
    is_working = False
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
    def set_working(self, working):
        self.is_working = working

    async def option_search(self):
        # Create result event
        def on_result(value: str):
            # Check if canceled
            if value.strip() == '': return

            # Check if value is long enough
            if len(value) <3: 
                self.log_message('Search must be at least 3 characters long')
                return

            # Execute in another thread to not block UI
            self.run_worker(self.execute_option_search(value), thread=True)

        # Create dialog
        self.app.push_screen(InputDialog(f'What do you wanna search?'), on_result)

    async def execute_option_search(self, value: str):
        # Start search
        self.app.call_from_thread(self.set_working, True)
        self.app.call_from_thread(self.log_message, f'Searching for "{value}"...')

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
        self.app.call_from_thread(self.log_message, f'Found {items_found} items')
        self.app.call_from_thread(self.set_working, False)

    async def option_clean(self):
        # Execute in another thread to not block UI
        self.run_worker(self.execute_option_clean, thread=True)

    async def execute_option_clean(self):
        # Start cleaning
        self.app.call_from_thread(self.set_working, True)
        self.app.call_from_thread(self.log_message, 'Cleaning albums...')

        # Sort & save albums metadata
        for index, album in enumerate(self.albums):
            self.app.call_from_thread(self.log_message, f'Cleaning album {index}...')
            album.sort_and_clean_metadata()
            self.app.call_from_thread(self.log_message, f'Saving album {index}...')
            album.save_metadata()

        # Finish cleaning
        self.app.call_from_thread(self.log_message, 'Finished cleaning albums')
        self.app.call_from_thread(self.set_working, False)

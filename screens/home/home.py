from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label
from screens.settings.settings import SettingsScreen
from screens.sync.sync import SyncScreen
from screens.gallery.gallery import GalleryScreen

class HomeScreen(Screen):
    
    # Info
    TITLE = 'Coon Gallery'


    # Screen
    def compose(self):
        # Create layout
        yield Header()
        yield Button(id='exit', label='Exit', variant='error')
        yield Label('Menus')
        yield Button(id='settings', label='Settings')
        yield Button(id='gallery', label='Gallery')
        yield Button(id='sync', label='Sync')

    # Events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case 'exit':
                self.app.exit()
            case 'settings':
                self.app.push_screen(SettingsScreen())
            case 'gallery':
                self.app.push_screen(GalleryScreen())
            case 'sync':
                self.app.push_screen(SyncScreen())
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from screens.settings.settings_screen import SettingsScreen
from screens.sync.sync_screen import SyncScreen
from screens.metadata.metadata_screen import MetadataScreen

class HomeScreen(Screen):

    # Info
    TITLE = 'Coon Gallery'


    # Screen
    def compose(self):
        # Create layout
        yield Header()
        yield Button(id='exit', label='Exit', variant='error')
        yield Button(id='settings', label='Settings')
        yield Button(id='metadata', label='Metadata')
        yield Button(id='sync', label='Sync')

    # Events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case 'exit':
                self.app.exit()
            case 'settings':
                self.app.push_screen(SettingsScreen())
            case 'metadata':
                self.app.push_screen(MetadataScreen())
            case 'sync':
                self.app.push_screen(SyncScreen())
from textual.screen import Screen
from textual.widgets import Header, Label, Button
from screens.settings.settings_screen import SettingsScreen
from screens.sync.sync_screen import SyncScreen
from screens.sync.sync_server import SyncServer
from screens.metadata.metadata_screen import MetadataScreen

class HomeScreen(Screen):

    # Info
    TITLE = 'Home'


    # Widgets
    def compose(self):
        # Create layout
        yield Header()
        yield Label("""
   ___                        ___         _   _                  
  /  _)                      /  _)       | | | |                 
 |      __   __   _  _      |    _  __,  | | | |  _   ,_         
 |     /  \_/  \_/ |/ |     |     |/  |  |/  |/  |/  /  |  |   | 
  \___/\__/ \__/   |  |_/    \___/ \_/|_/|__/|__/|__/   |_/ \_/|_/
                                                            /| 
                                                            \| 
        """)
        yield Button(classes='menu_button', id='exit', label='Exit', variant='error')
        yield Button(classes='menu_button', id='settings', label='Settings')
        yield Button(classes='menu_button', id='metadata', label='Metadata')
        yield Button(classes='menu_button', id='sync', label='Sync')

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            # Exit
            case 'exit':
                self.app.exit()
            # Settings menu
            case 'settings':
                self.app.push_screen(SettingsScreen())
            # Metadata menu
            case 'metadata':
                if SyncServer.current.is_syncing: 
                    self.app.notify('Can\'t open metadata menu while syncing with phone')
                else:
                    self.app.push_screen(MetadataScreen())
            # Sync menu
            case 'sync':
                self.app.push_screen(SyncScreen())
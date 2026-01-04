from textual.screen import Screen
from textual.widgets import Header, Button, Label

class SyncScreen(Screen):

    # Info
    TITLE = 'Sync'
    
    
    # Screen
    def compose(self):
        # Create layout
        yield Header()
        yield Button(id='back', label='Back', variant='error')
        yield Label('Sync albums')
        yield Button(id='download-albums', label='Download')
        yield Label('Sync metadata')
        yield Button(id='download-metadata', label='Download')
        yield Button(id='upload-metadata', label='Upload')

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case 'back':
                self.app.pop_screen()
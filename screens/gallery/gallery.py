from textual.screen import Screen
from textual.widgets import Header, Button, Label

class GalleryScreen(Screen):

    # Info
    TITLE = 'Gallery'
    
    # Layout
    def compose(self):
        # Create layout
        yield Header()
        yield Button(id='back', label='Back', variant='error')
        yield Label('Gallery')
        yield Button(id='search', label='Search')
        yield Label("Metadata")
        yield Button(id='create', label='Create')
        yield Button(id='clean', label='Clean')
        yield Button(id='fix', label='Fix')

    # Events
    def on_button_pressed(self, event):
        match event.button.id:
            case 'back':
                self.app.pop_screen()
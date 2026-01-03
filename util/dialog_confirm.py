from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label

class ConfirmDialog(ModalScreen[bool]):
    
    # Init
    def __init__(self, title: str = "Are you sure?"):
        self.title_text = title
        super().__init__()

    # Widget
    def compose(self):
        with Grid(id="dialog"):
            yield Label(content=self.title_text)
            yield Button(id="dialog-cancel", label="Cancel")
            yield Button(id="dialog-confirm", label="Confirm")

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "dialog-cancel":
            self.dismiss(False)
        else:
            self.dismiss(True)
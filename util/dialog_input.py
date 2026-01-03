from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Input

class InputDialog(ModalScreen[str]):
    
    # Init
    def __init__(self, placeholder: str = "Type here"):
        self.placeholder_text = placeholder
        super().__init__()

    # Widget
    def compose(self):
        # Create widgets
        self.w_input = Input(placeholder=self.placeholder_text)

        # Create layout
        with Grid(id="dialog"):
            yield self.w_input
            yield Button(id="dialog-cancel", label="Cancel")
            yield Button(id="dialog-confirm", label="Confirm")

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "dialog-cancel":
            self.dismiss('')
        else:
            self.dismiss(self.w_input.value)
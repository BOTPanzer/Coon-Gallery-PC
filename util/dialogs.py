from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label, Input

# Alert dialog
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

# Text input dialog
class InputDialog(ModalScreen[str]):

    # Init
    def __init__(self, placeholder: str = "Type here", value: str = ""):
        self.placeholder_text = placeholder
        self.value_text = value
        super().__init__()

    # Widget
    def compose(self):
        # Create widgets
        self.w_input = Input(placeholder=self.placeholder_text, value=self.value_text)

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
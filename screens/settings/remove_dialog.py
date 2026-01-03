from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label

class RemoveDialog(ModalScreen[bool]):

    # Widget
    def compose(self):
        with Grid(id="dialog"):
            yield Label(id="dialog-question", content="Remove link?")
            yield Button(id="dialog-cancel", label="Cancel")
            yield Button(id="dialog-confirm", label="Confirm")

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "dialog-cancel":
            self.dismiss(False)
        else:
            self.dismiss(True)
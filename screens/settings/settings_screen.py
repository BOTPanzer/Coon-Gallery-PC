from util.link import Link
from util.dialog_confirm import ConfirmDialog
from screens.settings.link_item import LinkItem
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import VerticalScroll

class SettingsScreen(Screen):

    # Info
    TITLE = 'Settings'

    # Widgets
    w_links = None


    # Screen
    def compose(self):
        # Create widgets
        self.w_links = VerticalScroll(id='links-list')

        # Create layout
        yield Header()
        yield Button(id='back', label='Back', variant='error')
        yield Label(classes='box', content='Link are formed by an album folder and its metadata file\n· Add an album folder to enable backing it up\n· Add a metadata file to enable generating metadata for its album\n\nNote: Make sure you add links in the same order as in the phone app')
        yield Button(id='add-link', label='Add link')
        with self.w_links:
            for index, link in enumerate(self.app.links):
                yield self.create_link_item(index, link)

    # Events
    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case 'back':
                self.app.pop_screen()
            case 'add-link':
                self.add_link()

    # Links
    def create_link_item(self, index: int, link: Link):
        return LinkItem(link, index, on_modify=self.app.save_links, on_remove=lambda link_item: self.remove_link(link_item))

    def add_link(self):
        # Add link to list
        link = Link()
        index = self.app.add_link(link)

        # Add link item to container
        link_item = self.create_link_item(index, link)
        self.w_links.mount(link_item)
        link_item.scroll_visible()

    def remove_link(self, link_item: LinkItem):
        # Create result event
        def on_result(remove: bool):
            # Don't remove
            if not remove: return

            # Remove link
            self.app.remove_link(link_item.link)
            link_item.remove() # Remove widget from UI

            # Update link items
            remaining_items = [ child for child in self.w_links.query(LinkItem) if not getattr(child, 'removed', False) ]
            for index, item in enumerate(remaining_items):
                item.update_index(index)

        # Create dialog
        self.app.push_screen(ConfirmDialog(f'Are you sure you want to remove Link {link_item.index}?'), on_result)
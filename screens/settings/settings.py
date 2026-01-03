from util.link import Link
from screens.settings.link_item import LinkItem
from textual.screen import Screen
from textual.widgets import Header, Button, Label
from textual.containers import VerticalScroll

# Screen
class SettingsScreen(Screen):

    # Info
    TITLE = 'Settings'

    # Widgets
    links_container = None


    # Screen
    def compose(self):
        # Create widgets
        self.links_container = VerticalScroll()

        # Create layout
        yield Header()
        yield Button(id='back', label='Back', variant='error')
        yield Label('Links')
        with self.links_container:
            for index, link in enumerate(self.app.links):
                yield self.create_link_item(index, link)
        yield Button(id='add-link', label='Add link')

    # Events
    def on_button_pressed(self, event):
        match event.button.id:
            case 'back':
                self.app.pop_screen()
            case 'add-link':
                self.add_link()

    # Links
    def create_link_item(self, index: int, link: Link):
        return LinkItem(link, index, on_modify=self.app.save_links, on_remove=lambda: self.remove_link(link))

    def add_link(self):
        # Add link to list
        link = Link()
        index = self.app.add_link(link)

        # Add link item to container
        link_item = self.create_link_item(index, link)
        self.links_container.mount(link_item)
        link_item.scroll_visible()

    def remove_link(self, link: Link):
        # Remove link
        self.app.remove_link(link)

        # Update link items
        remaining_items = [ child for child in self.links_container.query(LinkItem) if not getattr(child, 'removed', False) ]
        for index, item in enumerate(remaining_items):
            item.update_index(index)
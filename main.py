from util.link import Link
from util.util import Util
from textual.app import App
from screens.home.home import HomeScreen
import pathlib
import os

class CoonGallery(App):

    #   /$$$$$$
    #  /$$__  $$
    # | $$  \ $$  /$$$$$$   /$$$$$$
    # | $$$$$$$$ /$$__  $$ /$$__  $$
    # | $$__  $$| $$  \ $$| $$  \ $$
    # | $$  | $$| $$  | $$| $$  | $$
    # | $$  | $$| $$$$$$$/| $$$$$$$/
    # |__/  |__/| $$____/ | $$____/
    #           | $$      | $$
    #           | $$      | $$
    #           |__/      |__/

    CSS_PATH = "styles.tcss"

    # Init
    def on_mount(self):
        # Load links
        self.load_links()

        # Start HomeScreen
        self.push_screen(HomeScreen())


    #  /$$       /$$           /$$
    # | $$      |__/          | $$
    # | $$       /$$ /$$$$$$$ | $$   /$$  /$$$$$$$
    # | $$      | $$| $$__  $$| $$  /$$/ /$$_____/
    # | $$      | $$| $$  \ $$| $$$$$$/ |  $$$$$$
    # | $$      | $$| $$  | $$| $$_  $$  \____  $$
    # | $$$$$$$$| $$| $$  | $$| $$ \  $$ /$$$$$$$/
    # |________/|__/|__/  |__/|__/  \__/|_______/

    linksPath = os.path.join(pathlib.Path().resolve(), 'data', 'links.json')
    links = []

    def load_links(self):
        # Load links save from file
        save = Util.load_json(self.linksPath)

        # Parse save
        self.links = [ Link(item["album_path"], item["metadata_path"]) for item in save ]

    def save_links(self):
        # Create links save
        save = [ { "album_path": l.album_path, "metadata_path": l.metadata_path} for l in self.links ]

        # Save links into file
        Util.save_json(self.linksPath, save, True)

    def add_link(self, link: Link) -> int:
        # Add link
        self.links.append(link)

        # Save links
        self.save_links()

        # Return last index
        return len(self.links) - 1

    def remove_link(self, link: Link):
        # Remove link
        self.links.remove(link)

        # Save links
        self.save_links()


# App
if __name__ == "__main__":
    app = CoonGallery()
    app.run()
from util.library import Library
from util.util import Util
from textual.app import App
from screens.home.home_screen import HomeScreen

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

    CSS_PATH = Util.join('styles', 'main.tcss')

    # Init
    def on_mount(self):
        # Use rose-pine as default theme
        self.theme = "rose-pine"

        # Load links
        Library.load_links()

        # Start HomeScreen
        self.push_screen(HomeScreen())

# App
if __name__ == "__main__":
    app = CoonGallery()
    app.run()
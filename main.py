from util.library import Library
from util.util import Util, Server
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

    # Style
    CSS_PATH = Util.join('styles', 'main.tcss')
    theme = "rose-pine" # Use rose-pine as default theme

    # Init
    def on_mount(self):
        # Load links
        Library.load_links()

        # Start server
        self.server: Server = Server()
        self.run_worker(self.server.start(), thread=True)

        # Start HomeScreen
        self.push_screen(HomeScreen())

# Run app
if __name__ == "__main__":
    app = CoonGallery()
    app.run()
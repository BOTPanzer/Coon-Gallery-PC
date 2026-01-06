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

    # State
    def on_mount(self):
        # Load links
        Library.load_links()

        # Init & start server
        Server.current = Server()
        self.run_worker(Server.current.start(), thread=True)

        # Start app in home
        self.push_screen(HomeScreen())

# Run app
if __name__ == "__main__":
    app = CoonGallery()
    app.run()
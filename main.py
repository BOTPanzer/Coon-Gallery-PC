from util.library import Library
from util.util import Util
from textual.app import App
from screens.home.home_screen import HomeScreen
from screens.sync.sync_server import SyncServer

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
    CSS_PATH = Util.join_path('styles', 'main.tcss')
    theme = "rose-pine" # Use rose-pine as default theme

    # State
    def on_mount(self):
        # Load links
        Library.load_links()

        # Init & start server
        SyncServer.current = SyncServer()
        self.run_worker(SyncServer.current.start(), thread=True)

        # Start app in home
        self.push_screen(HomeScreen())

# Run app
if __name__ == "__main__":
    app = CoonGallery()
    app.run()
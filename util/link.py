class Link:

    # Link info
    album_path = ""
    metadata_path = ""

    # Constructor
    def __init__(self, album_folder: str = "", metadata_file: str = ""):
        self.album_path = album_folder
        self.metadata_path = metadata_file
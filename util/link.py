from os.path import exists

class Link:

    # Constructor
    def __init__(self, album_path: str = "", metadata_path: str = ""):
        # Save info
        self.album_path = album_path
        self.metadata_path = metadata_path

    # Validate
    def isValid(self) -> bool:
        return exists(self.album_path) and exists(self.metadata_path)
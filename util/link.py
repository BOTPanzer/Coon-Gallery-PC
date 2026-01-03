from os.path import exists

class Link:

    # Constructor
    def __init__(self, album_folder: str = "", metadata_file: str = ""):
        # Save info
        self.album_path = album_folder
        self.metadata_path = metadata_file

    # Validate
    def isValid(self) -> bool:
        return exists(self.album_path) and exists(self.metadata_path)
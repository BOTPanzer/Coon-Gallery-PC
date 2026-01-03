from util.link import Link
from util.util import Util
from os import listdir
from os.path import  isfile, join

class Album:

    # Constructor
    def __init__(self, link: Link, filter: list):
        # Save info
        self.isValid = False
        self.link = link
        self.metadata = {}
        self.items_with_metadata = []
        self.items_without_metadata = []

        # Check if link paths exist
        if not link.isValid(): return

        # Load metadata
        self.metadata = Util.load_json(link.metadata_path)

        # Load album items
        unfiltered_items = listdir(link.album_path)
        for item_name in unfiltered_items:
            # Check if item is a file
            if not isfile(join(link.album_path, item_name)): continue

            # Check if item has a valid format
            is_valid = False
            for format in filter:
                if item_name.lower().endswith(format):
                    is_valid = True
                    break
            if not is_valid: continue

            # Check if item has metadata
            if item_name in self.metadata:
                self.items_with_metadata.append(item_name)
            else:
                self.items_without_metadata.append(item_name)

        # Mark as valid
        self.isValid = True
from util.link import Link
from util.metadata import Metadata
from util.util import Util
from os import listdir
from os.path import  isfile, exists, getmtime
from collections.abc import Callable
import shutil

# Albums
class Album:

    # Constructor
    def __init__(self, link: Link, filter: list[str]):
        # Init info
        self.album_path: str = link.album_path
        self.metadata_path: str = link.metadata_path
        self.metadata: dict = {}
        self.items: list[AlbumItem] = []
        self.items_with_metadata: int = 0
        self.items_without_metadata: int = 0

        # Load metadata
        self.load_metadata()

        # Load items
        self.load_items(filter)

    # Metadata
    def load_metadata(self):
        # Check if metadata path exist
        if not exists(self.metadata_path): return

        # Load metadata
        self.metadata = Util.load_json(self.metadata_path)

    def save_metadata(self, backup: bool = True):
        # Check if should backup
        if backup and exists(self.metadata_path):
            # Create new backup path
            metadata_backup_path = ''
            metadata_backup_index = 0
            while True:
                metadata_backup_path = self.metadata_path + '.backup' + str(metadata_backup_index)
                if not exists(metadata_backup_path): break
                metadata_backup_index += 1

            # Copy to backup path (copy2 preserves timestamps)
            shutil.copy2(self.metadata_path, metadata_backup_path)

        # Save metadata
        Util.save_json(self.metadata_path, self.metadata)

    def item_has_metadata(self, item_name: str) -> bool:
        # Check if item has metadata
        return item_name in self.metadata

    def get_item_metadata(self, item_name: str) -> dict:
        # Check if item has metadata
        if self.item_has_metadata(item_name):
            return self.metadata[item_name]
        else:
            return {}

    def set_item_metadata(self, item_name: str, item_metadata: dict):
        # Update item metadata
        self.metadata[item_name] = item_metadata

    def clean_metadata(self):
        # Create new metadata
        new_metadata = {}

        # Sort items
        self.sort_items()

        # Check each item to see if it has metadata
        item: AlbumItem
        for item in self.items:
            # Check if item has metadata
            if self.item_has_metadata(item.name):
                # Has metadata -> Add key to new metadata
                new_metadata[item.name] = self.metadata[item.name]

        # Replace old metadata with the new one
        self.metadata = new_metadata

    # Album items
    def load_items(self, filter: list[str]):
        # Check if album path exists
        if not exists(self.album_path): return

        # Reset items
        self.items: list = []
        self.items_with_metadata: int = 0
        self.items_without_metadata: int = 0

        # Load album items
        unfiltered_items = listdir(self.album_path)
        for item_name in unfiltered_items:
            # Create item path
            item_path = Util.join(self.album_path, item_name)

            # Check if item is a file
            if not isfile(item_path): continue

            # Check if item has a valid format
            is_valid = False
            for format in filter:
                if item_name.lower().endswith(format):
                    is_valid = True
                    break
            if not is_valid: continue

            # Save item
            self.items.append(AlbumItem(item_path, item_name))

            # Check if item has metadata
            if self.item_has_metadata(item_name):
                # Has metadata -> Increase "with" count
                self.items_with_metadata += 1
            else:
                # No metadata -> Increase "without" count
                self.items_without_metadata += 1

    def sort_items(self): 
        # Sort items by modified date (newest first)
        self.items.sort(key=lambda item: getmtime(item.path), reverse=True)

    def refresh_items_stats(self):
        # Reset item stats
        self.items_with_metadata = 0
        self.items_without_metadata = 0

        # Check each item to see if it has metadata
        item: AlbumItem
        for item in self.items:
            if self.item_has_metadata(item.name):
                # Has metadata -> Increase "with" count
                self.items_with_metadata += 1
            else:
                # No metadata -> Increase "without" count
                self.items_without_metadata += 1

    def search(self, search: str, on_result: Callable[[str], None]):
        # Ignore case
        search = search.casefold()

        # Search items
        item: AlbumItem
        for item in self.items:
            # Check if item has metadata
            if not self.item_has_metadata(item.name): continue

            # Get metadata key
            item_metadata = self.get_item_metadata(item.name)

            # Check if metadata contains search
            if (
                (search in item.name) or
                (Metadata.has_valid_caption(item_metadata) and search in item_metadata['caption'].casefold()) or 
                (Metadata.has_valid_labels(item_metadata) and any(search in item.casefold() for item in item_metadata['labels'])) or 
                (Metadata.has_valid_text(item_metadata) and any(search in item.casefold() for item in item_metadata['text']))
            ): 
                # Metadata contains search -> Call on result with item path
                on_result(item.path)

# Album items
class AlbumItem:

    # Constructor
    def __init__(self, path, name: str):
        # Init info
        self.path = path
        self.name = name
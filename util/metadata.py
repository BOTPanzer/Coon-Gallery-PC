class Metadata:

    @staticmethod
    def has_valid_caption(item_metadata: dict) -> bool:
        # Check if item metadata has caption
        return ('caption' in item_metadata) and (type(item_metadata['caption']) is str)

    @staticmethod
    def has_valid_labels(item_metadata: dict) -> bool:
        # Check if item metadata has labels
        return ('labels' in item_metadata) and (type(item_metadata['labels']) is list)

    @staticmethod
    def has_valid_text(item_metadata: dict) -> bool:
        # Check if item metadata has text
        return ('text' in item_metadata) and (type(item_metadata['text']) is list)
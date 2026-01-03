import json

class Util:

    @staticmethod
    def save_json(path: str, data, pretty: bool = False):
        with open(path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=4)
            else:
                json.dump(data, f, ensure_ascii=False) # Uglyer but faster and smaller size

    @staticmethod
    def load_json(path: str):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
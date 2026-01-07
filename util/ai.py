from util.util import Util
from PIL import ImageFile

# Description generation model
class DescriptionModel:

    def __init__(self):
        # Import libraries
        import torch
        from transformers import AutoProcessor, AutoModelForCausalLM

        # Select device
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # Load model
        model_path = Util.join_path(Util.get_data_path(), 'florence2')
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=self.torch_dtype, trust_remote_code=True).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    def run(self, image: ImageFile, prompt: str) -> str:
        # Run prompt
        inputs = self.processor(text=prompt, images=image, return_tensors='pt').to(self.device, self.torch_dtype)
        generated_ids = self.model.generate(
            input_ids=inputs['input_ids'],
            pixel_values=inputs['pixel_values'],
            max_new_tokens=1024,
            num_beams=3
        )
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = self.processor.post_process_generation(generated_text, task=prompt, image_size=(image.width, image.height))
        return parsed_answer[prompt]

    def generate_caption(self, image: ImageFile) -> str:
        return self.run(image, '<MORE_DETAILED_CAPTION>').strip() # <CAPTION> <DETAILED_CAPTION>

    def generate_labels(self, image: ImageFile) -> list[str]:
        return list(set(self.run(image, '<OD>')['labels'])) # list(set()) removes 

# Text detection model
class TextModel:

    def __init__(self):
        # Import libraries
        import torch
        from doctr.models import ocr_predictor

        # Load reader
        self.model = ocr_predictor(
            det_arch='db_resnet50', 
            reco_arch='crnn_vgg16_bn', 
            pretrained=True, 
            assume_straight_pages=False,
            straighten_pages=True,       # Fixes tilted/angled photos
            preserve_aspect_ratio=True   # Prevents stretching of photos
        )

        # Enable cuda if available
        if torch.cuda.is_available(): self.model.cuda()

    def detect_text(self, image_path: str) -> list[str]:
        from doctr.io import DocumentFile

        # Analyze the document
        result = self.model(DocumentFile.from_images(image_path))

        # Parse text
        full_text = result.render() # human-readable string of all text found
        return [line.strip() for line in full_text.split('\n') if line.strip()] # Split by newlines to return a list of strings
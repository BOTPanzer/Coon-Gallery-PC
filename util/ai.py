from util.util import Util
import numpy as np
from PIL import Image
import cv2

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
        model_path = Util.join(Util.get_data_path(), 'florence2')
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=self.torch_dtype, trust_remote_code=True).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    def run(self, image: Image, prompt: str) -> str:
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

    def generate_caption(self, image: Image) -> str:
        return self.run(image, '<MORE_DETAILED_CAPTION>').strip() # <CAPTION> <DETAILED_CAPTION>

    def generate_labels(self, image: Image) -> list:
        return list(set(self.run(image, '<OD>')['labels'])) # list(set()) removes 

# Text detection model
class TextModel:

    def __init__(self):
        # Import libraries
        import torch
        from paddleocr import PaddleOCR # pip install paddlepaddle paddleocr

        # Load model
        self.model = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)

    def detect_text(self, image: Image):
        # Detect text in image
        numpy_image = np.array(image.convert('RGB'))
        numpy_image_cv2 = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR) # Convert to BGR
        result = self.model.ocr(numpy_image_cv2, cls=True)
        texts = []
        for result in result:
            if result == None: continue
            for region in result:
                textAndConfidence = region[1] # [0] = text, [1] = confidence
                text = textAndConfidence[0].strip()
                confidence = textAndConfidence[1]
                if confidence > 0.5:
                    texts.append(text)
        return texts
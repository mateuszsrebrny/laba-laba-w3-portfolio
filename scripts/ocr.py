import sys
import easyocr
from PIL import Image
import numpy as np
import cv2


def upscale_image(pil_image, scale=2.0):
    w, h = pil_image.size
    return pil_image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def preprocess_image(pil_image):
    gray = np.array(pil_image.convert("L"))
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    return binary

# --- Main ---
file = sys.argv[1]

# Load and preprocess with PIL
pil_img = Image.open(file)
upscaled_img = upscale_image(pil_img)
preprocessed_img = preprocess_image(upscaled_img)

# Run OCR
reader = easyocr.Reader(['en'], gpu=False)
result = reader.readtext(preprocessed_img)
#result = reader.readtext(pil_img)
#result = reader.readtext(file)

# Output result
print(" ".join([text[1] for text in result]))

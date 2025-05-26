import easyocr
from PIL import Image

reader = easyocr.Reader(['en'], gpu=False)
result = reader.readtext('your_image.jpg', detail=0)

for line in result:
    print(line)

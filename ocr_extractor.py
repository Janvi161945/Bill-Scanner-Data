"""
OCR Text Extraction Module using Google Cloud Vision API
"""
import io
import os
from google.cloud import vision
from PIL import Image
import config


class OCRExtractor:
    """Extract text from bill images using Google Cloud Vision API"""

    def __init__(self):
        """Initialize the Vision API client"""
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GOOGLE_CLOUD_CREDENTIALS
        self.client = vision.ImageAnnotatorClient()

    def extract_text_from_image(self, image_path):
        """
        Extract text from an image file

        Args:
            image_path (str): Path to the image file

        Returns:
            str: Extracted text from the image
        """
        try:
            # Read the image file
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # Perform text detection
            response = self.client.text_detection(
                image=image,
                image_context={'language_hints': config.OCR_LANGUAGE_HINTS}
            )

            if response.error.message:
                raise Exception(f'Google Vision API Error: {response.error.message}')

            # Get the full text annotation
            texts = response.text_annotations

            if texts:
                # The first annotation contains all detected text
                extracted_text = texts[0].description
                return extracted_text
            else:
                return ""

        except Exception as e:
            raise Exception(f'OCR Extraction Error: {str(e)}')

    def extract_text_from_bytes(self, image_bytes):
        """
        Extract text from image bytes (for uploaded files)

        Args:
            image_bytes (bytes): Image data as bytes

        Returns:
            str: Extracted text from the image
        """
        try:
            image = vision.Image(content=image_bytes)

            # Perform text detection
            response = self.client.text_detection(
                image=image,
                image_context={'language_hints': config.OCR_LANGUAGE_HINTS}
            )

            if response.error.message:
                raise Exception(f'Google Vision API Error: {response.error.message}')

            texts = response.text_annotations

            if texts:
                extracted_text = texts[0].description
                return extracted_text
            else:
                return ""

        except Exception as e:
            raise Exception(f'OCR Extraction Error: {str(e)}')


# Alternative: Tesseract OCR implementation (fallback option)
class TesseractOCRExtractor:
    """Extract text using Tesseract OCR (local, no API key needed)"""

    def __init__(self):
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            raise ImportError("pytesseract not installed. Run: pip install pytesseract")

    def extract_text_from_image(self, image_path):
        """Extract text from image using Tesseract"""
        try:
            image = Image.open(image_path)
            text = self.pytesseract.image_to_string(image, lang='eng')
            return text
        except Exception as e:
            raise Exception(f'Tesseract OCR Error: {str(e)}')

    def extract_text_from_bytes(self, image_bytes):
        """Extract text from image bytes using Tesseract"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = self.pytesseract.image_to_string(image, lang='eng')
            return text
        except Exception as e:
            raise Exception(f'Tesseract OCR Error: {str(e)}')

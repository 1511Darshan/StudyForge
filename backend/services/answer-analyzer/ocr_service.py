"""
OCR Service for StudyForge Answer Analyzer
Handles text extraction from handwritten answer sheets and question papers
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
import logging
from typing import List, Dict, Tuple, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRService:
    """Optical Character Recognition service for extracting text from images"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR service
        
        Args:
            tesseract_path: Path to tesseract executable (Windows only)
        """
        # Set tesseract path for Windows if provided
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            logger.info("Please install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Enhance image quality for better OCR accuracy
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            logger.info(f"Processing image: {image_path}")
            
            # Convert to RGB for PIL processing
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            # Enhance contrast and sharpness
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Sharpness(pil_img)
            pil_img = enhancer.enhance(1.1)
            
            # Convert back to OpenCV format
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
            
            # Apply adaptive thresholding for better text contrast
            adaptive_thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Optional: Apply morphological operations to clean up text
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            
            logger.info("Image preprocessing completed")
            return processed
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            raise
    
    def extract_text_basic(self, image_path: str) -> str:
        """
        Basic text extraction using Tesseract
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as string
        """
        try:
            processed_img = self.preprocess_image(image_path)
            
            # Configure Tesseract for better handwritten text recognition
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?;:()\n\-+=*/^%$#@[]{}|\\~`"' + "'"
            
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            # Clean up the extracted text
            cleaned_text = self._clean_extracted_text(text)
            
            logger.info(f"Extracted {len(cleaned_text)} characters of text")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return ""
    
    def extract_text_with_coordinates(self, image_path: str) -> List[Dict]:
        """
        Extract text with bounding box coordinates for layout analysis
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing text and position information
        """
        try:
            processed_img = self.preprocess_image(image_path)
            
            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(
                processed_img, 
                output_type=pytesseract.Output.DICT,
                config=r'--oem 3 --psm 6'
            )
            
            extracted_data = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                # Filter out low confidence and empty text
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence > 30 and text:  # Only keep confident detections
                    extracted_data.append({
                        'text': text,
                        'confidence': confidence / 100.0,  # Convert to 0-1 scale
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        },
                        'block_num': data['block_num'][i],
                        'par_num': data['par_num'][i],
                        'line_num': data['line_num'][i],
                        'word_num': data['word_num'][i]
                    })
            
            logger.info(f"Extracted {len(extracted_data)} text elements with coordinates")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting text with coordinates from {image_path}: {str(e)}")
            return []
    
    def extract_lines(self, image_path: str) -> List[str]:
        """
        Extract text organized by lines for better structure
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of text lines
        """
        try:
            text_data = self.extract_text_with_coordinates(image_path)
            
            # Group by line numbers
            lines_dict = {}
            for item in text_data:
                line_key = f"{item['block_num']}_{item['par_num']}_{item['line_num']}"
                if line_key not in lines_dict:
                    lines_dict[line_key] = []
                lines_dict[line_key].append(item)
            
            # Sort and combine words in each line
            lines = []
            for line_key in sorted(lines_dict.keys()):
                line_items = sorted(lines_dict[line_key], key=lambda x: x['bbox']['x'])
                line_text = ' '.join([item['text'] for item in line_items])
                if line_text.strip():
                    lines.append(line_text.strip())
            
            logger.info(f"Extracted {len(lines)} text lines")
            return lines
            
        except Exception as e:
            logger.error(f"Error extracting lines from {image_path}: {str(e)}")
            return []
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common OCR errors for mathematical text
        replacements = {
            # Common character misrecognitions
            '|': 'I',  # Vertical bar often mistaken for I
            '0': 'O',  # Zero to O in text (be careful with math)
            '5': 'S',  # Five to S in text
            '1': 'l',  # One to lowercase l in some contexts
            '6': 'G',  # Six to G
            '8': 'B',  # Eight to B
            # Mathematical symbols
            '×': '*',  # Multiplication
            '÷': '/',  # Division
            '−': '-',  # Minus sign
            '≤': '<=', # Less than or equal
            '≥': '>=', # Greater than or equal
            '≠': '!=', # Not equal
            '√': 'sqrt', # Square root
            '²': '^2',   # Superscript 2
            '³': '^3',   # Superscript 3
        }
        
        # Apply replacements cautiously (avoid over-correction)
        for old, new in replacements.items():
            # Only replace if it makes sense in context
            if old in text:
                text = text.replace(old, new)
        
        return text.strip()
    
    def validate_image(self, image_path: str) -> Tuple[bool, str]:
        """
        Validate if image is suitable for OCR processing
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return False, "Image file does not exist"
            
            # Check file size (limit to 10MB)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:
                return False, "Image file too large (max 10MB)"
            
            # Try to read the image
            img = cv2.imread(image_path)
            if img is None:
                return False, "Unable to read image file"
            
            # Check image dimensions
            height, width = img.shape[:2]
            if width < 100 or height < 100:
                return False, "Image too small (minimum 100x100 pixels)"
            
            if width > 5000 or height > 5000:
                return False, "Image too large (maximum 5000x5000 pixels)"
            
            return True, "Image is valid for OCR processing"
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}"
    
    def get_image_info(self, image_path: str) -> Dict:
        """
        Get basic information about the image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image information
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {}
            
            height, width, channels = img.shape
            file_size = os.path.getsize(image_path)
            
            return {
                'width': width,
                'height': height,
                'channels': channels,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting image info: {str(e)}")
            return {}

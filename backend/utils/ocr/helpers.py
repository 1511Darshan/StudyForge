"""
OCR utilities and helper functions
"""
import os
import tempfile
from typing import List, Dict
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def convert_to_supported_format(image_path: str, output_format: str = 'PNG') -> str:
    """
    Convert image to a format supported by OCR
    
    Args:
        image_path: Path to input image
        output_format: Desired output format (PNG, JPEG)
        
    Returns:
        Path to converted image
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Create temporary file for converted image
            temp_dir = tempfile.gettempdir()
            temp_filename = f"ocr_temp_{os.getpid()}_{hash(image_path) % 10000}.{output_format.lower()}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Save in supported format
            img.save(temp_path, format=output_format)
            
            logger.info(f"Converted {image_path} to {temp_path}")
            return temp_path
            
    except Exception as e:
        logger.error(f"Error converting image format: {str(e)}")
        return image_path  # Return original if conversion fails


def cleanup_temp_files(file_paths: List[str]):
    """
    Clean up temporary files created during OCR processing
    
    Args:
        file_paths: List of temporary file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path) and 'ocr_temp_' in os.path.basename(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not delete temporary file {file_path}: {str(e)}")


def estimate_reading_difficulty(text: str) -> Dict[str, float]:
    """
    Estimate the reading difficulty and quality of extracted text
    
    Args:
        text: Extracted text to analyze
        
    Returns:
        Dictionary with difficulty metrics
    """
    if not text:
        return {'confidence': 0.0, 'word_count': 0, 'avg_word_length': 0.0}
    
    words = text.split()
    word_count = len(words)
    
    if word_count == 0:
        return {'confidence': 0.0, 'word_count': 0, 'avg_word_length': 0.0}
    
    # Calculate average word length
    avg_word_length = sum(len(word) for word in words) / word_count
    
    # Estimate confidence based on various factors
    confidence = 1.0
    
    # Penalize very short or very long average word lengths
    if avg_word_length < 2 or avg_word_length > 12:
        confidence *= 0.8
    
    # Penalize if too many single characters (likely OCR errors)
    single_chars = sum(1 for word in words if len(word) == 1)
    if single_chars > word_count * 0.3:
        confidence *= 0.7
    
    # Penalize excessive special characters
    special_char_ratio = sum(1 for char in text if not char.isalnum() and char != ' ') / len(text)
    if special_char_ratio > 0.2:
        confidence *= 0.8
    
    return {
        'confidence': round(confidence, 2),
        'word_count': word_count,
        'avg_word_length': round(avg_word_length, 2),
        'special_char_ratio': round(special_char_ratio, 2)
    }


def extract_mathematical_expressions(text: str) -> List[str]:
    """
    Extract mathematical expressions from text
    
    Args:
        text: Text to search for mathematical expressions
        
    Returns:
        List of detected mathematical expressions
    """
    import re
    
    # Patterns for mathematical expressions
    patterns = [
        r'[a-zA-Z]?\s*[=]\s*[^=\n]+',  # Equations like x = 5, f(x) = 2x + 1
        r'\d+\s*[+\-*/^]\s*\d+',       # Basic arithmetic
        r'[a-zA-Z]+\([^)]+\)',         # Functions like sin(x), f(x)
        r'\d+\s*[a-zA-Z]\d*',          # Terms like 3x, 2y^2
        r'√\d+|sqrt\(\d+\)',           # Square roots
        r'\d+\^\d+',                   # Exponents
        r'\([^)]+\)\s*[+\-*/^]\s*\([^)]+\)',  # Grouped expressions
    ]
    
    expressions = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        expressions.extend(matches)
    
    # Remove duplicates and clean up
    unique_expressions = list(set(expr.strip() for expr in expressions if expr.strip()))
    
    return unique_expressions


def detect_language(text: str) -> str:
    """
    Simple language detection for the extracted text
    
    Args:
        text: Text to analyze
        
    Returns:
        Detected language code ('en', 'hi', 'unknown')
    """
    if not text:
        return 'unknown'
    
    # Count English words (simple heuristic)
    english_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'question', 'answer', 'solve', 'find', 'calculate', 'given', 'if',
        'then', 'therefore', 'because', 'since', 'when', 'where', 'what',
        'how', 'why', 'which', 'who', 'whose'
    }
    
    words = text.lower().split()
    if not words:
        return 'unknown'
    
    english_count = sum(1 for word in words if word in english_words)
    english_ratio = english_count / len(words)
    
    if english_ratio > 0.1:  # If more than 10% are common English words
        return 'en'
    else:
        # Check for Hindi/Devanagari characters
        hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        if hindi_chars > 0:
            return 'hi'
    
    return 'unknown'


def get_file_extension(image_path: str) -> str:
    """
    Get file extension in lowercase
    
    Args:
        image_path: Path to image file
        
    Returns:
        File extension without dot (e.g., 'jpg', 'png')
    """
    return os.path.splitext(image_path)[1].lower().lstrip('.')

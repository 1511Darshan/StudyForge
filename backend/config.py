"""
Configuration settings for StudyForge Answer Analyzer OCR
"""
import os

# OCR Configuration
OCR_CONFIG = {
    # Tesseract settings
    'tesseract_path': {
        'windows': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        'linux': '/usr/bin/tesseract',
        'mac': '/usr/local/bin/tesseract'
    },
    
    # Image processing settings
    'image_processing': {
        'max_file_size_mb': 10,
        'min_width': 100,
        'min_height': 100,
        'max_width': 5000,
        'max_height': 5000,
        'supported_formats': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']
    },
    
    # OCR accuracy settings
    'ocr_settings': {
        'min_confidence': 30,  # Minimum confidence for text detection
        'psm_mode': 6,         # Page segmentation mode
        'oem_mode': 3,         # OCR Engine mode
        'language': 'eng',     # Primary language
        'char_whitelist': '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?;:()\n\-+=*/^%$#@[]{}|\\~`"' + "'"
    },
    
    # Text processing settings
    'text_processing': {
        'max_single_char_ratio': 0.3,    # Maximum ratio of single characters
        'max_special_char_ratio': 0.2,   # Maximum ratio of special characters
        'min_word_length': 1,             # Minimum word length
        'max_word_length': 50             # Maximum word length
    }
}

# Get appropriate tesseract path based on OS
def get_tesseract_path():
    """Get the appropriate tesseract path for the current OS"""
    import platform
    system = platform.system().lower()
    
    if system == 'windows':
        path = OCR_CONFIG['tesseract_path']['windows']
    elif system == 'darwin':  # macOS
        path = OCR_CONFIG['tesseract_path']['mac']
    else:  # Linux and others
        path = OCR_CONFIG['tesseract_path']['linux']
    
    # Check if path exists
    if os.path.exists(path):
        return path
    
    # Try to find tesseract in PATH
    import shutil
    tesseract_cmd = shutil.which('tesseract')
    if tesseract_cmd:
        return tesseract_cmd
    
    return None

# Directory settings
UPLOAD_DIRS = {
    'answer_sheets': 'uploads/answer-sheets',
    'question_papers': 'uploads/question-papers',
    'temp': 'temp/ocr'
}

# Database settings
DATABASE_CONFIG = {
    'default_db_path': 'studyforge_analyzer.db',
    'backup_enabled': True,
    'backup_interval_hours': 24
}

# Logging settings
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'logs/analyzer.log'
}

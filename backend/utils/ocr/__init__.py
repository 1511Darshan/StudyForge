# OCR utils package
from .helpers import (
    convert_to_supported_format,
    cleanup_temp_files,
    estimate_reading_difficulty,
    extract_mathematical_expressions,
    detect_language,
    get_file_extension
)

__all__ = [
    'convert_to_supported_format',
    'cleanup_temp_files', 
    'estimate_reading_difficulty',
    'extract_mathematical_expressions',
    'detect_language',
    'get_file_extension'
]

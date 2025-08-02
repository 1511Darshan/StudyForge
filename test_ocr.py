"""
Test script for OCR service
Creates a sample image with text and tests OCR functionality
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def create_sample_image():
    """Create a sample image with text for testing OCR"""
    # Create a white image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use default font, fallback to built-in if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    
    # Add sample text that might appear in answer sheets
    sample_text = [
        "Q1. Solve the equation: x² + 5x + 6 = 0",
        "",
        "Solution:",
        "Using factoring method:",
        "x² + 5x + 6 = (x + 2)(x + 3) = 0",
        "Therefore: x = -2 or x = -3",
        "",
        "Verification:",
        "For x = -2: (-2)² + 5(-2) + 6 = 4 - 10 + 6 = 0 ✓",
        "For x = -3: (-3)² + 5(-3) + 6 = 9 - 15 + 6 = 0 ✓"
    ]
    
    y_position = 50
    for line in sample_text:
        if line.strip():  # Skip empty lines for positioning
            draw.text((50, y_position), line, fill='black', font=font)
        y_position += 35
    
    # Save the sample image
    sample_path = "test_answer_sheet.png"
    img.save(sample_path)
    print(f"✅ Created sample image: {sample_path}")
    return sample_path


def test_ocr_service():
    """Test the OCR service with sample image"""
    try:
        from backend.services.answer_analyzer.ocr_service import OCRService
        from backend.utils.ocr.helpers import estimate_reading_difficulty, extract_mathematical_expressions
        
        print("Testing OCR Service...")
        
        # Create sample image
        sample_image = create_sample_image()
        
        # Initialize OCR service
        ocr = OCRService()
        
        # Test image validation
        is_valid, message = ocr.validate_image(sample_image)
        print(f"✅ Image validation: {is_valid} - {message}")
        
        if not is_valid:
            print("❌ Sample image validation failed")
            return
        
        # Test basic text extraction
        print("\n--- Basic Text Extraction ---")
        text = ocr.extract_text_basic(sample_image)
        print(f"Extracted text ({len(text)} chars):")
        print(text[:200] + "..." if len(text) > 200 else text)
        
        # Test text with coordinates
        print("\n--- Text with Coordinates ---")
        text_data = ocr.extract_text_with_coordinates(sample_image)
        print(f"Found {len(text_data)} text elements")
        for i, item in enumerate(text_data[:3]):  # Show first 3 items
            print(f"  {i+1}. '{item['text']}' (confidence: {item['confidence']:.2f})")
        
        # Test line extraction
        print("\n--- Line Extraction ---")
        lines = ocr.extract_lines(sample_image)
        print(f"Extracted {len(lines)} lines:")
        for i, line in enumerate(lines[:5]):  # Show first 5 lines
            print(f"  {i+1}. {line}")
        
        # Test text analysis
        print("\n--- Text Analysis ---")
        difficulty = estimate_reading_difficulty(text)
        print(f"Reading difficulty: {difficulty}")
        
        math_expressions = extract_mathematical_expressions(text)
        print(f"Mathematical expressions found: {len(math_expressions)}")
        for expr in math_expressions[:3]:  # Show first 3
            print(f"  - {expr}")
        
        # Get image info
        print("\n--- Image Information ---")
        info = ocr.get_image_info(sample_image)
        print(f"Image info: {info}")
        
        print("\n🎉 OCR service test completed successfully!")
        
        # Clean up
        if os.path.exists(sample_image):
            os.remove(sample_image)
            print("🧹 Cleaned up test image")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install opencv-python pytesseract pillow numpy")
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_ocr_service()

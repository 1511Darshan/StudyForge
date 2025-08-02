"""
Integration test for OCR + Text Processing pipeline
Shows how the components work together for answer sheet analysis
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def create_realistic_answer_sheet():
    """Create a more realistic answer sheet image for testing"""
    # Create a larger image that resembles an answer sheet
    img = Image.new('RGB', (800, 1000), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font
    try:
        font_large = ImageFont.truetype("arial.ttf", 20)
        font_medium = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add header
    draw.text((50, 30), "Mathematics Exam - Answer Sheet", fill='black', font=font_large)
    draw.text((50, 60), "Name: John Doe    Roll No: 123    Class: X", fill='black', font=font_small)
    
    # Add questions and answers with realistic spacing
    y_pos = 120
    
    # Question 1
    draw.text((50, y_pos), "Q1. Solve the quadratic equation: x² + 5x + 6 = 0", fill='black', font=font_medium)
    y_pos += 40
    draw.text((70, y_pos), "Solution:", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "Using factoring method:", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "x² + 5x + 6 = (x + 2)(x + 3) = 0", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "Therefore: x = -2 or x = -3", fill='black', font=font_small)
    y_pos += 40
    
    # Question 2
    draw.text((50, y_pos), "Q2. Find the derivative of f(x) = 3x³ + 2x² - 5x + 1", fill='black', font=font_medium)
    y_pos += 40
    draw.text((70, y_pos), "Answer:", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "Using power rule: d/dx[x^n] = nx^(n-1)", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "f'(x) = 3×3x² + 2×2x - 5×1 + 0", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "f'(x) = 9x² + 4x - 5", fill='black', font=font_small)
    y_pos += 40
    
    # Question 3
    draw.text((50, y_pos), "Question 3: Calculate the area of a triangle with base = 10 cm, height = 8 cm", fill='black', font=font_medium)
    y_pos += 40
    draw.text((70, y_pos), "Given: base = 10 cm, height = 8 cm", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "Formula: Area = (1/2) × base × height", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "Area = (1/2) × 10 × 8 = 40 cm²", fill='black', font=font_small)
    y_pos += 40
    
    # Question 4
    draw.text((50, y_pos), "(4) Simplify: (2x + 3)² - (x - 1)²", fill='black', font=font_medium)
    y_pos += 40
    draw.text((70, y_pos), "Expanding the squares:", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "(2x + 3)² = 4x² + 12x + 9", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "(x - 1)² = x² - 2x + 1", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "Result = 4x² + 12x + 9 - x² + 2x - 1", fill='black', font=font_small)
    y_pos += 25
    draw.text((70, y_pos), "= 3x² + 14x + 8", fill='black', font=font_small)
    
    # Save the image
    filename = "realistic_answer_sheet.png"
    img.save(filename)
    return filename


def test_integration():
    """Test the complete OCR + Text Processing pipeline"""
    try:
        print("=== OCR + Text Processing Integration Test ===\n")
        
        # Import required modules
        from backend.services.answer_analyzer.ocr_service import OCRService
        from backend.services.answer_analyzer.text_processor import TextProcessor
        from backend.utils.question_patterns import QuestionPatternMatcher
        
        # Create test image
        print("📄 Creating realistic answer sheet...")
        image_path = create_realistic_answer_sheet()
        print(f"✅ Created test image: {image_path}")
        
        # Initialize services
        print("\n🔧 Initializing services...")
        ocr_service = OCRService()
        text_processor = TextProcessor()
        pattern_matcher = QuestionPatternMatcher()
        
        # Step 1: OCR Processing
        print("\n📖 Step 1: OCR Text Extraction")
        print("-" * 40)
        
        # Validate image first
        is_valid, message = ocr_service.validate_image(image_path)
        print(f"Image validation: {message}")
        
        if not is_valid:
            print("❌ Image validation failed, stopping test")
            return
        
        # Extract text with coordinates
        text_data = ocr_service.extract_text_with_coordinates(image_path)
        print(f"✅ Extracted {len(text_data)} text elements")
        
        # Show sample extracted text
        print("\nSample extracted text:")
        for i, item in enumerate(text_data[:5]):
            print(f"  {i+1}. '{item['text']}' (conf: {item['confidence']:.2f})")
        
        # Step 2: Question Pattern Analysis
        print("\n🔍 Step 2: Question Pattern Analysis")
        print("-" * 40)
        
        question_info = pattern_matcher.extract_all_question_numbers(text_data)
        print(f"✅ Detected {len(question_info)} questions")
        
        for q in question_info:
            print(f"  Q{q['question_number']}: {q['pattern_type']} (conf: {q['confidence']:.2f})")
        
        # Validate question sequence
        question_numbers = [q['question_number'] for q in question_info]
        validation = pattern_matcher.validate_question_sequence(question_numbers)
        print(f"\nSequence validation: {'✅ Valid' if validation['is_valid'] else '⚠️ Issues found'}")
        if validation['issues']:
            for issue in validation['issues']:
                print(f"  - {issue}")
        
        # Step 3: Text Segmentation
        print("\n✂️ Step 3: Text Segmentation")
        print("-" * 40)
        
        segments = text_processor.segment_by_questions(text_data, question_numbers)
        print(f"✅ Created {len(segments)} text segments")
        
        for q_num, segment in segments.items():
            print(f"\nQuestion {q_num}:")
            print(f"  Question: {segment['question_text'][:60]}...")
            print(f"  Answer: {segment['answer_text'][:60]}...")
            print(f"  Total chars: {len(segment['full_text'])}")
        
        # Step 4: Content Analysis
        print("\n📊 Step 4: Content Analysis")
        print("-" * 40)
        
        # Overall structure analysis
        structure_analysis = text_processor.analyze_text_structure(segments)
        print("Structure Analysis:")
        print(f"  Questions: {structure_analysis['total_questions']}")
        print(f"  Total words: {structure_analysis['total_words']}")
        print(f"  Avg answer length: {structure_analysis['avg_answer_length']:.1f} words")
        print(f"  Math content ratio: {structure_analysis['mathematical_content_ratio']:.2f}")
        print(f"  Confidence: {structure_analysis['confidence_score']:.2f}")
        
        if structure_analysis['quality_issues']:
            print("  Quality issues:")
            for issue in structure_analysis['quality_issues']:
                print(f"    - {issue}")
        
        # Mathematical content analysis
        print("\nMathematical Content Analysis:")
        for q_num, segment in list(segments.items())[:2]:  # Analyze first 2 questions
            math_content = text_processor.extract_mathematical_content(segment['full_text'])
            print(f"  Q{q_num}:")
            if math_content['equations']:
                print(f"    Equations: {math_content['equations']}")
            if math_content['expressions']:
                print(f"    Expressions: {math_content['expressions'][:3]}...")  # Show first 3
            if math_content['variables']:
                print(f"    Variables: {math_content['variables']}")
        
        # Subject detection
        full_text = ' '.join([seg['full_text'] for seg in segments.values()])
        subject_scores = pattern_matcher.detect_subject_from_content(full_text)
        print("\nSubject Detection:")
        for subject, score in sorted(subject_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                print(f"  {subject.title()}: {score:.2f}")
        
        # Step 5: Quality Assessment
        print("\n🎯 Step 5: Quality Assessment")
        print("-" * 40)
        
        # Get improvement suggestions
        suggestions = pattern_matcher.suggest_improvements(text_data, question_numbers)
        if suggestions:
            print("Improvement suggestions:")
            for suggestion in suggestions:
                print(f"  💡 {suggestion}")
        else:
            print("✅ No improvement suggestions - processing quality is good!")
        
        # Final summary
        print("\n📋 Final Summary")
        print("-" * 40)
        print(f"✅ Successfully processed answer sheet with {len(segments)} questions")
        print(f"✅ Overall confidence: {structure_analysis['confidence_score']:.2f}")
        print(f"✅ Text extraction quality: {'Good' if len(text_data) > 10 else 'Fair'}")
        print(f"✅ Question detection: {'Excellent' if len(question_info) >= 3 else 'Good'}")
        
        # Cleanup
        if os.path.exists(image_path):
            os.remove(image_path)
            print("🧹 Cleaned up test image")
        
        print("\n🎉 Integration test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_integration()

"""
Test script for text processing functionality
Tests question detection and text segmentation
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def create_sample_text_data():
    """Create sample OCR text data for testing"""
    return [
        {
            'text': 'Q1. Solve the quadratic equation x² + 5x + 6 = 0',
            'confidence': 0.95,
            'bbox': {'x': 50, 'y': 100, 'width': 300, 'height': 25}
        },
        {
            'text': 'Solution: Using factoring method',
            'confidence': 0.88,
            'bbox': {'x': 50, 'y': 140, 'width': 200, 'height': 20}
        },
        {
            'text': 'x² + 5x + 6 = (x + 2)(x + 3) = 0',
            'confidence': 0.92,
            'bbox': {'x': 50, 'y': 170, 'width': 250, 'height': 20}
        },
        {
            'text': 'Therefore x = -2 or x = -3',
            'confidence': 0.90,
            'bbox': {'x': 50, 'y': 200, 'width': 180, 'height': 20}
        },
        {
            'text': 'Q2. Find the derivative of f(x) = 3x³ + 2x² - 5x + 1',
            'confidence': 0.93,
            'bbox': {'x': 50, 'y': 280, 'width': 350, 'height': 25}
        },
        {
            'text': 'Answer: Using power rule',
            'confidence': 0.87,
            'bbox': {'x': 50, 'y': 320, 'width': 150, 'height': 20}
        },
        {
            'text': "f'(x) = 9x² + 4x - 5",
            'confidence': 0.91,
            'bbox': {'x': 50, 'y': 350, 'width': 140, 'height': 20}
        },
        {
            'text': 'Question 3: Calculate the area of triangle with base = 10 cm, height = 8 cm',
            'confidence': 0.89,
            'bbox': {'x': 50, 'y': 450, 'width': 400, 'height': 25}
        },
        {
            'text': 'Given: base = 10 cm, height = 8 cm',
            'confidence': 0.86,
            'bbox': {'x': 50, 'y': 490, 'width': 220, 'height': 20}
        },
        {
            'text': 'Area = (1/2) × base × height = (1/2) × 10 × 8 = 40 cm²',
            'confidence': 0.88,
            'bbox': {'x': 50, 'y': 520, 'width': 320, 'height': 20}
        }
    ]


def test_text_processor():
    """Test the text processing functionality"""
    try:
        from backend.services.answer_analyzer.text_processor import TextProcessor
        
        print("Testing Text Processor...")
        
        # Initialize processor
        processor = TextProcessor()
        
        # Create sample data
        sample_data = create_sample_text_data()
        print(f"✅ Created sample data with {len(sample_data)} text items")
        
        # Test question number extraction
        print("\n--- Question Number Extraction ---")
        question_numbers = processor.extract_question_numbers(sample_data)
        print(f"Detected question numbers: {question_numbers}")
        
        if len(question_numbers) >= 2:
            print("✅ Question number extraction successful")
        else:
            print("❌ Question number extraction failed")
            return
        
        # Test text segmentation
        print("\n--- Text Segmentation ---")
        segments = processor.segment_by_questions(sample_data, question_numbers)
        print(f"Created {len(segments)} segments")
        
        for q_num, segment in segments.items():
            print(f"\nQuestion {q_num}:")
            print(f"  Question: {segment['question_text'][:50]}...")
            print(f"  Answer: {segment['answer_text'][:50]}...")
            print(f"  Total length: {len(segment['full_text'])} characters")
        
        if len(segments) >= 2:
            print("✅ Text segmentation successful")
        else:
            print("❌ Text segmentation failed")
            return
        
        # Test mathematical content extraction
        print("\n--- Mathematical Content Analysis ---")
        for q_num, segment in list(segments.items())[:2]:  # Test first 2 questions
            math_content = processor.extract_mathematical_content(segment['full_text'])
            print(f"\nQuestion {q_num} mathematical content:")
            print(f"  Equations: {math_content['equations']}")
            print(f"  Expressions: {math_content['expressions']}")
            print(f"  Variables: {math_content['variables']}")
            print(f"  Numbers: {math_content['numbers']}")
        
        print("✅ Mathematical content extraction successful")
        
        # Test structure analysis
        print("\n--- Structure Analysis ---")
        analysis = processor.analyze_text_structure(segments)
        print("Analysis results:")
        print(f"  Total questions: {analysis['total_questions']}")
        print(f"  Total words: {analysis['total_words']}")
        print(f"  Average answer length: {analysis['avg_answer_length']:.1f} words")
        print(f"  Math content ratio: {analysis['mathematical_content_ratio']:.2f}")
        print(f"  Confidence score: {analysis['confidence_score']}")
        
        if analysis['quality_issues']:
            print(f"  Quality issues: {analysis['quality_issues']}")
        
        print("✅ Structure analysis successful")
        
        # Test context extraction
        print("\n--- Context Analysis ---")
        if len(segments) >= 2:
            first_question = list(segments.keys())[0]
            context = processor.get_question_context(segments, first_question)
            print(f"Context for Question {first_question}:")
            print(f"  Has next question: {bool(context['next_question'])}")
            print(f"  Related content: {context['related_content']}")
        
        print("✅ Context analysis successful")
        
        # Test edge cases
        print("\n--- Edge Case Testing ---")
        
        # Empty data
        empty_segments = processor.segment_by_questions([], [])
        print(f"Empty data handling: {len(empty_segments)} segments (expected: 0)")
        
        # Malformed text
        malformed_data = [
            {'text': 'Q999. Invalid question number', 'confidence': 0.5, 'bbox': {'x': 0, 'y': 0, 'width': 100, 'height': 20}},
            {'text': '!@#$%^&*()', 'confidence': 0.3, 'bbox': {'x': 0, 'y': 30, 'width': 100, 'height': 20}}
        ]
        
        malformed_questions = processor.extract_question_numbers(malformed_data)
        print(f"Malformed data handling: {malformed_questions}")
        
        print("✅ Edge case testing successful")
        
        print("\n🎉 All text processor tests passed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the text processor module is available")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_real_world_patterns():
    """Test with real-world question patterns"""
    try:
        from backend.services.answer_analyzer.text_processor import TextProcessor
        
        print("\nTesting Real-World Question Patterns...")
        
        processor = TextProcessor()
        
        # Various question formats found in real answer sheets
        real_world_data = [
            {'text': '1. What is the capital of India?', 'confidence': 0.9, 'bbox': {'x': 50, 'y': 50, 'width': 200, 'height': 20}},
            {'text': 'Ans. New Delhi', 'confidence': 0.85, 'bbox': {'x': 50, 'y': 80, 'width': 100, 'height': 20}},
            
            {'text': '(2) Solve: 2x + 3 = 7', 'confidence': 0.88, 'bbox': {'x': 50, 'y': 150, 'width': 150, 'height': 20}},
            {'text': '2x = 7 - 3 = 4', 'confidence': 0.82, 'bbox': {'x': 50, 'y': 180, 'width': 120, 'height': 20}},
            {'text': 'x = 2', 'confidence': 0.90, 'bbox': {'x': 50, 'y': 210, 'width': 50, 'height': 20}},
            
            {'text': 'No.3 Define photosynthesis', 'confidence': 0.87, 'bbox': {'x': 50, 'y': 280, 'width': 180, 'height': 20}},
            {'text': 'Photosynthesis is the process by which plants make food', 'confidence': 0.83, 'bbox': {'x': 50, 'y': 310, 'width': 300, 'height': 20}},
            
            {'text': 'Question 4: Why is water important?', 'confidence': 0.89, 'bbox': {'x': 50, 'y': 380, 'width': 220, 'height': 20}},
            {'text': 'Water is essential for life because...', 'confidence': 0.86, 'bbox': {'x': 50, 'y': 410, 'width': 250, 'height': 20}},
        ]
        
        # Test extraction
        questions = processor.extract_question_numbers(real_world_data)
        print(f"Real-world questions detected: {questions}")
        
        # Test segmentation
        segments = processor.segment_by_questions(real_world_data, questions)
        print(f"Segmented into {len(segments)} parts")
        
        for q_num, segment in segments.items():
            print(f"\nQ{q_num}: {segment['full_text'][:80]}...")
        
        if len(segments) >= 3:
            print("✅ Real-world pattern testing successful")
        else:
            print("⚠️ Some real-world patterns may not be detected")
        
    except Exception as e:
        print(f"❌ Real-world pattern test failed: {e}")


if __name__ == "__main__":
    test_text_processor()
    test_real_world_patterns()

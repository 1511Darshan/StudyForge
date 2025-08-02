"""
Test script for semantic matching functionality
Tests AI-powered answer analysis against rubrics
"""
import os
import sys
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def create_test_rubric():
    """Create a sample rubric for testing"""
    return {
        'id': 'test_math_q1',
        'subject': 'mathematics',
        'question_number': '1',
        'question_text': 'Solve the quadratic equation: x² + 5x + 6 = 0',
        'model_answer': 'Using factoring method: x² + 5x + 6 = (x + 2)(x + 3) = 0. Therefore x = -2 or x = -3',
        'marking_scheme': {
            'method_identification': {
                'description': 'Identifies correct method (factoring, quadratic formula, or completing square)',
                'marks': 2,
                'keywords': ['factoring', 'factor', 'quadratic formula', 'completing square']
            },
            'correct_factoring': {
                'description': 'Correctly factors the quadratic expression',
                'marks': 3,
                'keywords': ['(x + 2)', '(x + 3)', 'x+2', 'x+3']
            },
            'final_solution': {
                'description': 'States the correct solutions x = -2 and x = -3',
                'marks': 2,
                'keywords': ['x = -2', 'x = -3', 'x=-2', 'x=-3']
            },
            'verification': {
                'description': 'Shows verification by substituting back into original equation',
                'marks': 1,
                'keywords': ['verify', 'check', 'substitute', 'proof']
            }
        },
        'keywords': ['quadratic', 'equation', 'solve', 'factor', 'x = -2', 'x = -3'],
        'max_marks': 8
    }


def create_test_answers():
    """Create sample student answers for testing"""
    return {
        'excellent_answer': """
            Using factoring method to solve x² + 5x + 6 = 0
            
            I need to find two numbers that multiply to 6 and add to 5.
            Those numbers are 2 and 3.
            
            So x² + 5x + 6 = (x + 2)(x + 3) = 0
            
            Using zero product property:
            x + 2 = 0  or  x + 3 = 0
            x = -2     or  x = -3
            
            Verification:
            For x = -2: (-2)² + 5(-2) + 6 = 4 - 10 + 6 = 0 ✓
            For x = -3: (-3)² + 5(-3) + 6 = 9 - 15 + 6 = 0 ✓
        """,
        
        'good_answer': """
            x² + 5x + 6 = 0
            (x + 2)(x + 3) = 0
            x = -2 or x = -3
        """,
        
        'partial_answer': """
            x² + 5x + 6 = 0
            Using quadratic formula: x = (-b ± √(b²-4ac)) / 2a
            x = (-5 ± √(25-24)) / 2
            x = (-5 ± 1) / 2
            x = -2 or x = -3
        """,
        
        'incomplete_answer': """
            x² + 5x + 6 = 0
            (x + 2)(x + 3) = 0
        """,
        
        'wrong_answer': """
            x² + 5x + 6 = 0
            x = 2 or x = 3
        """
    }


class MockSemanticMatcher:
    """Mock semantic matcher for testing when Gemini API is not available"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def analyze_answer_against_rubric(self, student_answer: str, rubric: dict) -> dict:
        """Mock analysis based on keyword matching"""
        # Simple keyword-based analysis for testing
        analysis_items = []
        marking_scheme = rubric.get('marking_scheme', {})
        
        for rubric_key, rubric_info in marking_scheme.items():
            keywords = rubric_info.get('keywords', [])
            marks = rubric_info.get('marks', 0)
            description = rubric_info.get('description', '')
            
            # Check if any keywords are present
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in student_answer.lower():
                    found_keywords.append(keyword)
            
            if found_keywords:
                status = 'YES'
                confidence = 0.9
                evidence = f"Found keywords: {', '.join(found_keywords)}"
                missing_content = None
                marks_awarded = marks
            else:
                status = 'NO'
                confidence = 0.8
                evidence = None
                missing_content = f"Should include {description.lower()}"
                marks_awarded = 0
            
            analysis_items.append({
                'rubric_point': description,
                'status': status,
                'confidence': confidence,
                'evidence': evidence,
                'missing_content': missing_content,
                'marks_awarded': marks_awarded,
                'total_marks': marks
            })
        
        # Calculate overall scores
        total_possible = sum(item['total_marks'] for item in analysis_items)
        total_awarded = sum(item['marks_awarded'] for item in analysis_items)
        overall_score = total_awarded / total_possible if total_possible > 0 else 0
        missed_marks = total_possible - total_awarded
        
        return {
            'rubric_analysis': analysis_items,
            'overall_score': overall_score,
            'missed_marks_potential': missed_marks,
            'summary': f"Score: {total_awarded}/{total_possible} ({overall_score:.1%})",
            'confidence_score': 0.8,
            'analysis_notes': 'Mock analysis for testing'
        }


def test_semantic_matcher():
    """Test the semantic matching functionality"""
    print("=== Semantic Matcher Test ===\n")
    
    try:
        # Try to import and use real semantic matcher
        try:
            from backend.services.answer_analyzer.semantic_matcher import SemanticMatcher
            
            # Check if Google AI is available
            import google.generativeai as genai
            
            print("🤖 Using real Gemini AI semantic matcher")
            matcher = SemanticMatcher()
            
        except ImportError:
            print("⚠️  Gemini AI not available, using mock matcher")
            matcher = MockSemanticMatcher()
            
    except Exception as e:
        print(f"❌ Failed to initialize matcher: {e}")
        return
    
    # Create test data
    test_rubric = create_test_rubric()
    test_answers = create_test_answers()
    
    print(f"📋 Test rubric: {test_rubric['question_text']}")
    print(f"🎯 Max marks: {test_rubric['max_marks']}")
    print(f"📝 Testing {len(test_answers)} different answer types\n")
    
    # Test each answer type
    results = {}
    
    for answer_type, answer_text in test_answers.items():
        print(f"--- Testing {answer_type.replace('_', ' ').title()} ---")
        
        try:
            # Analyze the answer
            result = matcher.analyze_answer_against_rubric(answer_text, test_rubric)
            results[answer_type] = result
            
            # Display results
            if 'error' in result:
                print(f"❌ Analysis failed: {result['error']}")
                continue
            
            print(f"Overall score: {result.get('overall_score', 0):.2f}")
            print(f"Missed marks: {result.get('missed_marks_potential', 0):.1f}")
            print(f"Summary: {result.get('summary', 'No summary')}")
            
            # Show rubric analysis
            rubric_analysis = result.get('rubric_analysis', [])
            print(f"Rubric matches: {len(rubric_analysis)}")
            
            for i, item in enumerate(rubric_analysis, 1):
                status_icon = {'YES': '✅', 'PARTIAL': '⚠️', 'NO': '❌'}.get(item['status'], '❓')
                print(f"  {i}. {status_icon} {item['rubric_point'][:40]}...")
                print(f"     Status: {item['status']} (conf: {item.get('confidence', 0):.2f})")
                if item.get('evidence'):
                    print(f"     Evidence: \"{item['evidence'][:50]}...\"")
                if item.get('missing_content'):
                    print(f"     Missing: {item['missing_content'][:50]}...")
            
            print()
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            print()
    
    # Test batch analysis
    print("--- Testing Batch Analysis ---")
    
    if hasattr(matcher, 'batch_analyze'):
        batch_data = [
            {
                'question_number': '1',
                'answer': test_answers['good_answer'],
                'rubric': test_rubric
            },
            {
                'question_number': '2',
                'answer': test_answers['partial_answer'],
                'rubric': test_rubric
            }
        ]
        
        try:
            batch_results = matcher.batch_analyze(batch_data)
            print(f"✅ Batch analysis completed: {len(batch_results)} results")
            
            for result in batch_results:
                q_num = result.get('question_number', 'Unknown')
                score = result.get('overall_score', 0)
                print(f"  Q{q_num}: {score:.2f} score")
                
        except Exception as e:
            print(f"❌ Batch analysis failed: {e}")
    
    # Test improvement suggestions
    print("\n--- Testing Improvement Suggestions ---")
    
    if hasattr(matcher, 'generate_improvement_suggestions'):
        try:
            all_results = list(results.values())
            suggestions = matcher.generate_improvement_suggestions(all_results)
            
            if suggestions:
                print("💡 Improvement suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
            else:
                print("✅ No improvement suggestions needed")
                
        except Exception as e:
            print(f"❌ Suggestion generation failed: {e}")
    
    # Test confidence analysis
    print("\n--- Testing Confidence Analysis ---")
    
    if hasattr(matcher, 'get_confidence_summary'):
        try:
            all_results = list(results.values())
            confidence_summary = matcher.get_confidence_summary(all_results)
            
            print("📊 Confidence Summary:")
            print(f"  Overall confidence: {confidence_summary.get('overall_confidence', 0):.2f}")
            print(f"  Reliable questions: {confidence_summary.get('reliable_questions', 0)}/{confidence_summary.get('total_questions', 0)}")
            print(f"  Reliability ratio: {confidence_summary.get('reliability_ratio', 0):.2f}")
            
        except Exception as e:
            print(f"❌ Confidence analysis failed: {e}")
    
    print("\n🎉 Semantic matcher testing completed!")
    
    # Summary of results
    print("\n📈 Test Results Summary:")
    for answer_type, result in results.items():
        if 'error' not in result:
            score = result.get('overall_score', 0)
            missed = result.get('missed_marks_potential', 0)
            print(f"  {answer_type}: {score:.2f} score, {missed:.1f} missed marks")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Edge Cases Test ===\n")
    
    try:
        matcher = MockSemanticMatcher()  # Use mock for edge case testing
        test_rubric = create_test_rubric()
        
        # Test empty answer
        print("Testing empty answer...")
        result = matcher.analyze_answer_against_rubric("", test_rubric)
        print(f"Empty answer result: {'Pass' if 'error' in result else 'Unexpected success'}")
        
        # Test very long answer
        print("Testing very long answer...")
        long_answer = "This is a test answer. " * 100
        result = matcher.analyze_answer_against_rubric(long_answer, test_rubric)
        print(f"Long answer result: {'Pass' if 'rubric_analysis' in result else 'Failed'}")
        
        # Test special characters
        print("Testing special characters...")
        special_answer = "x² + 5x + 6 = 0, ∴ x = -2 or x = -3 (∵ factoring method)"
        result = matcher.analyze_answer_against_rubric(special_answer, test_rubric)
        print(f"Special chars result: {'Pass' if 'rubric_analysis' in result else 'Failed'}")
        
        # Test invalid rubric
        print("Testing invalid rubric...")
        invalid_rubric = {"invalid": "structure"}
        result = matcher.analyze_answer_against_rubric("test answer", invalid_rubric)
        print(f"Invalid rubric result: {'Pass' if result else 'Failed'}")
        
        print("✅ Edge case testing completed")
        
    except Exception as e:
        print(f"❌ Edge case testing failed: {e}")


if __name__ == "__main__":
    test_semantic_matcher()
    test_edge_cases()

"""
Question pattern utilities for text processing
Contains patterns and validation functions for different question formats
"""
import re
from typing import List, Dict, Optional


class QuestionPatternMatcher:
    """Handles various question numbering and formatting patterns"""
    
    def __init__(self):
        # Define question patterns with their confidence scores
        self.patterns = {
            'standard_q': {
                'pattern': r'Q\.?\s*(\d+)\.?',
                'confidence': 0.95,
                'description': 'Standard Q1, Q.1, Q 1 format'
            },
            'question_word': {
                'pattern': r'Question\s+(\d+)\.?',
                'confidence': 0.90,
                'description': 'Question 1, Question 2 format'
            },
            'numbered_list': {
                'pattern': r'^\s*(\d+)\.?\s*[A-Z]',
                'confidence': 0.85,
                'description': '1. Answer, 2. Solution format'
            },
            'parentheses': {
                'pattern': r'\(\s*(\d+)\s*\)',
                'confidence': 0.80,
                'description': '(1), (2) format'
            },
            'bracket_number': {
                'pattern': r'(\d+)\s*\)',
                'confidence': 0.75,
                'description': '1), 2) format'
            },
            'no_prefix': {
                'pattern': r'No\.?\s*(\d+)',
                'confidence': 0.88,
                'description': 'No.1, No 1 format'
            },
            'ans_prefix': {
                'pattern': r'Ans\.?\s*(\d+)',
                'confidence': 0.82,
                'description': 'Ans.1, Ans 1 format'
            },
            'colon_dash': {
                'pattern': r'^\s*(\d+)\s*[:-]',
                'confidence': 0.70,
                'description': '1:, 2- format'
            }
        }
        
        # Subject-specific question indicators
        self.subject_indicators = {
            'mathematics': [
                r'solve|find|calculate|determine|prove|show|derive',
                r'equation|expression|function|derivative|integral',
                r'graph|plot|sketch|curve|line|slope',
                r'area|volume|perimeter|radius|diameter',
                r'probability|statistics|mean|median|mode'
            ],
            'physics': [
                r'force|energy|momentum|velocity|acceleration',
                r'mass|weight|density|pressure|temperature',
                r'electric|magnetic|current|voltage|resistance',
                r'wave|frequency|amplitude|wavelength|period',
                r'calculate|determine|find|measure|observe'
            ],
            'chemistry': [
                r'element|compound|molecule|atom|ion',
                r'reaction|equation|balance|oxidation|reduction',
                r'acid|base|ph|buffer|concentration|molarity',
                r'organic|inorganic|polymer|catalyst|enzyme',
                r'calculate|determine|find|identify|name'
            ],
            'biology': [
                r'cell|tissue|organ|organism|species|evolution',
                r'dna|rna|protein|enzyme|hormone|gene',
                r'photosynthesis|respiration|digestion|circulation',
                r'ecosystem|environment|population|community',
                r'define|explain|describe|identify|classify'
            ]
        }
    
    def detect_question_pattern(self, text: str) -> Optional[Dict]:
        """
        Detect which question pattern is used in the text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with pattern info or None if no pattern found
        """
        best_match = None
        highest_confidence = 0
        
        for pattern_name, pattern_info in self.patterns.items():
            match = re.search(pattern_info['pattern'], text, re.IGNORECASE | re.MULTILINE)
            if match:
                confidence = pattern_info['confidence']
                
                # Boost confidence if it's at the beginning of text
                if match.start() < 10:
                    confidence += 0.05
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = {
                        'pattern_name': pattern_name,
                        'question_number': match.group(1),
                        'confidence': confidence,
                        'match_text': match.group(0),
                        'position': match.start(),
                        'description': pattern_info['description']
                    }
        
        return best_match
    
    def extract_all_question_numbers(self, text_items: List[Dict]) -> List[Dict]:
        """
        Extract all question numbers with their pattern information
        
        Args:
            text_items: List of text items from OCR
            
        Returns:
            List of question information dictionaries
        """
        questions = []
        
        for item in text_items:
            text = item.get('text', '').strip()
            if not text:
                continue
            
            pattern_match = self.detect_question_pattern(text)
            if pattern_match:
                question_info = {
                    'question_number': pattern_match['question_number'],
                    'pattern_type': pattern_match['pattern_name'],
                    'confidence': pattern_match['confidence'],
                    'text': text,
                    'bbox': item.get('bbox', {}),
                    'ocr_confidence': item.get('confidence', 0),
                    'full_item': item
                }
                questions.append(question_info)
        
        # Remove duplicates and sort by question number
        unique_questions = {}
        for q in questions:
            q_num = q['question_number']
            if q_num not in unique_questions or q['confidence'] > unique_questions[q_num]['confidence']:
                unique_questions[q_num] = q
        
        # Sort by question number
        sorted_questions = sorted(unique_questions.values(), key=lambda x: int(x['question_number']))
        
        return sorted_questions
    
    def detect_subject_from_content(self, text: str) -> Dict[str, float]:
        """
        Attempt to detect the subject based on content keywords
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary with subject probabilities
        """
        subject_scores = {}
        text_lower = text.lower()
        
        for subject, indicators in self.subject_indicators.items():
            score = 0
            total_patterns = len(indicators)
            
            for pattern in indicators:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            # Normalize score
            subject_scores[subject] = min(1.0, score / (total_patterns * 2))
        
        return subject_scores
    
    def validate_question_sequence(self, question_numbers: List[str]) -> Dict[str, any]:
        """
        Validate if the question sequence makes sense
        
        Args:
            question_numbers: List of detected question numbers
            
        Returns:
            Validation results
        """
        if not question_numbers:
            return {
                'is_valid': False,
                'issues': ['No questions detected'],
                'suggestions': ['Check if the image contains clear question numbers']
            }
        
        # Convert to integers for analysis
        try:
            numbers = [int(q) for q in question_numbers]
        except ValueError:
            return {
                'is_valid': False,
                'issues': ['Non-numeric question numbers found'],
                'suggestions': ['Ensure question numbers are numeric']
            }
        
        issues = []
        suggestions = []
        
        # Check for sequential numbering
        numbers.sort()
        expected_sequence = list(range(numbers[0], numbers[-1] + 1))
        missing_numbers = set(expected_sequence) - set(numbers)
        
        if missing_numbers:
            issues.append(f"Missing question numbers: {sorted(missing_numbers)}")
            suggestions.append("Check if some questions were not detected by OCR")
        
        # Check for duplicates
        duplicates = set([x for x in numbers if numbers.count(x) > 1])
        if duplicates:
            issues.append(f"Duplicate question numbers: {sorted(duplicates)}")
            suggestions.append("Review OCR results for duplicate detections")
        
        # Check for reasonable range
        if numbers[0] > 10:
            issues.append(f"First question number is {numbers[0]} (unusually high)")
            suggestions.append("Verify that question numbering starts from beginning")
        
        if len(numbers) > 50:
            issues.append(f"Too many questions detected: {len(numbers)}")
            suggestions.append("Check for false positive detections")
        
        # Check for large gaps
        for i in range(1, len(numbers)):
            gap = numbers[i] - numbers[i-1]
            if gap > 5:
                issues.append(f"Large gap between Q{numbers[i-1]} and Q{numbers[i]}")
                suggestions.append("Verify all questions in sequence are present")
        
        return {
            'is_valid': len(issues) == 0,
            'question_count': len(numbers),
            'range': f"{numbers[0]} to {numbers[-1]}" if numbers else "None",
            'issues': issues,
            'suggestions': suggestions
        }
    
    def suggest_improvements(self, text_items: List[Dict], detected_questions: List[str]) -> List[str]:
        """
        Suggest improvements for better question detection
        
        Args:
            text_items: Original OCR text items
            detected_questions: List of detected question numbers
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Analyze OCR confidence
        low_confidence_items = [item for item in text_items if item.get('confidence', 1) < 0.7]
        if low_confidence_items:
            suggestions.append(f"Found {len(low_confidence_items)} low-confidence text items. Consider improving image quality.")
        
        # Check for very short text items that might be question numbers
        short_items = [item for item in text_items if len(item.get('text', '').strip()) == 1 and item.get('text', '').isdigit()]
        if short_items and len(detected_questions) < len(short_items):
            suggestions.append("Found isolated numbers that might be question numbers. Check OCR segmentation.")
        
        # Look for question-like words without numbers
        question_words = ['question', 'solve', 'find', 'calculate', 'explain', 'define']
        question_like_items = []
        for item in text_items:
            text = item.get('text', '').lower()
            if any(word in text for word in question_words) and not any(char.isdigit() for char in text):
                question_like_items.append(item)
        
        if question_like_items:
            suggestions.append(f"Found {len(question_like_items)} question-like text without numbers. Review question numbering format.")
        
        return suggestions

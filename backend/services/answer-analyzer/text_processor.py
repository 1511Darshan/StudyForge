"""
Text processing service for StudyForge Answer Analyzer
Handles segmentation of text by questions and content analysis
"""
import re
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextSegment:
    """Represents a segment of text with metadata"""
    text: str
    question_number: str
    start_position: int
    end_position: int
    confidence: float
    bbox_info: Optional[Dict] = None
    

@dataclass
class QuestionBlock:
    """Represents a detected question block"""
    question_number: str
    question_text: str
    answer_text: str
    full_text: str
    position_info: Dict
    confidence: float


class TextProcessor:
    """Processes and segments OCR extracted text"""
    
    def __init__(self):
        # Question number patterns (in order of priority)
        self.question_patterns = [
            r'Q\.?\s*(\d+)\.?',                    # Q1., Q.1, Q 1
            r'Question\s+(\d+)\.?',                # Question 1, Question 1.
            r'^\s*(\d+)\.?\s*[A-Z]',              # 1. Answer, 2. Solution
            r'\(\s*(\d+)\s*\)',                   # (1), ( 1 )
            r'(\d+)\s*\)',                        # 1), 2)
            r'No\.?\s*(\d+)',                     # No.1, No 1
            r'Ans\.?\s*(\d+)',                    # Ans.1, Ans 1
            r'^\s*(\d+)\s*[:-]',                  # 1:, 2-
        ]
        
        # Patterns to identify question vs answer sections
        self.question_indicators = [
            r'solve|find|calculate|determine|prove|show|derive|explain|why|what|how|when|where',
            r'if|given|let|assume|suppose|consider',
            r'\?|\bmust\b|\bshall\b|\bwill\b'
        ]
        
        # Answer indicators
        self.answer_indicators = [
            r'solution|answer|result|therefore|hence|thus|so|because',
            r'given|substituting|solving|using|applying',
            r'step|method|procedure|process'
        ]
        
        # Mathematical content indicators
        self.math_patterns = [
            r'[a-zA-Z]\s*=\s*[^=]+',              # Variable assignments
            r'\d+\s*[+\-*/^]\s*\d+',              # Arithmetic operations
            r'[a-zA-Z]+\([^)]+\)',                # Functions
            r'\b(sin|cos|tan|log|ln|sqrt|exp)\b', # Mathematical functions
            r'\d+\s*[a-zA-Z]+\d*',                # Terms like 3x, 2y^2
            r'[=><≤≥≠±∞]',                        # Mathematical symbols
        ]
    
    def extract_question_numbers(self, text_data: List[Dict]) -> List[str]:
        """
        Extract question numbers from OCR text data
        
        Args:
            text_data: List of text items with coordinates from OCR
            
        Returns:
            Sorted list of detected question numbers
        """
        question_numbers = set()
        
        logger.info(f"Analyzing {len(text_data)} text items for question numbers")
        
        for item in text_data:
            text = item.get('text', '').strip()
            if not text:
                continue
                
            # Try each pattern
            for pattern in self.question_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if match.isdigit() and 1 <= int(match) <= 50:  # Reasonable question range
                        question_numbers.add(match)
                        logger.debug(f"Found question number '{match}' in text: '{text}'")
        
        # Convert to sorted list
        sorted_numbers = sorted(list(question_numbers), key=lambda x: int(x))
        logger.info(f"Detected question numbers: {sorted_numbers}")
        
        return sorted_numbers
    
    def segment_by_questions(self, text_data: List[Dict], question_numbers: List[str]) -> Dict[str, Dict]:
        """
        Group text by question numbers based on spatial layout
        
        Args:
            text_data: List of text items with coordinates from OCR
            question_numbers: List of question numbers to segment by
            
        Returns:
            Dictionary mapping question numbers to their text content
        """
        logger.info(f"Segmenting text into {len(question_numbers)} questions")
        
        # Initialize segments
        segments = {q_num: {
            'text_items': [],
            'question_text': '',
            'answer_text': '',
            'full_text': '',
            'position_info': {'start_y': float('inf'), 'end_y': 0}
        } for q_num in question_numbers}
        
        # Sort text items by vertical position (top to bottom)
        sorted_items = sorted(text_data, key=lambda x: x.get('bbox', {}).get('y', 0))
        
        current_question = None
        question_boundaries = self._detect_question_boundaries(sorted_items, question_numbers)
        
        for item in sorted_items:
            text = item.get('text', '').strip()
            bbox = item.get('bbox', {})
            y_pos = bbox.get('y', 0)
            
            # Determine which question this text belongs to
            found_question = self._assign_text_to_question(text, y_pos, question_boundaries, question_numbers)
            
            if found_question:
                current_question = found_question
            
            # Add to current question segment
            if current_question and current_question in segments:
                segments[current_question]['text_items'].append(item)
                
                # Update position info
                pos_info = segments[current_question]['position_info']
                pos_info['start_y'] = min(pos_info['start_y'], y_pos)
                pos_info['end_y'] = max(pos_info['end_y'], y_pos + bbox.get('height', 0))
        
        # Process each segment
        for q_num in segments:
            if segments[q_num]['text_items']:
                segments[q_num] = self._process_question_segment(segments[q_num], q_num)
            else:
                logger.warning(f"No text found for question {q_num}")
        
        # Remove empty segments
        segments = {k: v for k, v in segments.items() if v['full_text'].strip()}
        
        logger.info(f"Successfully segmented into {len(segments)} question blocks")
        return segments
    
    def _detect_question_boundaries(self, sorted_items: List[Dict], question_numbers: List[str]) -> Dict[str, int]:
        """
        Detect the Y-coordinate boundaries where each question starts
        
        Args:
            sorted_items: Text items sorted by Y position
            question_numbers: List of question numbers
            
        Returns:
            Dictionary mapping question numbers to their Y positions
        """
        boundaries = {}
        
        for item in sorted_items:
            text = item.get('text', '').strip()
            y_pos = item.get('bbox', {}).get('y', 0)
            
            # Check if this text contains a question number
            for q_num in question_numbers:
                for pattern in self.question_patterns:
                    if re.search(pattern.replace(r'(\d+)', q_num), text, re.IGNORECASE):
                        if q_num not in boundaries or y_pos < boundaries[q_num]:
                            boundaries[q_num] = y_pos
                        break
        
        logger.debug(f"Question boundaries: {boundaries}")
        return boundaries
    
    def _assign_text_to_question(self, text: str, y_pos: int, boundaries: Dict[str, int], 
                                question_numbers: List[str]) -> Optional[str]:
        """
        Determine which question a piece of text belongs to based on position
        
        Args:
            text: The text content
            y_pos: Y coordinate of the text
            boundaries: Question boundary positions
            question_numbers: List of question numbers
            
        Returns:
            Question number that this text belongs to, or None
        """
        # Direct question number detection
        for q_num in question_numbers:
            for pattern in self.question_patterns:
                if re.search(pattern.replace(r'(\d+)', q_num), text, re.IGNORECASE):
                    return q_num
        
        # Position-based assignment
        best_question = None
        min_distance = float('inf')
        
        for q_num in question_numbers:
            if q_num in boundaries:
                distance = abs(y_pos - boundaries[q_num])
                if distance < min_distance:
                    min_distance = distance
                    best_question = q_num
        
        return best_question
    
    def _process_question_segment(self, segment: Dict, question_number: str) -> Dict:
        """
        Process a question segment to separate question text from answer text
        
        Args:
            segment: Segment data with text items
            question_number: The question number
            
        Returns:
            Processed segment with separated question and answer text
        """
        # Combine all text
        all_text_parts = [item['text'] for item in segment['text_items']]
        full_text = ' '.join(all_text_parts)
        
        # Clean up the text
        full_text = self._clean_text(full_text)
        
        # Try to separate question from answer
        question_text, answer_text = self._separate_question_answer(full_text, question_number)
        
        segment.update({
            'question_text': question_text,
            'answer_text': answer_text,
            'full_text': full_text
        })
        
        logger.debug(f"Processed Q{question_number}: {len(question_text)} chars question, {len(answer_text)} chars answer")
        
        return segment
    
    def _separate_question_answer(self, text: str, question_number: str) -> Tuple[str, str]:
        """
        Attempt to separate question text from answer text
        
        Args:
            text: Combined text for the question
            question_number: Question number
            
        Returns:
            Tuple of (question_text, answer_text)
        """
        # Look for answer indicators
        answer_patterns = [
            r'(?i)(solution|answer|ans|solve|solving)[:.]?\s*',
            r'(?i)(given|substituting|using|applying)[:.]?\s*',
            r'(?i)(step\s*\d+|method|procedure)[:.]?\s*',
            r'(?i)(therefore|hence|thus|so)[:.]?\s*'
        ]
        
        best_split = 0
        for pattern in answer_patterns:
            match = re.search(pattern, text)
            if match:
                split_pos = match.start()
                if split_pos > best_split:
                    best_split = split_pos
        
        if best_split > 0:
            question_text = text[:best_split].strip()
            answer_text = text[best_split:].strip()
        else:
            # If no clear separation, assume first sentence is question
            sentences = re.split(r'[.!?]+', text, 1)
            if len(sentences) >= 2:
                question_text = sentences[0].strip() + '.'
                answer_text = sentences[1].strip()
            else:
                # Fallback: treat entire text as answer
                question_text = f"Question {question_number}"
                answer_text = text.strip()
        
        return question_text, answer_text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common OCR errors in mathematical context
        replacements = {
            # Mathematical symbols
            '×': '*',
            '÷': '/',
            '−': '-',
            '≤': '<=',
            '≥': '>=',
            '≠': '!=',
            '√': 'sqrt',
            '²': '^2',
            '³': '^3',
            # Common character confusions
            '|': 'I',  # Only in non-mathematical contexts
            'l': '1',   # Only when surrounded by numbers
            'O': '0',   # Only when in numerical contexts
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Fix spacing around mathematical operators
        text = re.sub(r'\s*([=+\-*/^<>])\s*', r' \1 ', text)
        
        # Clean up multiple spaces again
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def extract_mathematical_content(self, text: str) -> Dict[str, List[str]]:
        """
        Extract mathematical expressions and formulas from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary categorizing different types of mathematical content
        """
        math_content = {
            'equations': [],
            'expressions': [],
            'functions': [],
            'variables': [],
            'numbers': []
        }
        
        # Extract equations (contains = sign)
        equations = re.findall(r'[^=]*=[^=]*', text)
        math_content['equations'] = [eq.strip() for eq in equations if eq.strip()]
        
        # Extract mathematical expressions
        for pattern in self.math_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if 'functions' in pattern:
                math_content['functions'].extend(matches)
            else:
                math_content['expressions'].extend(matches)
        
        # Extract variables (single letters possibly with subscripts/superscripts)
        variables = re.findall(r'\b[a-zA-Z](?:[_\d]*|\^\d+)?\b', text)
        math_content['variables'] = list(set(var for var in variables if len(var) <= 3))
        
        # Extract numbers
        numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
        math_content['numbers'] = list(set(numbers))
        
        # Remove duplicates and empty entries
        for key in math_content:
            math_content[key] = list(set(item.strip() for item in math_content[key] if item.strip()))
        
        return math_content
    
    def analyze_text_structure(self, segments: Dict[str, Dict]) -> Dict[str, any]:
        """
        Analyze the overall structure and quality of segmented text
        
        Args:
            segments: Segmented question text
            
        Returns:
            Analysis results
        """
        analysis = {
            'total_questions': len(segments),
            'total_words': 0,
            'avg_answer_length': 0,
            'mathematical_content_ratio': 0,
            'confidence_score': 0,
            'quality_issues': []
        }
        
        if not segments:
            analysis['quality_issues'].append("No text segments found")
            return analysis
        
        word_counts = []
        math_content_count = 0
        total_chars = 0
        
        for q_num, segment in segments.items():
            text = segment.get('full_text', '')
            words = len(text.split())
            word_counts.append(words)
            total_chars += len(text)
            
            # Check for mathematical content
            math_content = self.extract_mathematical_content(text)
            if any(math_content.values()):
                math_content_count += 1
            
            # Quality checks
            if words < 3:
                analysis['quality_issues'].append(f"Question {q_num} has very short answer")
            
            if not any(char.isalpha() for char in text):
                analysis['quality_issues'].append(f"Question {q_num} contains no readable text")
        
        # Calculate metrics
        analysis['total_words'] = sum(word_counts)
        analysis['avg_answer_length'] = sum(word_counts) / len(word_counts) if word_counts else 0
        analysis['mathematical_content_ratio'] = math_content_count / len(segments) if segments else 0
        
        # Calculate confidence score based on various factors
        confidence = 1.0
        if analysis['avg_answer_length'] < 5:
            confidence *= 0.7
        if len(analysis['quality_issues']) > 0:
            confidence *= max(0.3, 1.0 - len(analysis['quality_issues']) * 0.2)
        if total_chars < 100:
            confidence *= 0.8
        
        analysis['confidence_score'] = round(confidence, 2)
        
        logger.info(f"Text structure analysis: {analysis['total_questions']} questions, "
                   f"confidence: {analysis['confidence_score']}")
        
        return analysis
    
    def get_question_context(self, segments: Dict[str, Dict], target_question: str) -> Dict[str, str]:
        """
        Get context around a specific question (previous/next questions)
        
        Args:
            segments: All question segments
            target_question: Question number to get context for
            
        Returns:
            Dictionary with context information
        """
        question_numbers = sorted([int(q) for q in segments.keys() if q.isdigit()])
        target_num = int(target_question) if target_question.isdigit() else None
        
        context = {
            'previous_question': '',
            'next_question': '',
            'related_content': []
        }
        
        if target_num is None:
            return context
        
        # Find previous and next questions
        target_index = None
        try:
            target_index = question_numbers.index(target_num)
        except ValueError:
            return context
        
        if target_index > 0:
            prev_q = str(question_numbers[target_index - 1])
            context['previous_question'] = segments.get(prev_q, {}).get('full_text', '')
        
        if target_index < len(question_numbers) - 1:
            next_q = str(question_numbers[target_index + 1])
            context['next_question'] = segments.get(next_q, {}).get('full_text', '')
        
        # Find related mathematical content
        target_math = self.extract_mathematical_content(
            segments.get(target_question, {}).get('full_text', '')
        )
        
        for q_num, segment in segments.items():
            if q_num != target_question:
                q_math = self.extract_mathematical_content(segment.get('full_text', ''))
                # Check for overlapping variables or functions
                if (set(target_math['variables']) & set(q_math['variables']) or
                    set(target_math['functions']) & set(q_math['functions'])):
                    context['related_content'].append(q_num)
        
        return context

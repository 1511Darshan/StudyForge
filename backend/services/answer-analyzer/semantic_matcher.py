"""
Semantic matching service for StudyForge Answer Analyzer
Uses AI/LLM to compare student answers with marking rubrics
"""
import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class RubricMatch:
    """Represents a match between student answer and rubric point"""
    rubric_point: str
    status: str  # YES, NO, PARTIAL
    confidence: float
    evidence: Optional[str]
    missing_content: Optional[str]
    marks_awarded: float
    total_marks: float


@dataclass
class AnalysisResult:
    """Complete analysis result for a question"""
    question_number: str
    rubric_matches: List[RubricMatch]
    overall_score: float
    missed_marks_potential: float
    summary: str
    confidence_score: float


class SemanticMatcher:
    """Semantic matching service using Google Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize semantic matcher
        
        Args:
            api_key: Google Gemini API key (if not set via environment)
        """
        self.api_key = api_key
        self.model = None
        self.confidence_threshold = 0.7  # Minimum confidence for flagging issues
        
        # Initialize Gemini model
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini model"""
        try:
            import google.generativeai as genai
            
            # Use provided API key or get from environment
            if self.api_key:
                genai.configure(api_key=self.api_key)
            else:
                # Assume API key is already configured in environment
                pass
            
            # Use Gemini Pro model for text analysis
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("Gemini AI model initialized successfully")
            
        except ImportError:
            logger.error("Google Generative AI library not found. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    def analyze_answer_against_rubric(self, student_answer: str, rubric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare student answer with marking rubric using LLM
        
        Args:
            student_answer: The student's written answer
            rubric: Dictionary containing marking scheme and criteria
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Analyzing answer ({len(student_answer)} chars) against rubric")
            
            # Validate inputs
            if not student_answer.strip():
                return self._get_error_response("Empty student answer")
            
            if not rubric or not isinstance(rubric, dict):
                return self._get_error_response("Invalid rubric format")
            
            # Build analysis prompt
            prompt = self._build_analysis_prompt(student_answer, rubric)
            
            # Generate analysis using Gemini
            start_time = time.time()
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistent analysis
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
            )
            
            analysis_time = time.time() - start_time
            logger.info(f"LLM analysis completed in {analysis_time:.2f} seconds")
            
            # Parse and validate response
            result = self._parse_llm_response(response.text)
            
            # Apply confidence filtering
            filtered_result = self._filter_by_confidence(result)
            
            logger.info(f"Analysis complete: {len(filtered_result.get('rubric_analysis', []))} high-confidence matches")
            
            return filtered_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._get_error_response("Invalid response format from AI model")
        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
            return self._get_error_response(str(e))
    
    def _build_analysis_prompt(self, student_answer: str, rubric: Dict[str, Any]) -> str:
        """
        Build the analysis prompt for the LLM
        
        Args:
            student_answer: Student's answer text
            rubric: Marking rubric dictionary
            
        Returns:
            Formatted prompt string
        """
        # Extract rubric information
        marking_scheme = rubric.get('marking_scheme', {})
        model_answer = rubric.get('model_answer', '')
        keywords = rubric.get('keywords', [])
        max_marks = rubric.get('max_marks', 0)
        
        prompt = f"""You are an expert examiner analyzing a student's answer against a detailed marking rubric. 

STUDENT ANSWER:
{student_answer}

MODEL ANSWER (for reference):
{model_answer}

MARKING RUBRIC:
{json.dumps(marking_scheme, indent=2)}

KEYWORDS TO LOOK FOR:
{', '.join(keywords) if keywords else 'None specified'}

MAXIMUM MARKS: {max_marks}

ANALYSIS INSTRUCTIONS:
For each rubric point in the marking scheme, determine:

1. STATUS: Is this concept/point addressed in the student's answer?
   - YES: Clearly and correctly addressed
   - PARTIAL: Partially addressed or minor errors
   - NO: Not addressed or major errors

2. CONFIDENCE: How confident are you in this assessment? (0.0 to 1.0)
   - Only flag as missing (NO/PARTIAL) if confidence > 0.7
   - Be conservative to avoid false positives

3. EVIDENCE: Quote the exact text from student answer that supports your assessment
   - If STATUS is YES or PARTIAL, provide the relevant quote
   - If STATUS is NO, evidence should be null

4. MISSING CONTENT: If STATUS is NO or PARTIAL, what specific content should be added?
   - Be specific and actionable
   - Focus on the key concept that's missing

5. MARKS: Calculate partial marks based on the rubric point's total marks

IMPORTANT GUIDELINES:
- Prioritize accuracy over completeness - only flag clear issues
- Consider alternative valid approaches the student might have used
- Mathematical answers may use different but equivalent methods
- Focus on understanding rather than exact wording
- Be lenient with minor notation differences

Respond in this exact JSON format:
{{
    "rubric_analysis": [
        {{
            "rubric_point": "description of what should be covered",
            "status": "YES/NO/PARTIAL",
            "confidence": 0.85,
            "evidence": "exact quote from student answer or null",
            "missing_content": "what should be added if status is NO/PARTIAL",
            "marks_awarded": 2.5,
            "total_marks": 3.0
        }}
    ],
    "overall_score": 0.75,
    "missed_marks_potential": 2.5,
    "summary": "Brief summary of student's performance",
    "analysis_notes": "Any additional observations"
}}"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate LLM response
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed response dictionary
        """
        # Clean the response text
        cleaned_text = self._clean_response_text(response_text)
        
        try:
            # Parse JSON
            result = json.loads(cleaned_text)
            
            # Validate structure
            self._validate_response_structure(result)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.debug(f"Cleaned response text: {cleaned_text[:500]}...")
            
            # Try to extract JSON from response if it's embedded
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            raise
    
    def _clean_response_text(self, text: str) -> str:
        """
        Clean and prepare response text for JSON parsing
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned text
        """
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Find the JSON object (starts with { and ends with })
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
        
        return text
    
    def _validate_response_structure(self, result: Dict[str, Any]):
        """
        Validate that the LLM response has the expected structure
        
        Args:
            result: Parsed response dictionary
            
        Raises:
            ValueError: If structure is invalid
        """
        required_fields = ['rubric_analysis', 'overall_score', 'missed_marks_potential', 'summary']
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate rubric_analysis structure
        if not isinstance(result['rubric_analysis'], list):
            raise ValueError("rubric_analysis must be a list")
        
        for i, item in enumerate(result['rubric_analysis']):
            required_item_fields = ['rubric_point', 'status', 'confidence']
            for field in required_item_fields:
                if field not in item:
                    raise ValueError(f"Missing field '{field}' in rubric_analysis item {i}")
            
            # Validate status values
            if item['status'] not in ['YES', 'NO', 'PARTIAL']:
                raise ValueError(f"Invalid status value: {item['status']}")
            
            # Validate confidence range
            confidence = item.get('confidence', 0)
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                raise ValueError(f"Invalid confidence value: {confidence}")
    
    def _filter_by_confidence(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter analysis results by confidence threshold to minimize false positives
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            Filtered result dictionary
        """
        if 'rubric_analysis' not in result:
            return result
        
        # Filter rubric analysis items
        high_confidence_items = []
        total_filtered_marks = 0
        
        for item in result['rubric_analysis']:
            confidence = item.get('confidence', 0)
            status = item.get('status', 'NO')
            
            # Keep all YES items regardless of confidence
            # Only filter NO/PARTIAL items by confidence
            if status == 'YES' or confidence >= self.confidence_threshold:
                high_confidence_items.append(item)
            else:
                # Add back the marks that were potentially missed due to low confidence
                marks_diff = item.get('total_marks', 0) - item.get('marks_awarded', 0)
                total_filtered_marks += marks_diff
                logger.debug(f"Filtered low-confidence item: {item['rubric_point']} (conf: {confidence:.2f})")
        
        # Update the result
        filtered_result = result.copy()
        filtered_result['rubric_analysis'] = high_confidence_items
        
        # Adjust missed marks calculation
        original_missed = filtered_result.get('missed_marks_potential', 0)
        filtered_result['missed_marks_potential'] = max(0, original_missed - total_filtered_marks)
        
        # Add metadata about filtering
        filtered_result['filtering_info'] = {
            'confidence_threshold': self.confidence_threshold,
            'original_items': len(result['rubric_analysis']),
            'filtered_items': len(high_confidence_items),
            'marks_adjustment': total_filtered_marks
        }
        
        return filtered_result
    
    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """
        Return standardized error response
        
        Args:
            error_msg: Error message
            
        Returns:
            Error response dictionary
        """
        return {
            "error": error_msg,
            "rubric_analysis": [],
            "overall_score": 0,
            "missed_marks_potential": 0,
            "summary": "Analysis failed",
            "confidence_score": 0
        }
    
    def batch_analyze(self, questions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple questions in batch
        
        Args:
            questions_data: List of question dictionaries with 'answer' and 'rubric' keys
            
        Returns:
            List of analysis results
        """
        results = []
        
        logger.info(f"Starting batch analysis of {len(questions_data)} questions")
        
        for i, question_data in enumerate(questions_data, 1):
            try:
                logger.info(f"Analyzing question {i}/{len(questions_data)}")
                
                answer = question_data.get('answer', '')
                rubric = question_data.get('rubric', {})
                question_number = question_data.get('question_number', str(i))
                
                # Analyze individual question
                analysis = self.analyze_answer_against_rubric(answer, rubric)
                
                # Add question metadata
                analysis['question_number'] = question_number
                analysis['analysis_order'] = i
                
                results.append(analysis)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to analyze question {i}: {e}")
                error_result = self._get_error_response(f"Analysis failed: {str(e)}")
                error_result['question_number'] = question_data.get('question_number', str(i))
                results.append(error_result)
        
        logger.info(f"Batch analysis completed: {len(results)} results")
        return results
    
    def generate_improvement_suggestions(self, analysis_results: List[Dict[str, Any]]) -> List[str]:
        """
        Generate actionable improvement suggestions based on analysis results
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        missed_topics = set()
        
        for result in analysis_results:
            question_num = result.get('question_number', 'Unknown')
            
            for item in result.get('rubric_analysis', []):
                if item.get('status') in ['NO', 'PARTIAL'] and item.get('confidence', 0) >= self.confidence_threshold:
                    missing_content = item.get('missing_content', '')
                    if missing_content:
                        suggestions.append(f"Q{question_num}: {missing_content}")
                        
                        # Extract topic for pattern analysis
                        rubric_point = item.get('rubric_point', '').lower()
                        if 'formula' in rubric_point or 'equation' in rubric_point:
                            missed_topics.add('formula_application')
                        elif 'method' in rubric_point or 'procedure' in rubric_point:
                            missed_topics.add('methodology')
                        elif 'explanation' in rubric_point or 'reasoning' in rubric_point:
                            missed_topics.add('explanations')
        
        # Add general suggestions based on patterns
        if 'formula_application' in missed_topics:
            suggestions.append("General: Review and practice formula applications")
        
        if 'methodology' in missed_topics:
            suggestions.append("General: Focus on showing clear step-by-step methods")
        
        if 'explanations' in missed_topics:
            suggestions.append("General: Provide more detailed explanations for your reasoning")
        
        # Limit to top suggestions
        return suggestions[:8]
    
    def get_confidence_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate confidence summary for the analysis
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Confidence summary dictionary
        """
        if not analysis_results:
            return {'overall_confidence': 0, 'reliable_questions': 0, 'total_questions': 0}
        
        reliable_count = 0
        total_confidence = 0
        
        for result in analysis_results:
            # Consider a question reliable if it has high overall confidence
            question_confidence = result.get('confidence_score', result.get('overall_score', 0))
            total_confidence += question_confidence
            
            if question_confidence >= 0.7:
                reliable_count += 1
        
        return {
            'overall_confidence': total_confidence / len(analysis_results),
            'reliable_questions': reliable_count,
            'total_questions': len(analysis_results),
            'reliability_ratio': reliable_count / len(analysis_results)
        }

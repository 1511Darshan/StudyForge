"""
Main analyzer service for StudyForge Answer Analyzer
Orchestrates the complete analysis pipeline: OCR -> Text Processing -> Semantic Matching
"""
import os
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import time

from .ocr_service import OCRService
from .text_processor import TextProcessor
from .semantic_matcher import SemanticMatcher
from ...models.analyzer.models import AnswerAnalysis, QuestionRubric, AnalysisFeedback
from ...models.analyzer.database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis pipeline"""
    confidence_threshold: float = 0.7
    min_text_length: int = 10
    max_questions_per_sheet: int = 20
    enable_ai_analysis: bool = True
    save_intermediate_results: bool = True
    include_confidence_scores: bool = True


@dataclass
class QuestionAnalysisResult:
    """Result for a single question analysis"""
    question_number: str
    detected_text: str
    rubric_analysis: List[Dict[str, Any]]
    overall_score: float
    missed_marks: float
    total_marks: float
    confidence_score: float
    processing_time: float
    feedback: Optional[str] = None


@dataclass
class SheetAnalysisResult:
    """Complete analysis result for an answer sheet"""
    sheet_id: str
    student_id: Optional[str]
    total_questions: int
    analyzed_questions: int
    overall_score: float
    total_possible_marks: float
    percentage_score: float
    analysis_time: float
    confidence_score: float
    question_results: List[QuestionAnalysisResult]
    processing_errors: List[str]
    metadata: Dict[str, Any]


class AnalyzerService:
    """Main service orchestrating the complete answer sheet analysis pipeline"""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the analyzer service
        
        Args:
            config: Analysis configuration (uses defaults if not provided)
        """
        self.config = config or AnalysisConfig()
        
        # Initialize component services
        self.ocr_service = OCRService()
        self.text_processor = TextProcessor()
        self.semantic_matcher = SemanticMatcher() if self.config.enable_ai_analysis else None
        self.db_manager = DatabaseManager()
        
        logger.info("AnalyzerService initialized with configuration:")
        logger.info(f"  - AI Analysis: {self.config.enable_ai_analysis}")
        logger.info(f"  - Confidence threshold: {self.config.confidence_threshold}")
        logger.info(f"  - Max questions per sheet: {self.config.max_questions_per_sheet}")
    
    def analyze_answer_sheet(
        self, 
        image_path: str, 
        rubrics: List[Dict[str, Any]], 
        student_id: Optional[str] = None,
        sheet_id: Optional[str] = None
    ) -> SheetAnalysisResult:
        """
        Analyze a complete answer sheet image against provided rubrics
        
        Args:
            image_path: Path to the answer sheet image
            rubrics: List of rubric dictionaries for each question
            student_id: Optional student identifier
            sheet_id: Optional sheet identifier (generated if not provided)
            
        Returns:
            Complete analysis result
        """
        start_time = time.time()
        sheet_id = sheet_id or f"sheet_{int(time.time())}"
        
        logger.info(f"Starting analysis of sheet {sheet_id} with {len(rubrics)} rubrics")
        
        try:
            # Step 1: Extract text from image using OCR
            logger.info("Step 1: Extracting text from answer sheet")
            ocr_result = self.ocr_service.extract_text_from_image(image_path)
            
            if not ocr_result or 'error' in ocr_result:
                error_msg = ocr_result.get('error', 'OCR extraction failed') if ocr_result else 'OCR service returned no result'
                return self._create_error_result(sheet_id, student_id, error_msg, start_time)
            
            extracted_text = ocr_result.get('text', '')
            text_coordinates = ocr_result.get('coordinates', [])
            
            if len(extracted_text) < self.config.min_text_length:
                return self._create_error_result(sheet_id, student_id, "Insufficient text extracted from image", start_time)
            
            logger.info(f"OCR completed: {len(extracted_text)} characters extracted")
            
            # Step 2: Process and segment text by questions
            logger.info("Step 2: Processing and segmenting text by questions")
            text_processing_result = self.text_processor.segment_by_questions(
                extracted_text, 
                text_coordinates
            )
            
            if 'error' in text_processing_result:
                return self._create_error_result(sheet_id, student_id, text_processing_result['error'], start_time)
            
            question_segments = text_processing_result.get('question_segments', [])
            processing_metadata = text_processing_result.get('metadata', {})
            
            logger.info(f"Text processing completed: {len(question_segments)} question segments identified")
            
            # Step 3: Analyze each question against its rubric
            logger.info("Step 3: Analyzing questions against rubrics")
            question_results = []
            processing_errors = []
            total_score = 0
            total_possible = 0
            total_confidence = 0
            
            # Create rubric lookup for efficiency
            rubric_lookup = {str(r.get('question_number', i+1)): r for i, r in enumerate(rubrics)}
            
            for segment in question_segments[:self.config.max_questions_per_sheet]:
                try:
                    result = self._analyze_single_question(segment, rubric_lookup)
                    if result:
                        question_results.append(result)
                        total_score += result.overall_score * result.total_marks
                        total_possible += result.total_marks
                        total_confidence += result.confidence_score
                        
                except Exception as e:
                    error_msg = f"Error analyzing question {segment.get('question_number', 'unknown')}: {str(e)}"
                    processing_errors.append(error_msg)
                    logger.error(error_msg)
            
            # Calculate overall metrics
            analysis_time = time.time() - start_time
            overall_score = total_score / total_possible if total_possible > 0 else 0
            percentage_score = overall_score * 100
            confidence_score = total_confidence / len(question_results) if question_results else 0
            
            # Create final result
            result = SheetAnalysisResult(
                sheet_id=sheet_id,
                student_id=student_id,
                total_questions=len(rubrics),
                analyzed_questions=len(question_results),
                overall_score=overall_score,
                total_possible_marks=total_possible,
                percentage_score=percentage_score,
                analysis_time=analysis_time,
                confidence_score=confidence_score,
                question_results=question_results,
                processing_errors=processing_errors,
                metadata={
                    'ocr_metadata': ocr_result.get('metadata', {}),
                    'text_processing_metadata': processing_metadata,
                    'config_used': asdict(self.config),
                    'rubrics_count': len(rubrics),
                    'image_path': image_path
                }
            )
            
            # Save to database if configured
            if self.config.save_intermediate_results:
                self._save_analysis_to_database(result)
            
            logger.info(f"Analysis completed: {percentage_score:.1f}% score, {confidence_score:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Critical error in analysis pipeline: {e}")
            return self._create_error_result(sheet_id, student_id, f"Pipeline error: {str(e)}", start_time)
    
    def _analyze_single_question(
        self, 
        question_segment: Dict[str, Any], 
        rubric_lookup: Dict[str, Dict[str, Any]]
    ) -> Optional[QuestionAnalysisResult]:
        """
        Analyze a single question segment against its rubric
        
        Args:
            question_segment: Question segment from text processor
            rubric_lookup: Dictionary mapping question numbers to rubrics
            
        Returns:
            Question analysis result or None if failed
        """
        start_time = time.time()
        
        question_number = str(question_segment.get('question_number', '1'))
        detected_text = question_segment.get('text', '')
        
        logger.debug(f"Analyzing question {question_number}: {len(detected_text)} characters")
        
        # Find matching rubric
        rubric = rubric_lookup.get(question_number)
        if not rubric:
            logger.warning(f"No rubric found for question {question_number}")
            return None
        
        if len(detected_text.strip()) < self.config.min_text_length:
            logger.warning(f"Insufficient text for question {question_number}")
            return None
        
        # Perform semantic analysis if AI is enabled
        rubric_analysis = []
        overall_score = 0
        missed_marks = 0
        confidence_score = 0.5  # Default confidence for non-AI analysis
        
        if self.semantic_matcher:
            try:
                semantic_result = self.semantic_matcher.analyze_answer_against_rubric(
                    detected_text, 
                    rubric
                )
                
                if 'error' not in semantic_result:
                    rubric_analysis = semantic_result.get('rubric_analysis', [])
                    overall_score = semantic_result.get('overall_score', 0)
                    missed_marks = semantic_result.get('missed_marks_potential', 0)
                    confidence_score = semantic_result.get('confidence_score', confidence_score)
                else:
                    logger.warning(f"Semantic analysis failed for Q{question_number}: {semantic_result['error']}")
                    
            except Exception as e:
                logger.error(f"Semantic analysis error for Q{question_number}: {e}")
        else:
            # Fallback to basic keyword matching
            rubric_analysis = self._basic_rubric_analysis(detected_text, rubric)
            overall_score = self._calculate_basic_score(rubric_analysis)
        
        processing_time = time.time() - start_time
        total_marks = rubric.get('max_marks', 0)
        
        return QuestionAnalysisResult(
            question_number=question_number,
            detected_text=detected_text,
            rubric_analysis=rubric_analysis,
            overall_score=overall_score,
            missed_marks=missed_marks,
            total_marks=total_marks,
            confidence_score=confidence_score,
            processing_time=processing_time
        )
    
    def _basic_rubric_analysis(self, text: str, rubric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform basic keyword-based rubric analysis when AI is not available
        
        Args:
            text: Student answer text
            rubric: Rubric dictionary
            
        Returns:
            List of basic analysis items
        """
        analysis_items = []
        marking_scheme = rubric.get('marking_scheme', {})
        text_lower = text.lower()
        
        for rubric_key, rubric_info in marking_scheme.items():
            keywords = rubric_info.get('keywords', [])
            marks = rubric_info.get('marks', 0)
            description = rubric_info.get('description', '')
            
            # Check keyword presence
            found_keywords = [kw for kw in keywords if kw.lower() in text_lower]
            
            if found_keywords:
                status = 'YES'
                confidence = 0.6  # Conservative confidence for keyword matching
                evidence = f"Found: {', '.join(found_keywords)}"
                marks_awarded = marks
            else:
                status = 'NO'
                confidence = 0.5
                evidence = None
                marks_awarded = 0
            
            analysis_items.append({
                'rubric_point': description,
                'status': status,
                'confidence': confidence,
                'evidence': evidence,
                'missing_content': f"Should include: {description}" if status == 'NO' else None,
                'marks_awarded': marks_awarded,
                'total_marks': marks
            })
        
        return analysis_items
    
    def _calculate_basic_score(self, analysis_items: List[Dict[str, Any]]) -> float:
        """Calculate overall score from basic analysis items"""
        if not analysis_items:
            return 0
        
        total_possible = sum(item['total_marks'] for item in analysis_items)
        total_awarded = sum(item['marks_awarded'] for item in analysis_items)
        
        return total_awarded / total_possible if total_possible > 0 else 0
    
    def _create_error_result(
        self, 
        sheet_id: str, 
        student_id: Optional[str], 
        error_msg: str, 
        start_time: float
    ) -> SheetAnalysisResult:
        """Create an error result for failed analysis"""
        return SheetAnalysisResult(
            sheet_id=sheet_id,
            student_id=student_id,
            total_questions=0,
            analyzed_questions=0,
            overall_score=0,
            total_possible_marks=0,
            percentage_score=0,
            analysis_time=time.time() - start_time,
            confidence_score=0,
            question_results=[],
            processing_errors=[error_msg],
            metadata={'error': error_msg}
        )
    
    def _save_analysis_to_database(self, result: SheetAnalysisResult):
        """Save analysis result to database"""
        try:
            # Create AnswerAnalysis record
            analysis_data = {
                'id': result.sheet_id,
                'student_id': result.student_id or 'unknown',
                'total_score': result.overall_score,
                'max_possible_score': result.total_possible_marks,
                'analysis_details': {
                    'question_results': [asdict(qr) for qr in result.question_results],
                    'metadata': result.metadata,
                    'processing_errors': result.processing_errors
                },
                'confidence_score': result.confidence_score,
                'processing_time': result.analysis_time,
                'created_at': datetime.now()
            }
            
            analysis = AnswerAnalysis(**analysis_data)
            self.db_manager.save_analysis(analysis)
            
            logger.info(f"Analysis result saved to database: {result.sheet_id}")
            
        except Exception as e:
            logger.error(f"Failed to save analysis to database: {e}")
    
    def get_analysis_history(self, student_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve analysis history from database
        
        Args:
            student_id: Filter by student ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of analysis records
        """
        try:
            analyses = self.db_manager.get_analyses(limit=limit)
            
            if student_id:
                analyses = [a for a in analyses if a.get('student_id') == student_id]
            
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis history: {e}")
            return []
    
    def generate_detailed_feedback(self, sheet_result: SheetAnalysisResult) -> Dict[str, Any]:
        """
        Generate detailed feedback for the analysis result
        
        Args:
            sheet_result: Complete sheet analysis result
            
        Returns:
            Detailed feedback dictionary
        """
        feedback = {
            'overall_performance': self._generate_overall_feedback(sheet_result),
            'question_feedback': [],
            'improvement_suggestions': [],
            'strengths': [],
            'areas_for_improvement': [],
            'confidence_assessment': self._assess_confidence(sheet_result)
        }
        
        # Generate question-specific feedback
        for q_result in sheet_result.question_results:
            q_feedback = {
                'question_number': q_result.question_number,
                'score': f"{q_result.overall_score * q_result.total_marks:.1f}/{q_result.total_marks}",
                'percentage': f"{q_result.overall_score * 100:.1f}%",
                'feedback': self._generate_question_feedback(q_result),
                'suggestions': self._extract_question_suggestions(q_result)
            }
            feedback['question_feedback'].append(q_feedback)
        
        # Generate improvement suggestions using semantic matcher if available
        if self.semantic_matcher:
            try:
                all_results = [{'rubric_analysis': qr.rubric_analysis, 'question_number': qr.question_number} 
                              for qr in sheet_result.question_results]
                suggestions = self.semantic_matcher.generate_improvement_suggestions(all_results)
                feedback['improvement_suggestions'] = suggestions
            except Exception as e:
                logger.error(f"Failed to generate improvement suggestions: {e}")
        
        # Identify strengths and areas for improvement
        feedback['strengths'], feedback['areas_for_improvement'] = self._analyze_performance_patterns(sheet_result)
        
        return feedback
    
    def _generate_overall_feedback(self, sheet_result: SheetAnalysisResult) -> str:
        """Generate overall performance feedback"""
        percentage = sheet_result.percentage_score
        
        if percentage >= 90:
            return f"Excellent work! You scored {percentage:.1f}%, demonstrating strong understanding across all topics."
        elif percentage >= 80:
            return f"Very good performance! You scored {percentage:.1f}% with solid understanding of most concepts."
        elif percentage >= 70:
            return f"Good work! You scored {percentage:.1f}%. There are a few areas where you can improve."
        elif percentage >= 60:
            return f"Fair performance at {percentage:.1f}%. Focus on understanding key concepts and practice more."
        else:
            return f"You scored {percentage:.1f}%. Consider reviewing the material and seeking additional help."
    
    def _generate_question_feedback(self, q_result: QuestionAnalysisResult) -> str:
        """Generate feedback for a specific question"""
        score_percentage = q_result.overall_score * 100
        
        if score_percentage >= 90:
            return "Excellent answer with clear understanding and proper methodology."
        elif score_percentage >= 80:
            return "Good answer with minor areas for improvement."
        elif score_percentage >= 60:
            return "Partial understanding shown, but missing some key elements."
        else:
            return "Needs significant improvement. Review the concept and practice similar problems."
    
    def _extract_question_suggestions(self, q_result: QuestionAnalysisResult) -> List[str]:
        """Extract suggestions from question analysis"""
        suggestions = []
        
        for item in q_result.rubric_analysis:
            if item.get('status') in ['NO', 'PARTIAL'] and item.get('missing_content'):
                suggestions.append(item['missing_content'])
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _assess_confidence(self, sheet_result: SheetAnalysisResult) -> Dict[str, Any]:
        """Assess confidence in the analysis"""
        confidence = sheet_result.confidence_score
        
        assessment = {
            'overall_confidence': confidence,
            'reliability': 'High' if confidence >= 0.8 else 'Medium' if confidence >= 0.6 else 'Low',
            'note': ''
        }
        
        if confidence < 0.6:
            assessment['note'] = "Low confidence - consider manual review of answers"
        elif confidence < 0.8:
            assessment['note'] = "Medium confidence - some answers may need verification"
        else:
            assessment['note'] = "High confidence - analysis is likely accurate"
        
        return assessment
    
    def _analyze_performance_patterns(self, sheet_result: SheetAnalysisResult) -> Tuple[List[str], List[str]]:
        """Analyze performance patterns to identify strengths and weaknesses"""
        strengths = []
        areas_for_improvement = []
        
        # Analyze by question performance
        high_scoring = [qr for qr in sheet_result.question_results if qr.overall_score >= 0.8]
        low_scoring = [qr for qr in sheet_result.question_results if qr.overall_score < 0.6]
        
        if len(high_scoring) >= len(sheet_result.question_results) * 0.7:
            strengths.append("Consistent good performance across most questions")
        
        if len(low_scoring) >= len(sheet_result.question_results) * 0.3:
            areas_for_improvement.append("Multiple questions need significant improvement")
        
        # Analyze common missing elements
        missing_patterns = {}
        for qr in sheet_result.question_results:
            for item in qr.rubric_analysis:
                if item.get('status') == 'NO':
                    pattern = item.get('rubric_point', '').lower()
                    if 'method' in pattern:
                        missing_patterns['methodology'] = missing_patterns.get('methodology', 0) + 1
                    elif 'explanation' in pattern:
                        missing_patterns['explanations'] = missing_patterns.get('explanations', 0) + 1
                    elif 'calculation' in pattern or 'formula' in pattern:
                        missing_patterns['calculations'] = missing_patterns.get('calculations', 0) + 1
        
        # Add pattern-based feedback
        total_questions = len(sheet_result.question_results)
        for pattern, count in missing_patterns.items():
            if count >= total_questions * 0.3:  # Missing in 30% or more questions
                areas_for_improvement.append(f"Focus on improving {pattern}")
        
        return strengths, areas_for_improvement
    
    def validate_rubrics(self, rubrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate rubric format and content
        
        Args:
            rubrics: List of rubric dictionaries
            
        Returns:
            Validation result with any errors
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'rubric_count': len(rubrics)
        }
        
        for i, rubric in enumerate(rubrics):
            rubric_errors = []
            
            # Check required fields
            required_fields = ['question_number', 'marking_scheme', 'max_marks']
            for field in required_fields:
                if field not in rubric:
                    rubric_errors.append(f"Missing required field: {field}")
            
            # Validate marking scheme structure
            if 'marking_scheme' in rubric:
                marking_scheme = rubric['marking_scheme']
                if not isinstance(marking_scheme, dict):
                    rubric_errors.append("marking_scheme must be a dictionary")
                else:
                    for key, value in marking_scheme.items():
                        if not isinstance(value, dict):
                            rubric_errors.append(f"marking_scheme[{key}] must be a dictionary")
                        elif 'marks' not in value:
                            rubric_errors.append(f"marking_scheme[{key}] missing 'marks' field")
            
            # Validate max_marks
            if 'max_marks' in rubric:
                try:
                    max_marks = float(rubric['max_marks'])
                    if max_marks <= 0:
                        rubric_errors.append("max_marks must be positive")
                except (ValueError, TypeError):
                    rubric_errors.append("max_marks must be a number")
            
            if rubric_errors:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'rubric_index': i,
                    'question_number': rubric.get('question_number', 'unknown'),
                    'errors': rubric_errors
                })
        
        return validation_result

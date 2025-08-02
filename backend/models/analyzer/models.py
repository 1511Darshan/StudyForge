"""
Database models for StudyForge Answer Analyzer
"""
from datetime import datetime
from typing import Dict, Any

# Since we're using Flask, I'll create models compatible with Flask-SQLAlchemy
# These can be easily integrated with the existing Flask app

class AnswerAnalysis:
    """Model for storing answer sheet analysis results"""
    
    def __init__(self):
        self.id: str = ""
        self.student_id: str = ""
        self.subject: str = ""
        self.question_paper_url: str = ""
        self.answer_sheet_url: str = ""
        self.ocr_text: str = ""
        self.analysis_results: Dict[str, Any] = {}
        self.total_missed_marks: float = 0.0
        self.confidence_score: float = 0.0
        self.status: str = "processing"  # processing, completed, failed
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject': self.subject,
            'question_paper_url': self.question_paper_url,
            'answer_sheet_url': self.answer_sheet_url,
            'analysis_results': self.analysis_results,
            'total_missed_marks': self.total_missed_marks,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnswerAnalysis':
        """Create model instance from dictionary"""
        instance = cls()
        instance.id = data.get('id', '')
        instance.student_id = data.get('student_id', '')
        instance.subject = data.get('subject', '')
        instance.question_paper_url = data.get('question_paper_url', '')
        instance.answer_sheet_url = data.get('answer_sheet_url', '')
        instance.analysis_results = data.get('analysis_results', {})
        instance.total_missed_marks = data.get('total_missed_marks', 0.0)
        instance.confidence_score = data.get('confidence_score', 0.0)
        instance.status = data.get('status', 'processing')
        
        # Parse datetime strings
        if data.get('created_at'):
            instance.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if data.get('updated_at'):
            instance.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            
        return instance


class QuestionRubric:
    """Model for storing question rubrics and marking schemes"""
    
    def __init__(self):
        self.id: str = ""
        self.subject: str = ""
        self.question_number: str = ""
        self.question_text: str = ""
        self.model_answer: str = ""
        self.marking_scheme: Dict[str, Any] = {}
        self.keywords: list = []
        self.max_marks: int = 0
        self.created_by: str = ""
        self.created_at: datetime = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'subject': self.subject,
            'question_number': self.question_number,
            'question_text': self.question_text,
            'model_answer': self.model_answer,
            'marking_scheme': self.marking_scheme,
            'keywords': self.keywords,
            'max_marks': self.max_marks,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionRubric':
        """Create model instance from dictionary"""
        instance = cls()
        instance.id = data.get('id', '')
        instance.subject = data.get('subject', '')
        instance.question_number = data.get('question_number', '')
        instance.question_text = data.get('question_text', '')
        instance.model_answer = data.get('model_answer', '')
        instance.marking_scheme = data.get('marking_scheme', {})
        instance.keywords = data.get('keywords', [])
        instance.max_marks = data.get('max_marks', 0)
        instance.created_by = data.get('created_by', '')
        
        if data.get('created_at'):
            instance.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            
        return instance


class AnalysisFeedback:
    """Model for storing student feedback on analysis results"""
    
    def __init__(self):
        self.id: str = ""
        self.analysis_id: str = ""
        self.student_id: str = ""
        self.question_number: str = ""
        self.feedback_type: str = ""  # dispute, confirm, suggestion
        self.feedback_text: str = ""
        self.is_resolved: str = "pending"  # pending, resolved, rejected
        self.created_at: datetime = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'student_id': self.student_id,
            'question_number': self.question_number,
            'feedback_type': self.feedback_type,
            'feedback_text': self.feedback_text,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisFeedback':
        """Create model instance from dictionary"""
        instance = cls()
        instance.id = data.get('id', '')
        instance.analysis_id = data.get('analysis_id', '')
        instance.student_id = data.get('student_id', '')
        instance.question_number = data.get('question_number', '')
        instance.feedback_type = data.get('feedback_type', '')
        instance.feedback_text = data.get('feedback_text', '')
        instance.is_resolved = data.get('is_resolved', 'pending')
        
        if data.get('created_at'):
            instance.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            
        return instance

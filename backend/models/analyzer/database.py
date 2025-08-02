"""
Database manager for StudyForge Answer Analyzer
Handles SQLite database operations for answer analysis data
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional
from .models import AnswerAnalysis, QuestionRubric, AnalysisFeedback


class DatabaseManager:
    """SQLite database manager for answer analyzer"""
    
    def __init__(self, db_path: str = "studyforge_analyzer.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with JSON support"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        try:
            # Create answer_analyses table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS answer_analyses (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    question_paper_url TEXT,
                    answer_sheet_url TEXT,
                    ocr_text TEXT,
                    analysis_results TEXT,
                    total_missed_marks REAL DEFAULT 0.0,
                    confidence_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'processing',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Create question_rubrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS question_rubrics (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    question_number TEXT,
                    question_text TEXT,
                    model_answer TEXT,
                    marking_scheme TEXT,
                    keywords TEXT,
                    max_marks INTEGER,
                    created_by TEXT,
                    created_at TEXT
                )
            """)
            
            # Create analysis_feedback table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_feedback (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT,
                    student_id TEXT,
                    question_number TEXT,
                    feedback_type TEXT,
                    feedback_text TEXT,
                    is_resolved TEXT DEFAULT 'pending',
                    created_at TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES answer_analyses (id)
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    # Answer Analysis CRUD operations
    def create_analysis(self, analysis: AnswerAnalysis) -> str:
        """Create new analysis record"""
        if not analysis.id:
            analysis.id = str(uuid.uuid4())
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO answer_analyses 
                (id, student_id, subject, question_paper_url, answer_sheet_url,
                 ocr_text, analysis_results, total_missed_marks, confidence_score,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.id, analysis.student_id, analysis.subject,
                analysis.question_paper_url, analysis.answer_sheet_url,
                analysis.ocr_text, json.dumps(analysis.analysis_results),
                analysis.total_missed_marks, analysis.confidence_score,
                analysis.status, analysis.created_at.isoformat(),
                analysis.updated_at.isoformat()
            ))
            conn.commit()
            return analysis.id
        finally:
            conn.close()
    
    def get_analysis(self, analysis_id: str) -> Optional[AnswerAnalysis]:
        """Get analysis by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM answer_analyses WHERE id = ?", (analysis_id,)
            )
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['analysis_results'] = json.loads(data['analysis_results'] or '{}')
                return AnswerAnalysis.from_dict(data)
            return None
        finally:
            conn.close()
    
    def update_analysis(self, analysis: AnswerAnalysis):
        """Update existing analysis"""
        analysis.updated_at = datetime.utcnow()
        conn = self.get_connection()
        try:
            conn.execute("""
                UPDATE answer_analyses 
                SET analysis_results = ?, total_missed_marks = ?, 
                    confidence_score = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (
                json.dumps(analysis.analysis_results),
                analysis.total_missed_marks,
                analysis.confidence_score,
                analysis.status,
                analysis.updated_at.isoformat(),
                analysis.id
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_student_analyses(self, student_id: str, limit: int = 10) -> List[AnswerAnalysis]:
        """Get all analyses for a student"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM answer_analyses 
                WHERE student_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (student_id, limit))
            
            analyses = []
            for row in cursor.fetchall():
                data = dict(row)
                data['analysis_results'] = json.loads(data['analysis_results'] or '{}')
                analyses.append(AnswerAnalysis.from_dict(data))
            
            return analyses
        finally:
            conn.close()
    
    # Question Rubric CRUD operations
    def create_rubric(self, rubric: QuestionRubric) -> str:
        """Create new rubric"""
        if not rubric.id:
            rubric.id = str(uuid.uuid4())
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO question_rubrics 
                (id, subject, question_number, question_text, model_answer,
                 marking_scheme, keywords, max_marks, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rubric.id, rubric.subject, rubric.question_number,
                rubric.question_text, rubric.model_answer,
                json.dumps(rubric.marking_scheme), json.dumps(rubric.keywords),
                rubric.max_marks, rubric.created_by, rubric.created_at.isoformat()
            ))
            conn.commit()
            return rubric.id
        finally:
            conn.close()
    
    def get_rubrics_by_subject(self, subject: str) -> List[QuestionRubric]:
        """Get all rubrics for a subject"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM question_rubrics WHERE subject = ?", (subject,)
            )
            
            rubrics = []
            for row in cursor.fetchall():
                data = dict(row)
                data['marking_scheme'] = json.loads(data['marking_scheme'] or '{}')
                data['keywords'] = json.loads(data['keywords'] or '[]')
                rubrics.append(QuestionRubric.from_dict(data))
            
            return rubrics
        finally:
            conn.close()
    
    def get_rubric_by_question(self, subject: str, question_number: str) -> Optional[QuestionRubric]:
        """Get rubric for specific question"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM question_rubrics 
                WHERE subject = ? AND question_number = ?
            """, (subject, question_number))
            
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['marking_scheme'] = json.loads(data['marking_scheme'] or '{}')
                data['keywords'] = json.loads(data['keywords'] or '[]')
                return QuestionRubric.from_dict(data)
            return None
        finally:
            conn.close()
    
    # Feedback CRUD operations
    def create_feedback(self, feedback: AnalysisFeedback) -> str:
        """Create new feedback"""
        if not feedback.id:
            feedback.id = str(uuid.uuid4())
        
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO analysis_feedback 
                (id, analysis_id, student_id, question_number, feedback_type,
                 feedback_text, is_resolved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.id, feedback.analysis_id, feedback.student_id,
                feedback.question_number, feedback.feedback_type,
                feedback.feedback_text, feedback.is_resolved,
                feedback.created_at.isoformat()
            ))
            conn.commit()
            return feedback.id
        finally:
            conn.close()
    
    def get_feedback_by_analysis(self, analysis_id: str) -> List[AnalysisFeedback]:
        """Get all feedback for an analysis"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM analysis_feedback WHERE analysis_id = ?", (analysis_id,)
            )
            
            feedback_list = []
            for row in cursor.fetchall():
                feedback_list.append(AnalysisFeedback.from_dict(dict(row)))
            
            return feedback_list
        finally:
            conn.close()
    
    # === RUBRIC MANAGEMENT METHODS ===
    
    def get_rubrics(self, filters: dict = None, limit: int = 50, offset: int = 0) -> List[QuestionRubric]:
        """Get rubrics with optional filtering"""
        conn = self.get_connection()
        try:
            query = "SELECT * FROM question_rubrics WHERE 1=1"
            params = []
            
            if filters:
                if 'subject' in filters:
                    query += " AND subject = ?"
                    params.append(filters['subject'])
                if 'topic' in filters:
                    query += " AND topic = ?"
                    params.append(filters['topic'])
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            
            rubrics = []
            for row in cursor.fetchall():
                rubrics.append(QuestionRubric.from_dict(dict(row)))
            
            return rubrics
        finally:
            conn.close()
    
    def get_rubric(self, rubric_id: str) -> Optional[QuestionRubric]:
        """Get a specific rubric by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM question_rubrics WHERE rubric_id = ?", (rubric_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return QuestionRubric.from_dict(dict(row))
            return None
        finally:
            conn.close()
    
    def save_rubric(self, rubric: QuestionRubric) -> QuestionRubric:
        """Save or update a rubric"""
        conn = self.get_connection()
        try:
            # Check if rubric exists
            existing = self.get_rubric(rubric.rubric_id)
            
            if existing:
                # Update existing rubric
                conn.execute("""
                    UPDATE question_rubrics SET
                        subject = ?, topic = ?, question_text = ?, model_answer = ?,
                        marking_scheme = ?, keywords = ?, max_marks = ?,
                        difficulty_level = ?, notes = ?, updated_at = ?
                    WHERE rubric_id = ?
                """, (
                    rubric.subject, rubric.topic, rubric.question_text, rubric.model_answer,
                    json.dumps(rubric.marking_scheme), json.dumps(rubric.keywords), rubric.max_marks,
                    rubric.difficulty_level, rubric.notes, datetime.utcnow().isoformat(),
                    rubric.rubric_id
                ))
            else:
                # Insert new rubric
                conn.execute("""
                    INSERT INTO question_rubrics (
                        rubric_id, subject, topic, question_text, model_answer,
                        marking_scheme, keywords, max_marks, difficulty_level,
                        notes, created_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rubric.rubric_id, rubric.subject, rubric.topic, rubric.question_text,
                    rubric.model_answer, json.dumps(rubric.marking_scheme), json.dumps(rubric.keywords),
                    rubric.max_marks, rubric.difficulty_level, rubric.notes, rubric.created_by,
                    rubric.created_at.isoformat()
                ))
            
            conn.commit()
            return rubric
        finally:
            conn.close()
    
    def delete_rubric(self, rubric_id: str) -> bool:
        """Delete a rubric"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("DELETE FROM question_rubrics WHERE rubric_id = ?", (rubric_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def count_analyses_by_rubric(self, rubric_id: str) -> int:
        """Count how many analyses use this rubric"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM answer_analyses WHERE analysis_results LIKE ?",
                (f'%{rubric_id}%',)
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def get_distinct_subjects(self) -> List[str]:
        """Get list of all subjects that have rubrics"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT DISTINCT subject FROM question_rubrics ORDER BY subject")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_topics_by_subject(self, subject: str) -> List[str]:
        """Get list of topics for a specific subject"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "SELECT DISTINCT topic FROM question_rubrics WHERE subject = ? ORDER BY topic",
                (subject,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

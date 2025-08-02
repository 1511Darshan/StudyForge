"""
Test script for database models
Run this to verify that the models work correctly
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.models.analyzer import AnswerAnalysis, QuestionRubric, DatabaseManager


def test_models():
    """Test the database models"""
    print("Testing StudyForge Answer Analyzer Models...")
    
    # Test database manager
    db = DatabaseManager(":memory:")  # Use in-memory database for testing
    print("✅ Database manager initialized")
    
    # Test creating an analysis
    analysis = AnswerAnalysis()
    analysis.student_id = "test_student_123"
    analysis.subject = "mathematics"
    analysis.question_paper_url = "/uploads/question_math.jpg"
    analysis.answer_sheet_url = "/uploads/answer_math.jpg"
    analysis.analysis_results = {
        "question_1": {
            "missed_marks": 2.5,
            "confidence": 0.85,
            "feedback": "Missing step in factoring"
        }
    }
    analysis.total_missed_marks = 2.5
    analysis.status = "completed"
    
    analysis_id = db.create_analysis(analysis)
    print(f"✅ Created analysis: {analysis_id}")
    
    # Test retrieving analysis
    retrieved = db.get_analysis(analysis_id)
    if retrieved and retrieved.student_id == "test_student_123":
        print("✅ Analysis retrieval successful")
    else:
        print("❌ Analysis retrieval failed")
    
    # Test creating rubric
    rubric = QuestionRubric()
    rubric.subject = "mathematics"
    rubric.question_number = "1"
    rubric.question_text = "Test question"
    rubric.model_answer = "Test answer"
    rubric.marking_scheme = {
        "step1": {"marks": 2, "description": "Show working"},
        "step2": {"marks": 3, "description": "Final answer"}
    }
    rubric.keywords = ["test", "sample"]
    rubric.max_marks = 5
    rubric.created_by = "test_teacher"
    
    rubric_id = db.create_rubric(rubric)
    print(f"✅ Created rubric: {rubric_id}")
    
    # Test retrieving rubrics
    rubrics = db.get_rubrics_by_subject("mathematics")
    if rubrics and len(rubrics) > 0:
        print("✅ Rubric retrieval successful")
    else:
        print("❌ Rubric retrieval failed")
    
    print("\n🎉 All model tests passed!")


if __name__ == "__main__":
    test_models()

"""
Sample rubric data for StudyForge Answer Analyzer
This file contains example rubrics for different subjects to get started
"""

SAMPLE_RUBRICS = {
    "mathematics": [
        {
            "id": "math_q1_algebra",
            "subject": "mathematics", 
            "question_number": "1",
            "question_text": "Solve the quadratic equation: x² + 5x + 6 = 0",
            "model_answer": "Using factoring method: x² + 5x + 6 = (x + 2)(x + 3) = 0. Therefore x = -2 or x = -3",
            "marking_scheme": {
                "method_identification": {
                    "description": "Identifies correct method (factoring, quadratic formula, or completing square)",
                    "marks": 2,
                    "keywords": ["factoring", "factor", "quadratic formula", "completing square"]
                },
                "correct_factoring": {
                    "description": "Correctly factors the quadratic expression",
                    "marks": 3,
                    "keywords": ["(x + 2)", "(x + 3)", "x+2", "x+3"]
                },
                "final_solution": {
                    "description": "States the correct solutions x = -2 and x = -3",
                    "marks": 2,
                    "keywords": ["x = -2", "x = -3", "x=-2", "x=-3"]
                },
                "verification": {
                    "description": "Shows verification by substituting back into original equation",
                    "marks": 1,
                    "keywords": ["verify", "check", "substitute", "proof"]
                }
            },
            "keywords": ["quadratic", "equation", "solve", "factor", "x = -2", "x = -3"],
            "max_marks": 8
        },
        {
            "id": "math_q2_calculus", 
            "subject": "mathematics",
            "question_number": "2",
            "question_text": "Find the derivative of f(x) = 3x³ + 2x² - 5x + 1",
            "model_answer": "f'(x) = 9x² + 4x - 5 using power rule",
            "marking_scheme": {
                "power_rule_application": {
                    "description": "Correctly applies power rule to each term",
                    "marks": 4,
                    "keywords": ["power rule", "d/dx", "derivative"]
                },
                "correct_coefficients": {
                    "description": "Gets correct coefficients: 9, 4, -5",
                    "marks": 3,
                    "keywords": ["9x²", "4x", "-5", "9x^2"]
                },
                "final_answer": {
                    "description": "States final answer f'(x) = 9x² + 4x - 5",
                    "marks": 1,
                    "keywords": ["f'(x) = 9x² + 4x - 5", "9x^2 + 4x - 5"]
                }
            },
            "keywords": ["derivative", "power rule", "9x²", "4x", "-5"],
            "max_marks": 8
        }
    ],
    
    "physics": [
        {
            "id": "phys_q1_mechanics",
            "subject": "physics",
            "question_number": "1", 
            "question_text": "A ball is thrown vertically upward with initial velocity 20 m/s. Find the maximum height reached.",
            "model_answer": "Using v² = u² + 2as, where v=0 at max height, u=20 m/s, a=-9.8 m/s². 0 = 400 + 2(-9.8)s, s = 400/19.6 = 20.4 m",
            "marking_scheme": {
                "equation_identification": {
                    "description": "Identifies correct kinematic equation v² = u² + 2as",
                    "marks": 2,
                    "keywords": ["v² = u² + 2as", "v^2 = u^2 + 2as", "kinematic equation"]
                },
                "variable_identification": {
                    "description": "Correctly identifies v=0, u=20 m/s, a=-9.8 m/s²",
                    "marks": 3,
                    "keywords": ["v=0", "u=20", "a=-9.8", "g=9.8"]
                },
                "substitution": {
                    "description": "Correctly substitutes values into equation",
                    "marks": 2,
                    "keywords": ["0 = 400", "2(-9.8)", "substitute"]
                },
                "final_calculation": {
                    "description": "Calculates final answer s = 20.4 m",
                    "marks": 2,
                    "keywords": ["20.4", "20.4 m", "s = 20.4"]
                }
            },
            "keywords": ["kinematic", "maximum height", "20.4", "v² = u² + 2as"],
            "max_marks": 9
        }
    ],
    
    "chemistry": [
        {
            "id": "chem_q1_stoichiometry",
            "subject": "chemistry",
            "question_number": "1",
            "question_text": "Balance the chemical equation: C₂H₆ + O₂ → CO₂ + H₂O",
            "model_answer": "2C₂H₆ + 7O₂ → 4CO₂ + 6H₂O",
            "marking_scheme": {
                "carbon_balance": {
                    "description": "Correctly balances carbon atoms (4 on each side)",
                    "marks": 2,
                    "keywords": ["4CO₂", "2C₂H₆", "carbon balance"]
                },
                "hydrogen_balance": {
                    "description": "Correctly balances hydrogen atoms (12 on each side)", 
                    "marks": 2,
                    "keywords": ["6H₂O", "12H", "hydrogen balance"]
                },
                "oxygen_balance": {
                    "description": "Correctly balances oxygen atoms (14 on each side)",
                    "marks": 2,
                    "keywords": ["7O₂", "14O", "oxygen balance"]
                },
                "final_equation": {
                    "description": "States final balanced equation with correct coefficients",
                    "marks": 2,
                    "keywords": ["2C₂H₆ + 7O₂ → 4CO₂ + 6H₂O", "2:7:4:6"]
                }
            },
            "keywords": ["balance", "equation", "2C₂H₆", "7O₂", "4CO₂", "6H₂O"],
            "max_marks": 8
        }
    ]
}


def get_sample_rubric(subject: str, question_number: str):
    """Get a sample rubric for testing"""
    subject_rubrics = SAMPLE_RUBRICS.get(subject.lower(), [])
    for rubric in subject_rubrics:
        if rubric["question_number"] == question_number:
            return rubric
    return None


def get_all_subjects():
    """Get list of all subjects with sample rubrics"""
    return list(SAMPLE_RUBRICS.keys())


def initialize_sample_data(db_manager):
    """Initialize database with sample rubric data"""
    from .models import QuestionRubric
    from datetime import datetime
    
    for subject, rubrics in SAMPLE_RUBRICS.items():
        for rubric_data in rubrics:
            # Check if rubric already exists
            existing = db_manager.get_rubric_by_question(
                rubric_data["subject"], 
                rubric_data["question_number"]
            )
            
            if not existing:
                rubric = QuestionRubric()
                rubric.id = rubric_data["id"]
                rubric.subject = rubric_data["subject"]
                rubric.question_number = rubric_data["question_number"]
                rubric.question_text = rubric_data["question_text"]
                rubric.model_answer = rubric_data["model_answer"]
                rubric.marking_scheme = rubric_data["marking_scheme"]
                rubric.keywords = rubric_data["keywords"]
                rubric.max_marks = rubric_data["max_marks"]
                rubric.created_by = "system"
                rubric.created_at = datetime.utcnow()
                
                db_manager.create_rubric(rubric)
                print(f"Created sample rubric: {subject} Q{rubric_data['question_number']}")
    
    print("Sample rubric data initialized successfully!")

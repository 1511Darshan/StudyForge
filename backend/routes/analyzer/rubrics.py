"""
Rubric management API endpoints for StudyForge Answer Analyzer
Handles CRUD operations for marking rubrics and scoring criteria
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, Any

# Import models and services
try:
    from backend.models.analyzer.models import QuestionRubric
    from backend.models.analyzer.database import DatabaseManager
    from backend.services.answer_analyzer.semantic_matcher import SemanticMatcher
    FULL_BACKEND_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Full backend not available: {e}")
    FULL_BACKEND_AVAILABLE = False

logger = logging.getLogger(__name__)

# Create blueprint
rubrics_bp = Blueprint('rubrics', __name__, url_prefix='/api/analyzer/rubrics')


def validate_rubric_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate rubric data structure
    
    Args:
        data: Rubric data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['subject', 'topic', 'question_text', 'max_marks']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
        
        if not data[field]:
            return False, f"Field '{field}' cannot be empty"
    
    # Validate max_marks is a positive number
    try:
        max_marks = float(data['max_marks'])
        if max_marks <= 0:
            return False, "max_marks must be a positive number"
    except (TypeError, ValueError):
        return False, "max_marks must be a valid number"
    
    # Validate marking_scheme structure
    marking_scheme = data.get('marking_scheme', {})
    if not isinstance(marking_scheme, dict):
        return False, "marking_scheme must be a dictionary"
    
    # Validate each marking scheme point
    total_scheme_marks = 0
    for point_id, point_data in marking_scheme.items():
        if not isinstance(point_data, dict):
            return False, f"Marking scheme point '{point_id}' must be a dictionary"
        
        required_point_fields = ['description', 'marks']
        for field in required_point_fields:
            if field not in point_data:
                return False, f"Missing field '{field}' in marking scheme point '{point_id}'"
        
        try:
            point_marks = float(point_data['marks'])
            if point_marks < 0:
                return False, f"Marks for point '{point_id}' cannot be negative"
            total_scheme_marks += point_marks
        except (TypeError, ValueError):
            return False, f"Invalid marks value for point '{point_id}'"
    
    # Check if total scheme marks match max_marks (with small tolerance)
    if abs(total_scheme_marks - max_marks) > 0.01:
        return False, f"Total marking scheme marks ({total_scheme_marks}) don't match max_marks ({max_marks})"
    
    return True, ""


@rubrics_bp.route('/', methods=['GET'])
def list_rubrics():
    """
    Get list of all rubrics with optional filtering
    
    Query parameters:
    - subject: Filter by subject
    - topic: Filter by topic
    - limit: Maximum number of results (default: 50)
    - offset: Number of results to skip (default: 0)
    """
    if not FULL_BACKEND_AVAILABLE:
        return get_mock_rubrics_list()
    
    try:
        # Get query parameters
        subject = request.args.get('subject')
        topic = request.args.get('topic')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Validate parameters
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0
        
        # Get database manager
        db_manager = DatabaseManager()
        
        # Build filter conditions
        filters = {}
        if subject:
            filters['subject'] = subject
        if topic:
            filters['topic'] = topic
        
        # Get rubrics from database
        rubrics = db_manager.get_rubrics(filters=filters, limit=limit, offset=offset)
        
        # Format response
        rubrics_data = []
        for rubric in rubrics:
            rubrics_data.append({
                'rubric_id': rubric.rubric_id,
                'subject': rubric.subject,
                'topic': rubric.topic,
                'question_text': rubric.question_text[:200] + '...' if len(rubric.question_text) > 200 else rubric.question_text,
                'max_marks': rubric.max_marks,
                'difficulty_level': rubric.difficulty_level,
                'created_at': rubric.created_at.isoformat(),
                'updated_at': rubric.updated_at.isoformat() if rubric.updated_at else None
            })
        
        return jsonify({
            'rubrics': rubrics_data,
            'count': len(rubrics_data),
            'offset': offset,
            'limit': limit
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {e}'}), 400
    except Exception as e:
        logger.error(f"Error listing rubrics: {e}")
        return jsonify({'error': 'Failed to retrieve rubrics'}), 500


@rubrics_bp.route('/<string:rubric_id>', methods=['GET'])
def get_rubric(rubric_id: str):
    """
    Get detailed rubric information
    
    Args:
        rubric_id: Unique rubric identifier
    """
    if not FULL_BACKEND_AVAILABLE:
        return get_mock_rubric_detail(rubric_id)
    
    try:
        db_manager = DatabaseManager()
        rubric = db_manager.get_rubric(rubric_id)
        
        if not rubric:
            return jsonify({'error': 'Rubric not found'}), 404
        
        # Return complete rubric data
        return jsonify({
            'rubric_id': rubric.rubric_id,
            'subject': rubric.subject,
            'topic': rubric.topic,
            'question_text': rubric.question_text,
            'model_answer': rubric.model_answer,
            'marking_scheme': rubric.marking_scheme,
            'keywords': rubric.keywords,
            'max_marks': rubric.max_marks,
            'difficulty_level': rubric.difficulty_level,
            'notes': rubric.notes,
            'created_at': rubric.created_at.isoformat(),
            'updated_at': rubric.updated_at.isoformat() if rubric.updated_at else None,
            'created_by': rubric.created_by
        })
        
    except Exception as e:
        logger.error(f"Error getting rubric {rubric_id}: {e}")
        return jsonify({'error': 'Failed to retrieve rubric'}), 500


@rubrics_bp.route('/', methods=['POST'])
def create_rubric():
    """
    Create a new marking rubric
    
    Required JSON fields:
    - subject: Subject name
    - topic: Topic/chapter name
    - question_text: The question text
    - max_marks: Maximum marks for the question
    - marking_scheme: Dictionary with marking criteria
    
    Optional fields:
    - model_answer: Ideal answer text
    - keywords: List of important keywords
    - difficulty_level: Easy/Medium/Hard
    - notes: Additional notes
    """
    if not FULL_BACKEND_AVAILABLE:
        return create_mock_rubric()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Validate rubric data
        is_valid, error_msg = validate_rubric_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Create rubric object
        rubric = QuestionRubric(
            subject=data['subject'].strip(),
            topic=data['topic'].strip(),
            question_text=data['question_text'].strip(),
            model_answer=data.get('model_answer', '').strip(),
            marking_scheme=data['marking_scheme'],
            keywords=data.get('keywords', []),
            max_marks=float(data['max_marks']),
            difficulty_level=data.get('difficulty_level', 'Medium'),
            notes=data.get('notes', '').strip(),
            created_by=data.get('created_by', 'system')
        )
        
        # Save to database
        db_manager = DatabaseManager()
        saved_rubric = db_manager.save_rubric(rubric)
        
        logger.info(f"Created new rubric: {saved_rubric.rubric_id}")
        
        return jsonify({
            'message': 'Rubric created successfully',
            'rubric_id': saved_rubric.rubric_id,
            'subject': saved_rubric.subject,
            'topic': saved_rubric.topic,
            'max_marks': saved_rubric.max_marks,
            'created_at': saved_rubric.created_at.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating rubric: {e}")
        return jsonify({'error': 'Failed to create rubric'}), 500


@rubrics_bp.route('/<string:rubric_id>', methods=['PUT'])
def update_rubric(rubric_id: str):
    """
    Update an existing rubric
    
    Args:
        rubric_id: Unique rubric identifier
    """
    if not FULL_BACKEND_AVAILABLE:
        return update_mock_rubric(rubric_id)
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Get existing rubric
        db_manager = DatabaseManager()
        rubric = db_manager.get_rubric(rubric_id)
        
        if not rubric:
            return jsonify({'error': 'Rubric not found'}), 404
        
        # Update fields if provided
        if 'subject' in data:
            rubric.subject = data['subject'].strip()
        if 'topic' in data:
            rubric.topic = data['topic'].strip()
        if 'question_text' in data:
            rubric.question_text = data['question_text'].strip()
        if 'model_answer' in data:
            rubric.model_answer = data['model_answer'].strip()
        if 'marking_scheme' in data:
            rubric.marking_scheme = data['marking_scheme']
        if 'keywords' in data:
            rubric.keywords = data['keywords']
        if 'max_marks' in data:
            rubric.max_marks = float(data['max_marks'])
        if 'difficulty_level' in data:
            rubric.difficulty_level = data['difficulty_level']
        if 'notes' in data:
            rubric.notes = data['notes'].strip()
        
        # Validate updated data
        rubric_dict = {
            'subject': rubric.subject,
            'topic': rubric.topic,
            'question_text': rubric.question_text,
            'max_marks': rubric.max_marks,
            'marking_scheme': rubric.marking_scheme
        }
        
        is_valid, error_msg = validate_rubric_data(rubric_dict)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Update timestamp
        rubric.updated_at = datetime.utcnow()
        
        # Save changes
        updated_rubric = db_manager.save_rubric(rubric)
        
        logger.info(f"Updated rubric: {rubric_id}")
        
        return jsonify({
            'message': 'Rubric updated successfully',
            'rubric_id': updated_rubric.rubric_id,
            'updated_at': updated_rubric.updated_at.isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {e}'}), 400
    except Exception as e:
        logger.error(f"Error updating rubric {rubric_id}: {e}")
        return jsonify({'error': 'Failed to update rubric'}), 500


@rubrics_bp.route('/<string:rubric_id>', methods=['DELETE'])
def delete_rubric(rubric_id: str):
    """
    Delete a rubric
    
    Args:
        rubric_id: Unique rubric identifier
    """
    if not FULL_BACKEND_AVAILABLE:
        return delete_mock_rubric(rubric_id)
    
    try:
        db_manager = DatabaseManager()
        
        # Check if rubric exists
        rubric = db_manager.get_rubric(rubric_id)
        if not rubric:
            return jsonify({'error': 'Rubric not found'}), 404
        
        # Check if rubric is being used in any analyses
        analyses_count = db_manager.count_analyses_by_rubric(rubric_id)
        if analyses_count > 0:
            return jsonify({
                'error': f'Cannot delete rubric. It is used in {analyses_count} analyses.'
            }), 400
        
        # Delete rubric
        success = db_manager.delete_rubric(rubric_id)
        
        if success:
            logger.info(f"Deleted rubric: {rubric_id}")
            return jsonify({'message': 'Rubric deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete rubric'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting rubric {rubric_id}: {e}")
        return jsonify({'error': 'Failed to delete rubric'}), 500


@rubrics_bp.route('/validate', methods=['POST'])
def validate_rubric():
    """
    Validate rubric structure without saving
    
    Returns validation result and any errors found
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Validate rubric data
        is_valid, error_msg = validate_rubric_data(data)
        
        if is_valid:
            # Additional validation using semantic matcher
            if FULL_BACKEND_AVAILABLE:
                try:
                    semantic_matcher = SemanticMatcher()
                    # Test the rubric structure with sample data
                    test_result = semantic_matcher.analyze_answer_against_rubric(
                        "Sample answer for validation",
                        data
                    )
                    
                    validation_notes = []
                    if 'error' in test_result:
                        validation_notes.append(f"Semantic validation warning: {test_result['error']}")
                    
                    return jsonify({
                        'valid': True,
                        'message': 'Rubric structure is valid',
                        'validation_notes': validation_notes
                    })
                except Exception as e:
                    return jsonify({
                        'valid': True,
                        'message': 'Rubric structure is valid (basic validation only)',
                        'warning': f'Advanced validation failed: {str(e)}'
                    })
            else:
                return jsonify({
                    'valid': True,
                    'message': 'Rubric structure is valid (basic validation only)'
                })
        else:
            return jsonify({
                'valid': False,
                'error': error_msg
            }), 400
        
    except Exception as e:
        logger.error(f"Error validating rubric: {e}")
        return jsonify({'error': 'Validation failed'}), 500


@rubrics_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """Get list of all subjects that have rubrics"""
    if not FULL_BACKEND_AVAILABLE:
        return jsonify({
            'subjects': ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science']
        })
    
    try:
        db_manager = DatabaseManager()
        subjects = db_manager.get_distinct_subjects()
        
        return jsonify({'subjects': subjects})
        
    except Exception as e:
        logger.error(f"Error getting subjects: {e}")
        return jsonify({'error': 'Failed to retrieve subjects'}), 500


@rubrics_bp.route('/topics', methods=['GET'])
def get_topics():
    """
    Get list of topics for a subject
    
    Query parameter:
    - subject: Subject name (required)
    """
    subject = request.args.get('subject')
    
    if not subject:
        return jsonify({'error': 'Subject parameter required'}), 400
    
    if not FULL_BACKEND_AVAILABLE:
        mock_topics = {
            'Mathematics': ['Algebra', 'Calculus', 'Geometry', 'Statistics'],
            'Physics': ['Mechanics', 'Thermodynamics', 'Electromagnetism', 'Optics'],
            'Chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry'],
            'Biology': ['Cell Biology', 'Genetics', 'Ecology', 'Evolution'],
            'Computer Science': ['Data Structures', 'Algorithms', 'Database Systems', 'Networks']
        }
        
        return jsonify({
            'subject': subject,
            'topics': mock_topics.get(subject, [])
        })
    
    try:
        db_manager = DatabaseManager()
        topics = db_manager.get_topics_by_subject(subject)
        
        return jsonify({
            'subject': subject,
            'topics': topics
        })
        
    except Exception as e:
        logger.error(f"Error getting topics for subject {subject}: {e}")
        return jsonify({'error': 'Failed to retrieve topics'}), 500


# Mock functions for demonstration
def get_mock_rubrics_list():
    """Return mock rubrics list for demonstration"""
    return jsonify({
        'rubrics': [
            {
                'rubric_id': 'rubric_math_001',
                'subject': 'Mathematics',
                'topic': 'Calculus',
                'question_text': 'Find the derivative of f(x) = x^3 + 2x^2 - 5x + 1',
                'max_marks': 10.0,
                'difficulty_level': 'Medium',
                'created_at': '2025-08-02T16:00:00',
                'updated_at': None
            },
            {
                'rubric_id': 'rubric_phys_001',
                'subject': 'Physics',
                'topic': 'Mechanics',
                'question_text': 'A ball is thrown vertically upward with initial velocity 20 m/s...',
                'max_marks': 15.0,
                'difficulty_level': 'Hard',
                'created_at': '2025-08-02T15:30:00',
                'updated_at': '2025-08-02T16:15:00'
            }
        ],
        'count': 2,
        'offset': 0,
        'limit': 50,
        'note': 'Mock data for demonstration'
    })


def get_mock_rubric_detail(rubric_id: str):
    """Return mock rubric detail for demonstration"""
    if rubric_id == 'rubric_math_001':
        return jsonify({
            'rubric_id': 'rubric_math_001',
            'subject': 'Mathematics',
            'topic': 'Calculus',
            'question_text': 'Find the derivative of f(x) = x^3 + 2x^2 - 5x + 1',
            'model_answer': 'f\'(x) = 3x^2 + 4x - 5',
            'marking_scheme': {
                'derivative_rules': {
                    'description': 'Correctly applies derivative rules',
                    'marks': 4.0
                },
                'calculation': {
                    'description': 'Accurate calculation of each term',
                    'marks': 4.0
                },
                'final_answer': {
                    'description': 'Correct final simplified form',
                    'marks': 2.0
                }
            },
            'keywords': ['derivative', 'power rule', 'polynomial'],
            'max_marks': 10.0,
            'difficulty_level': 'Medium',
            'notes': 'Standard calculus differentiation problem',
            'created_at': '2025-08-02T16:00:00',
            'updated_at': None,
            'created_by': 'system'
        })
    else:
        return jsonify({'error': 'Rubric not found'}), 404


def create_mock_rubric():
    """Mock rubric creation"""
    return jsonify({
        'message': 'Rubric created successfully (mock)',
        'rubric_id': f'mock_rubric_{int(datetime.now().timestamp())}',
        'subject': 'Mock Subject',
        'topic': 'Mock Topic',
        'max_marks': 10.0,
        'created_at': datetime.now().isoformat()
    }), 201


def update_mock_rubric(rubric_id: str):
    """Mock rubric update"""
    return jsonify({
        'message': 'Rubric updated successfully (mock)',
        'rubric_id': rubric_id,
        'updated_at': datetime.now().isoformat()
    })


def delete_mock_rubric(rubric_id: str):
    """Mock rubric deletion"""
    return jsonify({'message': 'Rubric deleted successfully (mock)'})

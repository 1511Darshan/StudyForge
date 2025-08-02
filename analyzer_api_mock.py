"""
Mock Answer Analyzer API routes for demonstration
Shows the API structure and endpoints without requiring full backend dependencies
"""
import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

# Create blueprint for analyzer routes
analyzer_bp = Blueprint('analyzer', __name__, url_prefix='/api/analyzer')

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_folder() -> str:
    """Get the upload folder path, create if it doesn't exist"""
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads', 'answer-sheets')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


@analyzer_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the analyzer service"""
    return jsonify({
        'status': 'healthy',
        'service': 'answer_analyzer_mock',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'analyzer_service': True,
            'database': True,
            'ai_analysis': False  # Mock version
        },
        'note': 'This is a mock API for demonstration'
    }), 200


@analyzer_bp.route('/upload', methods=['POST'])
def upload_answer_sheet():
    """
    Upload an answer sheet image for analysis (Mock implementation)
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload an answer sheet image'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Allowed file types: {", ".join(ALLOWED_EXTENSIONS)}',
                'uploaded_type': file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown'
            }), 400
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Extract metadata from form
        student_id = request.form.get('student_id')
        subject = request.form.get('subject')
        exam_id = request.form.get('exam_id')
        
        # Generate file ID for tracking
        file_id = f"upload_{timestamp}_{student_id or 'anonymous'}"
        
        logger.info(f"File uploaded successfully: {unique_filename} (ID: {file_id})")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file_id': file_id,
            'filename': unique_filename,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'metadata': {
                'student_id': student_id,
                'subject': subject,
                'exam_id': exam_id,
                'upload_timestamp': datetime.now().isoformat()
            },
            'note': 'Mock upload - file saved but not processed'
        }), 200
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return jsonify({
            'error': 'Upload failed',
            'message': 'An error occurred while uploading the file',
            'details': str(e)
        }), 500


@analyzer_bp.route('/analyze', methods=['POST'])
def analyze_answer_sheet():
    """
    Mock analysis endpoint that returns simulated results
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must contain JSON data'
            }), 400
        
        file_path = data.get('file_path')
        rubrics = data.get('rubrics', [])
        student_id = data.get('student_id')
        
        if not file_path:
            return jsonify({
                'error': 'Missing file_path',
                'message': 'file_path is required for analysis'
            }), 400
        
        if not rubrics:
            return jsonify({
                'error': 'Missing rubrics',
                'message': 'At least one rubric is required for analysis'
            }), 400
        
        # Mock analysis results
        analysis_id = f"analysis_{int(datetime.now().timestamp())}"
        
        # Simulate question results
        question_results = []
        total_score = 0
        total_marks = 0
        
        for i, rubric in enumerate(rubrics, 1):
            max_marks = rubric.get('max_marks', 10)
            # Simulate scoring (random-ish but deterministic)
            score = 0.8 + (i * 0.1) % 0.3  # Between 0.8 and 1.0
            marks_awarded = score * max_marks
            
            question_results.append({
                'question_number': str(i),
                'detected_text': f"Mock detected text for question {i}...",
                'score': score,
                'marks_awarded': marks_awarded,
                'total_marks': max_marks,
                'confidence': 0.85,
                'rubric_analysis': [
                    {
                        'rubric_point': f"Mock rubric point {j+1}",
                        'status': 'YES' if j < 2 else 'PARTIAL',
                        'confidence': 0.9,
                        'evidence': f"Mock evidence {j+1}",
                        'marks_awarded': 2,
                        'total_marks': 2
                    }
                    for j in range(3)
                ],
                'processing_time': 0.5
            })
            
            total_score += marks_awarded
            total_marks += max_marks
        
        overall_score = total_score / total_marks if total_marks > 0 else 0
        
        response_data = {
            'success': True,
            'analysis_id': analysis_id,
            'student_id': student_id,
            'analysis_results': {
                'overall_score': overall_score,
                'percentage_score': overall_score * 100,
                'total_possible_marks': total_marks,
                'total_questions': len(rubrics),
                'analyzed_questions': len(rubrics),
                'confidence_score': 0.85,
                'analysis_time': 2.5
            },
            'question_results': question_results,
            'feedback': {
                'overall_performance': f"Mock analysis completed with {overall_score * 100:.1f}% score",
                'improvement_suggestions': [
                    'Mock suggestion 1: Focus on showing methodology',
                    'Mock suggestion 2: Include more detailed explanations'
                ],
                'strengths': ['Good problem-solving approach'],
                'areas_for_improvement': ['Mathematical notation'],
                'confidence_assessment': {
                    'overall_confidence': 0.85,
                    'reliability': 'High',
                    'note': 'Mock analysis - confidence simulated'
                }
            },
            'metadata': {
                'processing_errors': [],
                'analysis_timestamp': datetime.now().isoformat(),
                'config_used': {
                    'ai_analysis_enabled': False,
                    'confidence_threshold': 0.7
                },
                'note': 'This is a mock analysis for demonstration'
            }
        }
        
        logger.info(f"Mock analysis completed: {overall_score * 100:.1f}% score for {len(rubrics)} questions")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Mock analysis failed: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'message': 'An error occurred during mock analysis',
            'details': str(e)
        }), 500


@analyzer_bp.route('/results/<analysis_id>', methods=['GET'])
def get_analysis_result(analysis_id: str):
    """
    Mock results retrieval endpoint
    """
    try:
        # Mock response
        response_data = {
            'analysis_id': analysis_id,
            'student_id': 'mock_student',
            'overall_score': 8.5,
            'max_possible_score': 10.0,
            'percentage_score': 85.0,
            'confidence_score': 0.85,
            'processing_time': 2.5,
            'created_at': datetime.now().isoformat(),
            'note': 'Mock result - not from actual analysis'
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve mock analysis {analysis_id}: {e}")
        return jsonify({
            'error': 'Retrieval failed',
            'message': 'An error occurred while retrieving the mock analysis',
            'details': str(e)
        }), 500


@analyzer_bp.route('/history', methods=['GET'])
def get_analysis_history():
    """
    Mock analysis history endpoint
    """
    try:
        # Mock history data
        response_data = {
            'total_count': 3,
            'returned_count': 3,
            'offset': 0,
            'limit': 50,
            'analyses': [
                {
                    'analysis_id': 'mock_analysis_1',
                    'student_id': 'student_001',
                    'overall_score': 8.5,
                    'max_possible_score': 10.0,
                    'percentage_score': 85.0,
                    'confidence_score': 0.85,
                    'created_at': datetime.now().isoformat(),
                    'processing_time': 2.5
                },
                {
                    'analysis_id': 'mock_analysis_2',
                    'student_id': 'student_002',
                    'overall_score': 7.2,
                    'max_possible_score': 10.0,
                    'percentage_score': 72.0,
                    'confidence_score': 0.78,
                    'created_at': datetime.now().isoformat(),
                    'processing_time': 3.1
                },
                {
                    'analysis_id': 'mock_analysis_3',
                    'student_id': 'student_003',
                    'overall_score': 9.1,
                    'max_possible_score': 10.0,
                    'percentage_score': 91.0,
                    'confidence_score': 0.92,
                    'created_at': datetime.now().isoformat(),
                    'processing_time': 1.8
                }
            ],
            'note': 'Mock history data for demonstration'
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve mock analysis history: {e}")
        return jsonify({
            'error': 'Retrieval failed',
            'message': 'An error occurred while retrieving mock analysis history',
            'details': str(e)
        }), 500


# Error handlers for the blueprint
@analyzer_bp.errorhandler(413)
def file_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'message': f'Maximum file size is {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413


@analyzer_bp.errorhandler(404)
def not_found(error):
    """Handle not found error"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested analyzer endpoint does not exist'
    }), 404


@analyzer_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal server error in analyzer: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred in the analyzer service'
    }), 500

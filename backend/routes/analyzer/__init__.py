"""
API routes for StudyForge Answer Analyzer
Handles file uploads, analysis requests, and result retrieval
"""
import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, List, Any, Optional

from ...services.answer_analyzer.analyzer_service import AnalyzerService, AnalysisConfig
from ...models.analyzer.database import DatabaseManager

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
    try:
        # Test analyzer service initialization
        analyzer = AnalyzerService()
        db_manager = DatabaseManager()
        
        return jsonify({
            'status': 'healthy',
            'service': 'answer_analyzer',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'analyzer_service': True,
                'database': True,
                'ai_analysis': analyzer.config.enable_ai_analysis
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'answer_analyzer',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@analyzer_bp.route('/upload', methods=['POST'])
def upload_answer_sheet():
    """
    Upload an answer sheet image for analysis
    
    Expected form data:
    - file: Image file (required)
    - student_id: Student identifier (optional)
    - subject: Subject name (optional)
    - exam_id: Exam identifier (optional)
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
        
        # Check file size (Flask's MAX_CONTENT_LENGTH should handle this, but double-check)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'error': 'File too large',
                'message': f'Maximum file size is {MAX_FILE_SIZE // (1024*1024)}MB',
                'uploaded_size': f'{file_size // (1024*1024)}MB'
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
            'file_size': file_size,
            'metadata': {
                'student_id': student_id,
                'subject': subject,
                'exam_id': exam_id,
                'upload_timestamp': datetime.now().isoformat()
            }
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
    Analyze an uploaded answer sheet against rubrics
    
    Expected JSON payload:
    {
        "file_path": "path/to/uploaded/image.jpg",
        "rubrics": [
            {
                "question_number": "1",
                "subject": "mathematics",
                "question_text": "Solve x² + 5x + 6 = 0",
                "model_answer": "x = -2 or x = -3",
                "marking_scheme": {
                    "method": {"description": "Shows factoring method", "marks": 2},
                    "solution": {"description": "Correct final answer", "marks": 3}
                },
                "keywords": ["factor", "x = -2", "x = -3"],
                "max_marks": 5
            }
        ],
        "student_id": "student123",
        "analysis_config": {
            "enable_ai_analysis": true,
            "confidence_threshold": 0.7
        }
    }
    """
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must contain JSON data'
            }), 400
        
        # Validate required fields
        file_path = data.get('file_path')
        rubrics = data.get('rubrics', [])
        
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
        
        # Validate file exists
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'File not found',
                'message': f'The specified file does not exist: {file_path}'
            }), 404
        
        # Extract optional parameters
        student_id = data.get('student_id')
        analysis_config_data = data.get('analysis_config', {})
        
        # Create analysis configuration
        config = AnalysisConfig(
            enable_ai_analysis=analysis_config_data.get('enable_ai_analysis', True),
            confidence_threshold=analysis_config_data.get('confidence_threshold', 0.7),
            min_text_length=analysis_config_data.get('min_text_length', 10),
            max_questions_per_sheet=analysis_config_data.get('max_questions_per_sheet', 20),
            save_intermediate_results=analysis_config_data.get('save_intermediate_results', True)
        )
        
        # Initialize analyzer service
        analyzer = AnalyzerService(config)
        
        # Validate rubrics format
        validation_result = analyzer.validate_rubrics(rubrics)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Invalid rubrics',
                'message': 'One or more rubrics have invalid format',
                'validation_errors': validation_result['errors']
            }), 400
        
        logger.info(f"Starting analysis: {file_path} with {len(rubrics)} rubrics")
        
        # Perform analysis
        result = analyzer.analyze_answer_sheet(
            image_path=file_path,
            rubrics=rubrics,
            student_id=student_id
        )
        
        # Check for processing errors
        if result.processing_errors:
            logger.warning(f"Analysis completed with errors: {result.processing_errors}")
        
        # Generate detailed feedback
        feedback = analyzer.generate_detailed_feedback(result)
        
        logger.info(f"Analysis completed: {result.percentage_score:.1f}% score for {result.analyzed_questions} questions")
        
        # Prepare response
        response_data = {
            'success': True,
            'analysis_id': result.sheet_id,
            'student_id': result.student_id,
            'analysis_results': {
                'overall_score': result.overall_score,
                'percentage_score': result.percentage_score,
                'total_possible_marks': result.total_possible_marks,
                'total_questions': result.total_questions,
                'analyzed_questions': result.analyzed_questions,
                'confidence_score': result.confidence_score,
                'analysis_time': result.analysis_time
            },
            'question_results': [
                {
                    'question_number': qr.question_number,
                    'detected_text': qr.detected_text[:200] + '...' if len(qr.detected_text) > 200 else qr.detected_text,
                    'score': qr.overall_score,
                    'marks_awarded': qr.overall_score * qr.total_marks,
                    'total_marks': qr.total_marks,
                    'confidence': qr.confidence_score,
                    'rubric_analysis': qr.rubric_analysis,
                    'processing_time': qr.processing_time
                }
                for qr in result.question_results
            ],
            'feedback': feedback,
            'metadata': {
                'processing_errors': result.processing_errors,
                'analysis_timestamp': datetime.now().isoformat(),
                'config_used': {
                    'ai_analysis_enabled': config.enable_ai_analysis,
                    'confidence_threshold': config.confidence_threshold
                }
            }
        }
        
        return jsonify(response_data), 200
        
    except json.JSONDecodeError:
        return jsonify({
            'error': 'Invalid JSON',
            'message': 'Request body contains invalid JSON'
        }), 400
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'message': 'An error occurred during analysis',
            'details': str(e)
        }), 500


@analyzer_bp.route('/results/<analysis_id>', methods=['GET'])
def get_analysis_result(analysis_id: str):
    """
    Retrieve analysis results by ID
    
    Args:
        analysis_id: The analysis ID to retrieve
        
    Query parameters:
        include_details: Include detailed question analysis (default: true)
        include_feedback: Include feedback and suggestions (default: true)
    """
    try:
        # Get query parameters
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        include_feedback = request.args.get('include_feedback', 'true').lower() == 'true'
        
        # Retrieve from database
        db_manager = DatabaseManager()
        analysis_data = db_manager.get_analysis(analysis_id)
        
        if not analysis_data:
            return jsonify({
                'error': 'Analysis not found',
                'message': f'No analysis found with ID: {analysis_id}'
            }), 404
        
        # Prepare response
        response_data = {
            'analysis_id': analysis_data.get('id', analysis_id),
            'student_id': analysis_data.get('student_id'),
            'overall_score': analysis_data.get('total_score', 0),
            'max_possible_score': analysis_data.get('max_possible_score', 0),
            'percentage_score': (analysis_data.get('total_score', 0) / analysis_data.get('max_possible_score', 1)) * 100,
            'confidence_score': analysis_data.get('confidence_score', 0),
            'processing_time': analysis_data.get('processing_time', 0),
            'created_at': analysis_data.get('created_at')
        }
        
        # Add detailed analysis if requested
        if include_details:
            analysis_details = analysis_data.get('analysis_details', {})
            response_data['question_results'] = analysis_details.get('question_results', [])
            response_data['metadata'] = analysis_details.get('metadata', {})
            response_data['processing_errors'] = analysis_details.get('processing_errors', [])
        
        # Add feedback if requested
        if include_feedback:
            # Generate feedback from stored data if not cached
            # This would require reconstructing the result object and calling generate_detailed_feedback
            # For now, we'll include basic feedback
            response_data['feedback'] = {
                'overall_performance': f"Analysis completed with {response_data['percentage_score']:.1f}% score",
                'note': 'Detailed feedback generation requires re-analysis'
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {e}")
        return jsonify({
            'error': 'Retrieval failed',
            'message': 'An error occurred while retrieving the analysis',
            'details': str(e)
        }), 500


@analyzer_bp.route('/history', methods=['GET'])
def get_analysis_history():
    """
    Get analysis history with optional filtering
    
    Query parameters:
        student_id: Filter by student ID
        limit: Maximum number of results (default: 50, max: 200)
        offset: Number of results to skip (default: 0)
        order_by: Sort order - 'created_at' or 'score' (default: 'created_at')
        order_dir: Sort direction - 'asc' or 'desc' (default: 'desc')
    """
    try:
        # Parse query parameters
        student_id = request.args.get('student_id')
        limit = min(int(request.args.get('limit', 50)), 200)  # Cap at 200
        offset = int(request.args.get('offset', 0))
        order_by = request.args.get('order_by', 'created_at')
        order_dir = request.args.get('order_dir', 'desc')
        
        # Validate parameters
        if order_by not in ['created_at', 'score']:
            order_by = 'created_at'
        if order_dir not in ['asc', 'desc']:
            order_dir = 'desc'
        
        # Retrieve from database
        db_manager = DatabaseManager()
        analyses = db_manager.get_analyses(limit=limit + offset)  # Get more than needed for offset
        
        # Apply filtering
        if student_id:
            analyses = [a for a in analyses if a.get('student_id') == student_id]
        
        # Apply sorting
        if order_by == 'score':
            analyses.sort(key=lambda x: x.get('total_score', 0), reverse=(order_dir == 'desc'))
        else:  # created_at
            analyses.sort(key=lambda x: x.get('created_at', ''), reverse=(order_dir == 'desc'))
        
        # Apply pagination
        paginated_analyses = analyses[offset:offset + limit]
        
        # Prepare response
        response_data = {
            'total_count': len(analyses),
            'returned_count': len(paginated_analyses),
            'offset': offset,
            'limit': limit,
            'analyses': [
                {
                    'analysis_id': analysis.get('id'),
                    'student_id': analysis.get('student_id'),
                    'overall_score': analysis.get('total_score', 0),
                    'max_possible_score': analysis.get('max_possible_score', 0),
                    'percentage_score': (analysis.get('total_score', 0) / analysis.get('max_possible_score', 1)) * 100,
                    'confidence_score': analysis.get('confidence_score', 0),
                    'created_at': analysis.get('created_at'),
                    'processing_time': analysis.get('processing_time', 0)
                }
                for analysis in paginated_analyses
            ]
        }
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid parameters',
            'message': 'One or more query parameters have invalid values',
            'details': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Failed to retrieve analysis history: {e}")
        return jsonify({
            'error': 'Retrieval failed',
            'message': 'An error occurred while retrieving analysis history',
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

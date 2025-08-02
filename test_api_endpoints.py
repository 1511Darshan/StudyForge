"""
Test script for the Answer Analyzer API endpoints
Tests file upload, analysis, and result retrieval functionality
"""
import requests
import json
import time
import os
from PIL import Image, ImageDraw, ImageFont
import tempfile


class AnalyzerAPITester:
    """Test client for the Answer Analyzer API"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/analyzer"
        
    def create_test_image(self):
        """Create a test answer sheet image"""
        # Create a simple answer sheet for testing
        img = Image.new('RGB', (800, 1000), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw header
        draw.text((50, 30), "Mathematics Test - Answer Sheet", fill='black', font=font)
        draw.text((50, 60), "Student: John Doe", fill='black', font=small_font)
        
        # Question 1
        y_pos = 120
        draw.text((50, y_pos), "1. Solve x² + 5x + 6 = 0", fill='black', font=font)
        y_pos += 40
        draw.text((70, y_pos), "Using factoring method:", fill='black', font=small_font)
        y_pos += 25
        draw.text((70, y_pos), "x² + 5x + 6 = (x + 2)(x + 3) = 0", fill='black', font=small_font)
        y_pos += 25
        draw.text((70, y_pos), "Therefore: x = -2 or x = -3", fill='black', font=small_font)
        
        # Question 2
        y_pos += 60
        draw.text((50, y_pos), "2. Find the area of a circle with radius 3cm", fill='black', font=font)
        y_pos += 40
        draw.text((70, y_pos), "Area = πr² = π × 3² = 9π cm²", fill='black', font=small_font)
        
        return img
    
    def create_test_rubrics(self):
        """Create test rubrics for the sample questions"""
        return [
            {
                "question_number": "1",
                "subject": "mathematics",
                "question_text": "Solve the quadratic equation: x² + 5x + 6 = 0",
                "model_answer": "Using factoring method: x² + 5x + 6 = (x + 2)(x + 3) = 0. Therefore x = -2 or x = -3",
                "marking_scheme": {
                    "method_identification": {
                        "description": "Identifies correct method (factoring)",
                        "marks": 2,
                        "keywords": ["factoring", "factor"]
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
                    }
                },
                "keywords": ["quadratic", "equation", "solve", "factor", "x = -2", "x = -3"],
                "max_marks": 7
            },
            {
                "question_number": "2",
                "subject": "mathematics",
                "question_text": "Find the area of a circle with radius 3cm",
                "model_answer": "Area = πr² = π × 3² = 9π cm²",
                "marking_scheme": {
                    "formula": {
                        "description": "States correct formula for area of circle",
                        "marks": 1,
                        "keywords": ["πr²", "π × r²", "pi r squared"]
                    },
                    "substitution": {
                        "description": "Correctly substitutes radius value",
                        "marks": 1,
                        "keywords": ["3²", "9"]
                    },
                    "calculation": {
                        "description": "Performs correct calculation",
                        "marks": 1,
                        "keywords": ["9π", "9pi"]
                    },
                    "units": {
                        "description": "Includes correct units",
                        "marks": 1,
                        "keywords": ["cm²", "cm2", "square cm"]
                    }
                },
                "keywords": ["area", "circle", "π", "radius", "9π", "cm²"],
                "max_marks": 4
            }
        ]
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print("=== Testing Health Check ===")
        
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service Status: {data.get('status')}")
                print(f"   Service: {data.get('service')}")
                print(f"   Components: {data.get('components', {})}")
                return True
            else:
                print(f"❌ Health check failed: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {e}")
            print("   Make sure the Flask server is running on http://localhost:5000")
            return False
    
    def test_file_upload(self):
        """Test file upload endpoint"""
        print("\n=== Testing File Upload ===")
        
        try:
            # Create test image
            test_image = self.create_test_image()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                test_image.save(tmp_file.name)
                temp_path = tmp_file.name
            
            # Upload file
            with open(temp_path, 'rb') as f:
                files = {'file': ('test_answer_sheet.png', f, 'image/png')}
                data = {
                    'student_id': 'test_student_123',
                    'subject': 'mathematics',
                    'exam_id': 'test_exam_001'
                }
                
                response = requests.post(
                    f"{self.api_base}/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful!")
                print(f"   File ID: {data.get('file_id')}")
                print(f"   Filename: {data.get('filename')}")
                print(f"   File size: {data.get('file_size')} bytes")
                print(f"   File path: {data.get('file_path')}")
                
                # Clean up temp file
                os.unlink(temp_path)
                
                return data.get('file_path')
            else:
                print(f"❌ Upload failed: {response.text}")
                os.unlink(temp_path)
                return None
                
        except Exception as e:
            print(f"❌ Upload test failed: {e}")
            return None
    
    def test_analysis(self, file_path):
        """Test analysis endpoint"""
        print("\n=== Testing Analysis ===")
        
        if not file_path:
            print("❌ No file path provided for analysis")
            return None
        
        try:
            # Prepare analysis request
            rubrics = self.create_test_rubrics()
            
            payload = {
                "file_path": file_path,
                "rubrics": rubrics,
                "student_id": "test_student_123",
                "analysis_config": {
                    "enable_ai_analysis": False,  # Use basic analysis for testing
                    "confidence_threshold": 0.7,
                    "save_intermediate_results": True
                }
            }
            
            print(f"Analyzing file: {os.path.basename(file_path)}")
            print(f"Rubrics: {len(rubrics)} questions")
            
            response = requests.post(
                f"{self.api_base}/analyze",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Analysis might take longer
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Analysis successful!")
                
                results = data.get('analysis_results', {})
                print(f"   Analysis ID: {data.get('analysis_id')}")
                print(f"   Student ID: {data.get('student_id')}")
                print(f"   Overall Score: {results.get('percentage_score', 0):.1f}%")
                print(f"   Questions analyzed: {results.get('analyzed_questions')}/{results.get('total_questions')}")
                print(f"   Confidence: {results.get('confidence_score', 0):.2f}")
                print(f"   Processing time: {results.get('analysis_time', 0):.2f}s")
                
                # Show question results
                question_results = data.get('question_results', [])
                print(f"\n   Question Results:")
                for qr in question_results:
                    q_num = qr.get('question_number')
                    score = qr.get('score', 0)
                    marks = qr.get('marks_awarded', 0)
                    total = qr.get('total_marks', 0)
                    print(f"     Q{q_num}: {score:.2f} ({marks:.1f}/{total} marks)")
                
                # Show feedback summary
                feedback = data.get('feedback', {})
                if feedback:
                    print(f"\n   Feedback:")
                    print(f"     Overall: {feedback.get('overall_performance', 'No feedback')}")
                    
                    suggestions = feedback.get('improvement_suggestions', [])
                    if suggestions:
                        print(f"     Suggestions: {len(suggestions)} items")
                        for i, suggestion in enumerate(suggestions[:3], 1):
                            print(f"       {i}. {suggestion}")
                
                return data.get('analysis_id')
            else:
                print(f"❌ Analysis failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Analysis test failed: {e}")
            return None
    
    def test_get_results(self, analysis_id):
        """Test results retrieval endpoint"""
        print("\n=== Testing Results Retrieval ===")
        
        if not analysis_id:
            print("❌ No analysis ID provided")
            return False
        
        try:
            response = requests.get(
                f"{self.api_base}/results/{analysis_id}",
                params={
                    'include_details': 'true',
                    'include_feedback': 'true'
                },
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Results retrieved successfully!")
                print(f"   Analysis ID: {data.get('analysis_id')}")
                print(f"   Student ID: {data.get('student_id')}")
                print(f"   Overall Score: {data.get('percentage_score', 0):.1f}%")
                print(f"   Confidence: {data.get('confidence_score', 0):.2f}")
                print(f"   Created at: {data.get('created_at')}")
                
                return True
            else:
                print(f"❌ Results retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Results test failed: {e}")
            return False
    
    def test_history(self):
        """Test analysis history endpoint"""
        print("\n=== Testing Analysis History ===")
        
        try:
            response = requests.get(
                f"{self.api_base}/history",
                params={
                    'limit': 10,
                    'order_by': 'created_at',
                    'order_dir': 'desc'
                },
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ History retrieved successfully!")
                print(f"   Total count: {data.get('total_count', 0)}")
                print(f"   Returned: {data.get('returned_count', 0)}")
                
                analyses = data.get('analyses', [])
                if analyses:
                    print(f"   Recent analyses:")
                    for i, analysis in enumerate(analyses[:5], 1):
                        score = analysis.get('percentage_score', 0)
                        student = analysis.get('student_id', 'Unknown')
                        print(f"     {i}. {student}: {score:.1f}%")
                else:
                    print(f"   No previous analyses found")
                
                return True
            else:
                print(f"❌ History retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ History test failed: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        print("🧪 Starting Answer Analyzer API Test Suite")
        print("=" * 60)
        
        # Test 1: Health Check
        if not self.test_health_check():
            print("\n❌ Cannot proceed - service is not healthy")
            return False
        
        # Test 2: File Upload
        file_path = self.test_file_upload()
        if not file_path:
            print("\n❌ Cannot proceed - file upload failed")
            return False
        
        # Test 3: Analysis
        analysis_id = self.test_analysis(file_path)
        if not analysis_id:
            print("\n❌ Analysis failed")
            return False
        
        # Test 4: Results Retrieval
        if not self.test_get_results(analysis_id):
            print("\n❌ Results retrieval failed")
            return False
        
        # Test 5: History
        if not self.test_history():
            print("\n❌ History retrieval failed")
            return False
        
        print("\n🎉 All API tests passed successfully!")
        print("=" * 60)
        
        # Clean up uploaded file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print("🧹 Cleaned up test files")
        except:
            pass
        
        return True


def test_error_conditions():
    """Test various error conditions"""
    print("\n🚨 Testing Error Conditions")
    print("-" * 30)
    
    tester = AnalyzerAPITester()
    
    # Test 1: Upload without file
    print("Test 1: Upload without file...")
    try:
        response = requests.post(f"{tester.api_base}/upload", timeout=10)
        print(f"   Status: {response.status_code} ✅" if response.status_code == 400 else f"   Status: {response.status_code} ❌")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Analysis without file_path
    print("Test 2: Analysis without file_path...")
    try:
        response = requests.post(
            f"{tester.api_base}/analyze",
            json={"rubrics": []},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"   Status: {response.status_code} ✅" if response.status_code == 400 else f"   Status: {response.status_code} ❌")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get non-existent results
    print("Test 3: Get non-existent results...")
    try:
        response = requests.get(f"{tester.api_base}/results/nonexistent", timeout=10)
        print(f"   Status: {response.status_code} ✅" if response.status_code == 404 else f"   Status: {response.status_code} ❌")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("✅ Error condition tests completed")


if __name__ == "__main__":
    # Create tester instance
    tester = AnalyzerAPITester()
    
    # Run full test suite
    success = tester.run_full_test_suite()
    
    # Test error conditions
    test_error_conditions()
    
    # Final result
    if success:
        print("\n🎊 All tests completed successfully!")
        print("The Answer Analyzer API is working correctly.")
    else:
        print("\n⚠️ Some tests failed.")
        print("Check the server logs for more details.")

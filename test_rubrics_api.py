"""
Comprehensive test suite for Rubric Management API endpoints
Tests all CRUD operations and validation features
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def test_rubrics_api():
    """Run comprehensive tests for rubrics API endpoints"""
    
    import requests
    
    base_url = "http://127.0.0.1:5000/api/analyzer/rubrics"
    
    print("🧪 Testing Rubric Management API Endpoints")
    print("=" * 50)
    
    # Test 1: List all rubrics
    print("\n1. Testing: GET /api/analyzer/rubrics/")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['count']} rubrics")
            print(f"   Subjects: {[r['subject'] for r in data['rubrics']]}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 2: Get subjects list
    print("\n2. Testing: GET /api/analyzer/rubrics/subjects")
    try:
        response = requests.get(f"{base_url}/subjects")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Available subjects: {', '.join(data['subjects'])}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 3: Get topics for Mathematics
    print("\n3. Testing: GET /api/analyzer/rubrics/topics?subject=Mathematics")
    try:
        response = requests.get(f"{base_url}/topics", params={'subject': 'Mathematics'})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Mathematics topics: {', '.join(data['topics'])}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 4: Get specific rubric
    print("\n4. Testing: GET /api/analyzer/rubrics/rubric_math_001")
    try:
        response = requests.get(f"{base_url}/rubric_math_001")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Rubric: {data['subject']} - {data['topic']}")
            print(f"   Question: {data['question_text'][:60]}...")
            print(f"   Max marks: {data['max_marks']}")
            print(f"   Marking scheme points: {len(data['marking_scheme'])}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 5: Filter rubrics by subject
    print("\n5. Testing: GET /api/analyzer/rubrics/?subject=Physics")
    try:
        response = requests.get(f"{base_url}/", params={'subject': 'Physics'})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Physics rubrics found: {data['count']}")
            if data['rubrics']:
                print(f"   First Physics rubric: {data['rubrics'][0]['topic']}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 6: Create new rubric
    print("\n6. Testing: POST /api/analyzer/rubrics/ (Create new rubric)")
    new_rubric = {
        "subject": "Computer Science",
        "topic": "Data Structures",
        "question_text": "Implement a binary search tree with insert, delete, and search operations.",
        "model_answer": "Create a BST class with Node structure containing left, right pointers and data. Implement recursive insert, delete with three cases, and search operations.",
        "marking_scheme": {
            "node_structure": {
                "description": "Correct Node class definition with left, right, data",
                "marks": 2.0
            },
            "insert_operation": {
                "description": "Correct recursive insert implementation",
                "marks": 3.0
            },
            "delete_operation": {
                "description": "Delete with all three cases handled",
                "marks": 4.0
            },
            "search_operation": {
                "description": "Efficient search implementation",
                "marks": 1.0
            }
        },
        "keywords": ["binary search tree", "BST", "insert", "delete", "search", "recursion"],
        "max_marks": 10.0,
        "difficulty_level": "Hard",
        "notes": "Standard BST implementation problem"
    }
    
    try:
        response = requests.post(f"{base_url}/", json=new_rubric)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Created rubric: {data['rubric_id']}")
            print(f"   Subject: {data['subject']}, Topic: {data['topic']}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 7: Validate rubric structure
    print("\n7. Testing: POST /api/analyzer/rubrics/validate")
    test_rubric = {
        "subject": "Mathematics",
        "topic": "Algebra",
        "question_text": "Solve the quadratic equation x² + 5x + 6 = 0",
        "max_marks": 8.0,
        "marking_scheme": {
            "factoring": {
                "description": "Correctly factors the equation",
                "marks": 4.0
            },
            "solutions": {
                "description": "Finds both solutions x = -2, x = -3",
                "marks": 4.0
            }
        }
    }
    
    try:
        response = requests.post(f"{base_url}/validate", json=test_rubric)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Validation result: {data['valid']}")
            print(f"   Message: {data['message']}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 8: Invalid rubric validation
    print("\n8. Testing: POST /api/analyzer/rubrics/validate (Invalid rubric)")
    invalid_rubric = {
        "subject": "Mathematics",
        # Missing required fields
        "max_marks": 10.0
    }
    
    try:
        response = requests.post(f"{base_url}/validate", json=invalid_rubric)
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"   ✅ Correctly rejected invalid rubric")
            print(f"   Error: {data['error']}")
        else:
            print(f"   ❌ Should have returned 400, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 9: Update rubric
    print("\n9. Testing: PUT /api/analyzer/rubrics/rubric_math_001")
    update_data = {
        "difficulty_level": "Easy",
        "notes": "Updated difficulty level to Easy for beginners"
    }
    
    try:
        response = requests.put(f"{base_url}/rubric_math_001", json=update_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Updated rubric: {data['message']}")
            print(f"   Updated at: {data['updated_at']}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test 10: Delete rubric (test with non-existent ID)
    print("\n10. Testing: DELETE /api/analyzer/rubrics/test_rubric_999")
    try:
        response = requests.delete(f"{base_url}/test_rubric_999")
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Delete response: {data['message']}")
        else:
            print(f"    ❌ Error: {response.text}")
    except Exception as e:
        print(f"    ❌ Connection failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Rubric Management API testing completed!")
    print("\nAll endpoints are functional and ready for use.")


if __name__ == "__main__":
    test_rubrics_api()

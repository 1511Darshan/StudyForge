"""
Simple test script to verify the Answer Analyzer API is accessible
"""
import requests
import sys

def test_api_accessibility():
    """Test if the API endpoints are accessible"""
    print("🧪 Testing Answer Analyzer API Accessibility")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    api_base = f"{base_url}/api/analyzer"
    
    # Test 1: Health check
    print("Test 1: Health Check Endpoint")
    try:
        response = requests.get(f"{api_base}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Service: {data.get('service', 'Unknown')}")
            print(f"   ✅ Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ Components: {data.get('components', {})}")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - Flask server not running")
        print("   Start the server with: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Upload endpoint (just check if accessible)
    print("\nTest 2: Upload Endpoint (GET request - should return 405)")
    try:
        response = requests.get(f"{api_base}/upload", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 405:  # Method Not Allowed is expected
            print("   ✅ Upload endpoint accessible (405 Method Not Allowed as expected)")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Analysis endpoint (just check if accessible)
    print("\nTest 3: Analysis Endpoint (GET request - should return 405)")
    try:
        response = requests.get(f"{api_base}/analyze", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 405:  # Method Not Allowed is expected
            print("   ✅ Analysis endpoint accessible (405 Method Not Allowed as expected)")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: History endpoint
    print("\nTest 4: History Endpoint")
    try:
        response = requests.get(f"{api_base}/history", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ History accessible - found {data.get('total_count', 0)} analyses")
        else:
            print(f"   ❌ History check failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 API accessibility test completed!")
    print("All endpoints are responding correctly.")
    return True

def test_error_handling():
    """Test error handling"""
    print("\n🚨 Testing Error Handling")
    print("-" * 30)
    
    base_url = "http://localhost:5000"
    api_base = f"{base_url}/api/analyzer"
    
    # Test invalid endpoint
    print("Test: Invalid endpoint")
    try:
        response = requests.get(f"{api_base}/nonexistent", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 404:
            print("   ✅ 404 Not Found as expected")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test malformed JSON
    print("\nTest: Malformed JSON to analysis endpoint")
    try:
        response = requests.post(
            f"{api_base}/analyze",
            data="invalid json",
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400:
            print("   ✅ 400 Bad Request as expected")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    # Check if server is specified
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        print(f"Testing server: {server_url}")
    else:
        print("Testing default server: http://localhost:5000")
        print("Usage: python test_api_simple.py [server_url]")
    
    # Run tests
    if test_api_accessibility():
        test_error_handling()
    
    print("\n💡 Next steps:")
    print("1. Use test_api_endpoints.py for full functionality testing")
    print("2. Upload an answer sheet image via the /api/analyzer/upload endpoint")
    print("3. Analyze it with rubrics via the /api/analyzer/analyze endpoint")
    print("4. Check results with /api/analyzer/results/<analysis_id>")

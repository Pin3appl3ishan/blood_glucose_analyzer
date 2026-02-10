"""
API Test Script for Blood Glucose Analyzer Backend

Tests all major API endpoints to verify the backend is working correctly.
Run the Flask server first: python app.py

Usage: python test_api.py
"""

import requests
import json
import sys

# API base URL
BASE_URL = "http://localhost:5000"

# Test results tracking
tests_passed = 0
tests_failed = 0


def print_header(text):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_result(test_name, passed, details=""):
    """Print test result."""
    global tests_passed, tests_failed

    if passed:
        tests_passed += 1
        status = "\033[92mPASS\033[0m"  # Green
    else:
        tests_failed += 1
        status = "\033[91mFAIL\033[0m"  # Red

    print(f"[{status}] {test_name}")
    if details:
        print(f"       {details}")


def test_health_check():
    """Test GET / - Basic health check."""
    print_header("Test 1: Basic Health Check (GET /)")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        data = response.json()

        passed = (
            response.status_code == 200 and
            data.get("status") == "running" and
            "Blood Glucose Analyzer" in data.get("message", "")
        )

        print_result(
            "Basic health check",
            passed,
            f"Status: {data.get('status')}, Message: {data.get('message')}"
        )
        return passed

    except requests.exceptions.ConnectionError:
        print_result("Basic health check", False, "Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print_result("Basic health check", False, str(e))
        return False


def test_detailed_health():
    """Test GET /api/health - Detailed health check."""
    print_header("Test 2: Detailed Health Check (GET /api/health)")

    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = response.json()

        # Check structure
        has_services = "services" in data
        has_ocr = "ocr" in data.get("services", {})
        has_ml = "ml_model" in data.get("services", {})
        has_uploads = "uploads" in data.get("services", {})

        passed = has_services and has_ocr and has_ml and has_uploads

        print_result(
            "Detailed health check structure",
            passed,
            f"Status: {data.get('status')}"
        )

        # Print service details
        services = data.get("services", {})
        ocr_init = services.get("ocr", {}).get("initialized", False)
        ml_init = services.get("ml_model", {}).get("initialized", False)
        uploads_ok = services.get("uploads", {}).get("exists", False)

        print(f"       OCR Service: {'Ready' if ocr_init else 'Not initialized'}")
        print(f"       ML Model: {'Ready' if ml_init else 'Not initialized'}")
        print(f"       Uploads Folder: {'Ready' if uploads_ok else 'Not found'}")

        return passed

    except Exception as e:
        print_result("Detailed health check", False, str(e))
        return False


def test_manual_input_prediabetes():
    """Test POST /api/manual-input - Fasting 105 mg/dL (Prediabetes)."""
    print_header("Test 3: Manual Input - Fasting 105 mg/dL (Prediabetes)")

    try:
        payload = {
            "test_type": "fasting",
            "value": 105,
            "unit": "mg/dL"
        }

        response = requests.post(
            f"{BASE_URL}/api/manual-input",
            json=payload,
            timeout=5
        )
        data = response.json()

        classification = data.get("classification", {}).get("classification", "")

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            classification == "Prediabetes"
        )

        print_result(
            "Fasting 105 mg/dL classification",
            passed,
            f"Expected: Prediabetes, Got: {classification}"
        )

        if passed:
            severity = data.get("classification", {}).get("severity", "")
            print(f"       Severity: {severity}")

        return passed

    except Exception as e:
        print_result("Fasting 105 mg/dL classification", False, str(e))
        return False


def test_manual_input_normal():
    """Test POST /api/manual-input - Fasting 85 mg/dL (Normal)."""
    print_header("Test 4: Manual Input - Fasting 85 mg/dL (Normal)")

    try:
        payload = {
            "test_type": "fasting",
            "value": 85,
            "unit": "mg/dL"
        }

        response = requests.post(
            f"{BASE_URL}/api/manual-input",
            json=payload,
            timeout=5
        )
        data = response.json()

        classification = data.get("classification", {}).get("classification", "")

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            classification == "Normal"
        )

        print_result(
            "Fasting 85 mg/dL classification",
            passed,
            f"Expected: Normal, Got: {classification}"
        )

        if passed:
            severity = data.get("classification", {}).get("severity", "")
            print(f"       Severity: {severity}")

        return passed

    except Exception as e:
        print_result("Fasting 85 mg/dL classification", False, str(e))
        return False


def test_manual_input_diabetes():
    """Test POST /api/manual-input - HbA1c 6.8% (Diabetes)."""
    print_header("Test 5: Manual Input - HbA1c 6.8% (Diabetes)")

    try:
        payload = {
            "test_type": "hba1c",
            "value": 6.8,
            "unit": "%"
        }

        response = requests.post(
            f"{BASE_URL}/api/manual-input",
            json=payload,
            timeout=5
        )
        data = response.json()

        classification = data.get("classification", {}).get("classification", "")

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            classification == "Diabetes"
        )

        print_result(
            "HbA1c 6.8% classification",
            passed,
            f"Expected: Diabetes, Got: {classification}"
        )

        if passed:
            severity = data.get("classification", {}).get("severity", "")
            recommendation = data.get("classification", {}).get("recommendation", "")[:80]
            print(f"       Severity: {severity}")
            print(f"       Recommendation: {recommendation}...")

        return passed

    except Exception as e:
        print_result("HbA1c 6.8% classification", False, str(e))
        return False


def test_risk_prediction():
    """Test POST /api/predict-risk - Diabetes risk prediction."""
    print_header("Test 6: Risk Prediction (POST /api/predict-risk)")

    try:
        payload = {
            "glucose": 140,
            "bmi": 28,
            "age": 45,
            "blood_pressure": 85
        }

        response = requests.post(
            f"{BASE_URL}/api/predict-risk",
            json=payload,
            timeout=10
        )
        data = response.json()

        has_probability = "risk_probability" in data
        has_percentage = "risk_percentage" in data
        has_category = "risk_category" in data

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            has_probability and
            has_percentage and
            has_category
        )

        print_result(
            "Risk prediction",
            passed,
            f"Risk: {data.get('risk_percentage', 'N/A')}% ({data.get('risk_category', 'N/A')})"
        )

        if passed:
            confidence = data.get("confidence_level", "")
            print(f"       Confidence Level: {confidence}")
            print(f"       Factors Provided: {', '.join(data.get('factors_provided', []))}")

        return passed

    except Exception as e:
        print_result("Risk prediction", False, str(e))
        return False


def test_thresholds():
    """Test GET /api/thresholds - Get classification thresholds."""
    print_header("Test 7: Get Thresholds (GET /api/thresholds)")

    try:
        response = requests.get(f"{BASE_URL}/api/thresholds", timeout=5)
        data = response.json()

        has_thresholds = "thresholds" in data
        thresholds = data.get("thresholds", {})

        # Check for expected test types
        expected_types = ["fasting", "hba1c", "ppbs", "rbs", "ogtt"]
        found_types = [t for t in expected_types if t in thresholds]

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            has_thresholds and
            len(found_types) == len(expected_types)
        )

        print_result(
            "Get thresholds",
            passed,
            f"Found {len(found_types)}/{len(expected_types)} test types"
        )

        if passed:
            print(f"       Test types: {', '.join(found_types)}")

        return passed

    except Exception as e:
        print_result("Get thresholds", False, str(e))
        return False


def test_supported_tests():
    """Test GET /api/supported-tests - Get supported test types."""
    print_header("Test 8: Get Supported Tests (GET /api/supported-tests)")

    try:
        response = requests.get(f"{BASE_URL}/api/supported-tests", timeout=5)
        data = response.json()

        has_supported = "supported_types" in data
        has_description = "description" in data

        supported = data.get("supported_types", {})

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            has_supported and
            has_description and
            len(supported) > 0
        )

        print_result(
            "Get supported tests",
            passed,
            f"Found {len(supported)} supported test types"
        )

        if passed:
            print(f"       Types: {', '.join(supported.keys())}")

        return passed

    except Exception as e:
        print_result("Get supported tests", False, str(e))
        return False


def test_invalid_input():
    """Test POST /api/manual-input with invalid data."""
    print_header("Test 9: Invalid Input Handling")

    try:
        # Test missing fields
        payload = {"value": 100}  # Missing test_type

        response = requests.post(
            f"{BASE_URL}/api/manual-input",
            json=payload,
            timeout=5
        )
        data = response.json()

        passed = (
            response.status_code == 400 and
            data.get("success") == False and
            "error" in data
        )

        print_result(
            "Missing field validation",
            passed,
            f"Error: {data.get('error', 'No error message')}"
        )

        # Test invalid test type
        payload = {"test_type": "invalid_type", "value": 100, "unit": "mg/dL"}

        response = requests.post(
            f"{BASE_URL}/api/manual-input",
            json=payload,
            timeout=5
        )
        data = response.json()

        passed2 = (
            response.status_code == 400 and
            data.get("success") == False
        )

        print_result(
            "Invalid test type validation",
            passed2,
            f"Error: {data.get('error', 'No error message')}"
        )

        return passed and passed2

    except Exception as e:
        print_result("Invalid input handling", False, str(e))
        return False


def test_batch_input():
    """Test POST /api/manual-input/batch - Multiple readings."""
    print_header("Test 10: Batch Input (POST /api/manual-input/batch)")

    try:
        payload = {
            "readings": [
                {"test_type": "fasting", "value": 105, "unit": "mg/dL"},
                {"test_type": "hba1c", "value": 5.5, "unit": "%"},
                {"test_type": "ppbs", "value": 160, "unit": "mg/dL"}
            ]
        }

        response = requests.post(
            f"{BASE_URL}/api/manual-input/batch",
            json=payload,
            timeout=5
        )
        data = response.json()

        has_results = "results" in data
        has_summary = "summary" in data
        results = data.get("results", [])

        passed = (
            response.status_code == 200 and
            data.get("success") == True and
            has_results and
            has_summary and
            len(results) == 3
        )

        print_result(
            "Batch classification",
            passed,
            f"Processed {len(results)} readings"
        )

        if passed:
            summary = data.get("summary", {})
            print(f"       Overall Status: {summary.get('overall_status', 'N/A')}")
            print(f"       Overall Severity: {summary.get('overall_severity', 'N/A')}")

        return passed

    except Exception as e:
        print_result("Batch classification", False, str(e))
        return False


def run_all_tests():
    """Run all API tests."""
    print("\n" + "=" * 60)
    print("  BLOOD GLUCOSE ANALYZER - API TEST SUITE")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the Flask server is running: python app.py")

    # Check if server is running first
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n\033[91mERROR: Cannot connect to server at {}\033[0m".format(BASE_URL))
        print("Please start the Flask server first:")
        print("  cd backend")
        print("  python app.py")
        sys.exit(1)

    # Run all tests
    test_health_check()
    test_detailed_health()
    test_manual_input_prediabetes()
    test_manual_input_normal()
    test_manual_input_diabetes()
    test_risk_prediction()
    test_thresholds()
    test_supported_tests()
    test_invalid_input()
    test_batch_input()

    # Print summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    total = tests_passed + tests_failed
    print(f"\n  Total Tests: {total}")
    print(f"  \033[92mPassed: {tests_passed}\033[0m")
    print(f"  \033[91mFailed: {tests_failed}\033[0m")

    if tests_failed == 0:
        print("\n  \033[92m✓ All tests passed!\033[0m")
    else:
        print(f"\n  \033[91m✗ {tests_failed} test(s) failed\033[0m")

    print("\n" + "=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

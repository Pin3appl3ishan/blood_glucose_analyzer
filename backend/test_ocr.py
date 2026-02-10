"""
Test script for OCR Service
Usage: python test_ocr.py <path_to_image>
"""

import sys
import os

# Add the backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ocr_service import get_ocr_service


def test_ocr(image_path: str):
    """Test OCR service with a given image."""

    print(f"\n{'='*60}")
    print(f"Testing OCR with: {image_path}")
    print('='*60)

    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return

    # Get OCR service
    ocr = get_ocr_service()

    if not ocr.initialized:
        print(f"Error: OCR service failed to initialize: {ocr.init_error}")
        return

    print("\n[1] Extracting raw text...")
    print("-" * 40)

    text_result = ocr.extract_text(image_path)

    if text_result['success']:
        print(text_result.get('text', 'No text extracted'))
    else:
        print(f"Error: {text_result.get('error')}")

    print("\n[2] Extracting glucose values...")
    print("-" * 40)

    glucose_result = ocr.extract_glucose_values(image_path)

    if glucose_result['extraction_success']:
        values = glucose_result.get('detected_values', [])

        if values:
            print(f"Found {len(values)} glucose value(s):\n")
            for i, val in enumerate(values, 1):
                print(f"  {i}. Test Type: {val['test_type'].upper()}")
                print(f"     Value: {val['value']} {val['unit']}")
                print(f"     Confidence: {val['confidence']:.0%}")
                if 'row_text' in val:
                    print(f"     Source: {val['row_text']}")
                print()
        else:
            print("No glucose values detected in the image.")
            print("This could mean:")
            print("  - The image doesn't contain glucose test results")
            print("  - The text format wasn't recognized")
    else:
        print(f"Error: {glucose_result.get('error')}")

    print('='*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ocr.py <path_to_image>")
        print("\nExample:")
        print("  python test_ocr.py sample_report.jpg")
        print("  python test_ocr.py C:/path/to/lab_report.png")
        sys.exit(1)

    image_path = sys.argv[1]
    test_ocr(image_path)

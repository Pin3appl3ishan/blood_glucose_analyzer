"""
Blood Glucose Classification Service

Classifies blood glucose values based on American Diabetes Association (ADA) guidelines.
Provides severity levels and recommendations for different test types.

Reference: ADA Standards of Medical Care in Diabetes
"""

from typing import Dict, Any, Optional, Tuple


# Conversion factor: mmol/L to mg/dL
MMOL_TO_MGDL = 18.0


# Classification thresholds based on ADA guidelines
# Format: test_type -> list of (max_value, classification, severity)
# Values are in mg/dL (except HbA1c which is in %)
THRESHOLDS = {
    'fasting': {
        'unit': 'mg/dL',
        'ranges': [
            {'max': 70, 'classification': 'Low', 'severity': 'moderate'},
            {'max': 99, 'classification': 'Normal', 'severity': 'low'},
            {'max': 125, 'classification': 'Prediabetes', 'severity': 'moderate'},
            {'max': float('inf'), 'classification': 'Diabetes', 'severity': 'high'}
        ],
        'normal_range': {'min': 70, 'max': 99},
        'display_name': 'Fasting Blood Sugar (FBS)'
    },
    'hba1c': {
        'unit': '%',
        'ranges': [
            {'max': 4.0, 'classification': 'Low', 'severity': 'moderate'},
            {'max': 5.6, 'classification': 'Normal', 'severity': 'low'},
            {'max': 6.4, 'classification': 'Prediabetes', 'severity': 'moderate'},
            {'max': float('inf'), 'classification': 'Diabetes', 'severity': 'high'}
        ],
        'normal_range': {'min': 4.0, 'max': 5.6},
        'display_name': 'HbA1c (Glycated Hemoglobin)'
    },
    'ppbs': {
        'unit': 'mg/dL',
        'ranges': [
            {'max': 70, 'classification': 'Low', 'severity': 'moderate'},
            {'max': 139, 'classification': 'Normal', 'severity': 'low'},
            {'max': 199, 'classification': 'Prediabetes', 'severity': 'moderate'},
            {'max': float('inf'), 'classification': 'Diabetes', 'severity': 'high'}
        ],
        'normal_range': {'min': 70, 'max': 139},
        'display_name': 'Post-Prandial Blood Sugar (PPBS)'
    },
    'rbs': {
        'unit': 'mg/dL',
        'ranges': [
            {'max': 70, 'classification': 'Low', 'severity': 'moderate'},
            {'max': 139, 'classification': 'Normal', 'severity': 'low'},
            {'max': 199, 'classification': 'Needs Monitoring', 'severity': 'moderate'},
            {'max': float('inf'), 'classification': 'Diabetes', 'severity': 'high'}
        ],
        'normal_range': {'min': 70, 'max': 139},
        'display_name': 'Random Blood Sugar (RBS)'
    },
    'ogtt': {
        'unit': 'mg/dL',
        'ranges': [
            {'max': 70, 'classification': 'Low', 'severity': 'moderate'},
            {'max': 139, 'classification': 'Normal', 'severity': 'low'},
            {'max': 199, 'classification': 'Prediabetes', 'severity': 'moderate'},
            {'max': float('inf'), 'classification': 'Diabetes', 'severity': 'high'}
        ],
        'normal_range': {'min': 70, 'max': 139},
        'display_name': 'Oral Glucose Tolerance Test (OGTT 2-hour)'
    }
}


# Recommendations based on test type and classification
RECOMMENDATIONS = {
    'fasting': {
        'Low': (
            "Your fasting blood sugar is below the normal range. Low blood sugar "
            "(hypoglycemia) can cause symptoms like shakiness, sweating, and confusion. "
            "Consider eating regular, balanced meals. Please consult your healthcare "
            "provider to understand the cause and appropriate management."
        ),
        'Normal': (
            "Your fasting blood sugar is within the normal range. Continue maintaining "
            "a healthy lifestyle with balanced nutrition, regular physical activity, "
            "and routine health check-ups."
        ),
        'Prediabetes': (
            "Your fasting blood sugar indicates prediabetes. This means your blood sugar "
            "is higher than normal but not yet in the diabetes range. The good news is that "
            "lifestyle changes can often help prevent or delay progression to type 2 diabetes. "
            "Consider consulting your healthcare provider about diet modifications, increasing "
            "physical activity, and monitoring your blood sugar regularly."
        ),
        'Diabetes': (
            "Your fasting blood sugar is in the diabetes range. It's important to consult "
            "with a healthcare provider for proper diagnosis and to discuss a management plan. "
            "With appropriate care, diet, exercise, and possibly medication, blood sugar "
            "levels can be effectively managed."
        )
    },
    'hba1c': {
        'Low': (
            "Your HbA1c level is below the typical range. While this may indicate good "
            "blood sugar control, very low levels can sometimes indicate other conditions. "
            "Please consult your healthcare provider to discuss your results."
        ),
        'Normal': (
            "Your HbA1c is within the normal range, indicating good average blood sugar "
            "control over the past 2-3 months. Continue your healthy habits and maintain "
            "regular check-ups with your healthcare provider."
        ),
        'Prediabetes': (
            "Your HbA1c indicates prediabetes, meaning your average blood sugar over the "
            "past 2-3 months has been elevated. This is an opportunity to make positive "
            "changes. Research shows that lifestyle modifications including healthy eating, "
            "regular exercise, and maintaining a healthy weight can significantly reduce "
            "the risk of developing type 2 diabetes. Consider discussing a prevention "
            "plan with your healthcare provider."
        ),
        'Diabetes': (
            "Your HbA1c is in the diabetes range. This reflects your average blood sugar "
            "over the past 2-3 months. Please consult with a healthcare provider for "
            "proper diagnosis and to create a personalized management plan. Many people "
            "with diabetes lead healthy, active lives with proper care and monitoring."
        )
    },
    'ppbs': {
        'Low': (
            "Your post-meal blood sugar is below the expected range. This could indicate "
            "reactive hypoglycemia. Please consult your healthcare provider, especially "
            "if you experience symptoms like shakiness or dizziness after meals."
        ),
        'Normal': (
            "Your post-meal blood sugar is within the normal range. Your body is "
            "processing glucose effectively. Continue with your balanced eating habits "
            "and regular physical activity."
        ),
        'Prediabetes': (
            "Your post-meal blood sugar is elevated, which may indicate prediabetes. "
            "Your body may be having difficulty processing glucose after meals. "
            "Consider discussing with your healthcare provider about dietary adjustments, "
            "particularly reducing refined carbohydrates and added sugars."
        ),
        'Diabetes': (
            "Your post-meal blood sugar is in the diabetes range. Please consult with "
            "a healthcare provider for proper evaluation. Post-meal glucose management "
            "is important and can be addressed through diet, timing of meals, and "
            "potentially medication as recommended by your doctor."
        )
    },
    'rbs': {
        'Low': (
            "Your random blood sugar is below the normal range. If you're experiencing "
            "symptoms of low blood sugar, consider having a small snack. Please consult "
            "your healthcare provider to understand why your blood sugar may be low."
        ),
        'Normal': (
            "Your random blood sugar is within the normal range. This is a good sign "
            "of healthy glucose metabolism. Continue maintaining your healthy lifestyle."
        ),
        'Needs Monitoring': (
            "Your random blood sugar is elevated and needs monitoring. While a single "
            "random test isn't diagnostic, this result suggests you should follow up "
            "with your healthcare provider for additional testing, such as a fasting "
            "glucose or HbA1c test."
        ),
        'Diabetes': (
            "Your random blood sugar is significantly elevated. If you're experiencing "
            "symptoms like increased thirst, frequent urination, or unexplained weight loss, "
            "please consult a healthcare provider promptly. A proper diagnosis requires "
            "additional testing."
        )
    },
    'ogtt': {
        'Low': (
            "Your 2-hour glucose tolerance test result is below the expected range. "
            "Please discuss this result with your healthcare provider to understand "
            "its significance for your health."
        ),
        'Normal': (
            "Your glucose tolerance test result is normal. Your body is effectively "
            "processing and clearing glucose. Continue your healthy lifestyle habits."
        ),
        'Prediabetes': (
            "Your glucose tolerance test indicates prediabetes (impaired glucose tolerance). "
            "This means your body is taking longer than normal to process glucose. "
            "The positive news is that lifestyle interventions have been shown to be "
            "very effective at this stage. Consider speaking with your healthcare provider "
            "about a diabetes prevention program."
        ),
        'Diabetes': (
            "Your glucose tolerance test result is in the diabetes range. This indicates "
            "that your body has difficulty processing glucose. Please consult with a "
            "healthcare provider for confirmation and to discuss a comprehensive "
            "management approach."
        )
    }
}


# Standard medical disclaimer
DISCLAIMER = (
    "IMPORTANT: This analysis is for educational and informational purposes only. "
    "It is not intended to be a substitute for professional medical advice, diagnosis, "
    "or treatment. Always seek the advice of your physician or other qualified health "
    "provider with any questions you may have regarding a medical condition. Never "
    "disregard professional medical advice or delay in seeking it because of information "
    "provided by this tool."
)


def convert_to_mgdl(value: float, unit: str, test_type: str) -> Tuple[float, str]:
    """
    Convert glucose value to mg/dL if needed.

    Args:
        value: The glucose value
        unit: The unit of measurement ('mg/dL', 'mmol/L', or '%')
        test_type: The type of test

    Returns:
        Tuple of (converted_value, unit)
    """
    # HbA1c is always in percentage, no conversion needed
    if test_type == 'hba1c':
        return value, '%'

    # Convert mmol/L to mg/dL
    if unit.lower() in ['mmol/l', 'mmol']:
        return value * MMOL_TO_MGDL, 'mg/dL'

    return value, 'mg/dL'


def validate_input(test_type: str, value: float) -> Tuple[bool, Optional[str]]:
    """
    Validate input parameters.

    Args:
        test_type: The type of glucose test
        value: The glucose value

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check test type
    if test_type not in THRESHOLDS:
        valid_types = ', '.join(THRESHOLDS.keys())
        return False, f"Invalid test type '{test_type}'. Valid types: {valid_types}"

    # Check value is a positive number
    if not isinstance(value, (int, float)):
        return False, "Value must be a number"

    if value < 0:
        return False, "Value must be a positive number"

    # Check for unreasonable values
    if test_type == 'hba1c':
        if value > 20:
            return False, "HbA1c value seems unusually high. Please verify the value."
    else:
        if value > 1000:
            return False, "Glucose value seems unusually high. Please verify the value."

    return True, None


def get_classification_for_value(test_type: str, value: float) -> Dict[str, Any]:
    """
    Get the classification details for a given value.

    Args:
        test_type: The type of glucose test
        value: The glucose value (in mg/dL or % for HbA1c)

    Returns:
        Dictionary with classification, severity, and range
    """
    threshold_config = THRESHOLDS[test_type]
    ranges = threshold_config['ranges']

    prev_max = 0
    for range_info in ranges:
        if value <= range_info['max']:
            return {
                'classification': range_info['classification'],
                'severity': range_info['severity'],
                'range': {
                    'min': prev_max + (1 if prev_max > 0 else 0),
                    'max': range_info['max'] if range_info['max'] != float('inf') else None
                }
            }
        prev_max = range_info['max']

    # Fallback (shouldn't reach here due to infinity max)
    return {
        'classification': 'Unknown',
        'severity': 'unknown',
        'range': {'min': None, 'max': None}
    }


def get_recommendation(test_type: str, classification: str) -> str:
    """
    Get health recommendation based on test type and classification.

    Args:
        test_type: The type of glucose test
        classification: The classification result

    Returns:
        Recommendation text
    """
    test_recommendations = RECOMMENDATIONS.get(test_type, {})
    return test_recommendations.get(
        classification,
        "Please consult with your healthcare provider to discuss your results."
    )


def classify_glucose(test_type: str, value: float, unit: str = 'mg/dL') -> Dict[str, Any]:
    """
    Classify a blood glucose value based on ADA guidelines.

    Args:
        test_type: Type of glucose test ('fasting', 'hba1c', 'ppbs', 'rbs', 'ogtt')
        value: The glucose value
        unit: Unit of measurement ('mg/dL', 'mmol/L', or '%' for HbA1c)

    Returns:
        Dictionary containing:
        - test_type: The test type
        - original_value: Original value provided
        - original_unit: Original unit provided
        - value: Value used for classification (converted if needed)
        - unit: Unit used for classification
        - classification: Classification result (Normal, Prediabetes, Diabetes, etc.)
        - severity: Severity level (low, moderate, high)
        - range: The range for the classification
        - normal_range: The normal range for this test type
        - recommendation: Health recommendation text
        - disclaimer: Medical disclaimer
        - display_name: Human-readable test name
    """
    # Normalize test type
    test_type = test_type.lower().strip()

    # Validate input
    is_valid, error_message = validate_input(test_type, value)
    if not is_valid:
        return {
            'success': False,
            'error': error_message
        }

    # Store original values
    original_value = value
    original_unit = unit

    # Convert to standard units if needed
    converted_value, converted_unit = convert_to_mgdl(value, unit, test_type)

    # Get classification
    classification_result = get_classification_for_value(test_type, converted_value)

    # Get recommendation
    recommendation = get_recommendation(test_type, classification_result['classification'])

    # Get threshold config
    threshold_config = THRESHOLDS[test_type]

    return {
        'success': True,
        'test_type': test_type,
        'display_name': threshold_config['display_name'],
        'original_value': original_value,
        'original_unit': original_unit,
        'value': round(converted_value, 1),
        'unit': converted_unit,
        'classification': classification_result['classification'],
        'severity': classification_result['severity'],
        'range': classification_result['range'],
        'normal_range': threshold_config['normal_range'],
        'recommendation': recommendation,
        'disclaimer': DISCLAIMER
    }


def classify_multiple(readings: list) -> Dict[str, Any]:
    """
    Classify multiple glucose readings.

    Args:
        readings: List of dictionaries with 'test_type', 'value', and 'unit' keys

    Returns:
        Dictionary with results for each reading and summary
    """
    results = []
    has_diabetes = False
    has_prediabetes = False

    for reading in readings:
        test_type = reading.get('test_type', '')
        value = reading.get('value', 0)
        unit = reading.get('unit', 'mg/dL')

        result = classify_glucose(test_type, value, unit)
        results.append(result)

        if result.get('success'):
            classification = result.get('classification', '')
            if classification == 'Diabetes':
                has_diabetes = True
            elif classification in ['Prediabetes', 'Needs Monitoring']:
                has_prediabetes = True

    # Determine overall status
    if has_diabetes:
        overall_status = 'Diabetes Range Detected'
        overall_severity = 'high'
    elif has_prediabetes:
        overall_status = 'Prediabetes/Monitoring Needed'
        overall_severity = 'moderate'
    else:
        overall_status = 'Normal Range'
        overall_severity = 'low'

    return {
        'results': results,
        'summary': {
            'total_readings': len(readings),
            'overall_status': overall_status,
            'overall_severity': overall_severity
        },
        'disclaimer': DISCLAIMER
    }


def get_all_thresholds() -> Dict[str, Any]:
    """
    Get all threshold values for frontend display.

    Returns:
        Dictionary containing all test types with their thresholds and ranges
    """
    thresholds_data = {}

    for test_type, config in THRESHOLDS.items():
        ranges_display = []
        prev_max = 0

        for range_info in config['ranges']:
            max_val = range_info['max']
            if max_val == float('inf'):
                range_str = f">= {prev_max + 1}"
                max_display = None
            else:
                if prev_max == 0:
                    range_str = f"< {max_val + 1}"
                else:
                    range_str = f"{prev_max + 1} - {max_val}"
                max_display = max_val

            ranges_display.append({
                'classification': range_info['classification'],
                'severity': range_info['severity'],
                'min': prev_max + 1 if prev_max > 0 else 0,
                'max': max_display,
                'range_display': range_str
            })
            prev_max = max_val if max_val != float('inf') else prev_max

        thresholds_data[test_type] = {
            'display_name': config['display_name'],
            'unit': config['unit'],
            'normal_range': config['normal_range'],
            'ranges': ranges_display
        }

    return {
        'thresholds': thresholds_data,
        'disclaimer': DISCLAIMER
    }


# Convenience function for quick classification
def quick_classify(test_type: str, value: float, unit: str = 'mg/dL') -> str:
    """
    Quick classification that returns just the classification string.

    Args:
        test_type: Type of glucose test
        value: The glucose value
        unit: Unit of measurement

    Returns:
        Classification string or error message
    """
    result = classify_glucose(test_type, value, unit)
    if result.get('success'):
        return result['classification']
    return result.get('error', 'Classification failed')

"""
Report Validation Service

Validates uploaded lab reports to ensure they contain glucose-related test results.
Provides helpful feedback for incorrect report types.
"""

import re
from typing import Dict, Any, List, Set


# Glucose-related keywords that indicate a valid glucose report
GLUCOSE_KEYWORDS = {
    # General glucose terms
    'glucose', 'blood sugar', 'sugar level', 'blood glucose',

    # Fasting glucose
    'fasting', 'fbg', 'fbs', 'fasting blood sugar', 'fasting glucose',
    'fasting blood glucose', 'f.b.s', 'f.b.g',

    # HbA1c
    'hba1c', 'hb a1c', 'a1c', 'glycated', 'hemoglobin a1c', 'haemoglobin a1c',
    'glycohemoglobin', 'glycosylated hemoglobin', 'glycosylated haemoglobin',
    'hgba1c',

    # Post-prandial
    'ppbs', 'post prandial', 'postprandial', 'after meal', 'pp blood sugar',
    'post meal', '2 hour glucose', '2hr glucose', '2-hour glucose',
    'pp glucose', 'pbs',

    # Random blood sugar
    'rbs', 'random blood sugar', 'random glucose', 'r.b.s',
    'random blood glucose',

    # OGTT
    'ogtt', 'oral glucose tolerance', 'glucose tolerance', 'gtt',
    'glucose tolerance test',

    # General diabetes terms
    'diabetic', 'diabetes', 'glycemia', 'hyperglycemia', 'hypoglycemia',
    'prediabetes', 'pre-diabetes'
}

# Keywords for other report types (rejection indicators)
# These indicate non-glucose reports when found WITHOUT glucose keywords
REJECTION_KEYWORDS = {
    'haematology': {
        'keywords': {
            'rbc', 'wbc', 'platelet', 'platelets', 'mcv', 'mch', 'mchc',
            'hematocrit', 'haematocrit', 'neutrophil', 'lymphocyte',
            'monocyte', 'eosinophil', 'basophil', 'reticulocyte',
            'complete blood count', 'cbc', 'blood count', 'differential count',
            'packed cell volume', 'pcv', 'esr', 'erythrocyte sedimentation',
            'rdw', 'mpv', 'pdw'
        },
        'display_name': 'Complete Blood Count (CBC) / Haematology',
        'message': (
            "This appears to be a Complete Blood Count (CBC) or Haematology report. "
            "This app is designed to analyze glucose-related lab reports only. "
            "Please upload a report containing glucose tests such as Fasting Blood Sugar, "
            "HbA1c, Post-Prandial Blood Sugar, or similar glucose measurements."
        )
    },
    'lipid': {
        'keywords': {
            'cholesterol', 'triglyceride', 'triglycerides', 'hdl', 'ldl', 'vldl',
            'lipid profile', 'lipid panel', 'total cholesterol',
            'hdl cholesterol', 'ldl cholesterol', 'non-hdl',
            'cholesterol ratio', 'atherogenic'
        },
        'display_name': 'Lipid Profile',
        'message': (
            "This appears to be a Lipid Profile report (cholesterol test). "
            "This app analyzes glucose-related reports only. "
            "Please upload a report containing glucose tests like Fasting Blood Sugar, "
            "HbA1c, or Oral Glucose Tolerance Test results."
        )
    },
    'liver': {
        'keywords': {
            'sgpt', 'sgot', 'bilirubin', 'alt', 'ast', 'albumin',
            'liver function', 'lft', 'hepatic', 'alkaline phosphatase',
            'alp', 'ggt', 'gamma gt', 'total protein', 'globulin',
            'direct bilirubin', 'indirect bilirubin', 'conjugated bilirubin'
        },
        'display_name': 'Liver Function Test (LFT)',
        'message': (
            "This appears to be a Liver Function Test (LFT) report. "
            "This app is specifically designed for glucose analysis. "
            "Please upload a glucose-related report such as Fasting Blood Sugar, "
            "HbA1c, or Random Blood Sugar test results."
        )
    },
    'kidney': {
        'keywords': {
            'creatinine', 'urea', 'bun', 'gfr', 'egfr',
            'kidney function', 'renal function', 'kft', 'rft',
            'uric acid', 'blood urea nitrogen', 'microalbumin',
            'creatinine clearance', 'cystatin'
        },
        'display_name': 'Kidney Function Test (KFT)',
        'message': (
            "This appears to be a Kidney Function Test (KFT) report. "
            "This app focuses on blood glucose analysis. "
            "Please upload a report containing glucose measurements like "
            "Fasting Glucose, HbA1c, or Post-Prandial Blood Sugar."
        )
    },
    'thyroid': {
        'keywords': {
            'tsh', 't3', 't4', 'thyroid', 'ft3', 'ft4',
            'free t3', 'free t4', 'thyroid stimulating',
            'thyroxine', 'triiodothyronine', 'thyroid function',
            'thyroid profile', 'anti-tpo', 'tpo antibody'
        },
        'display_name': 'Thyroid Function Test',
        'message': (
            "This appears to be a Thyroid Function Test report. "
            "This app analyzes glucose and diabetes-related reports only. "
            "Please upload a report with glucose tests such as Fasting Blood Sugar, "
            "HbA1c, OGTT, or similar glucose measurements."
        )
    },
    'urine': {
        'keywords': {
            'urine routine', 'urinalysis', 'urine analysis',
            'urine culture', 'specific gravity', 'urine ph',
            'pus cells', 'epithelial cells', 'urine microscopy',
            'cast', 'crystals', 'urine protein', 'urine ketone'
        },
        'display_name': 'Urine Analysis',
        'message': (
            "This appears to be a Urine Analysis report. "
            "This app is designed for blood glucose report analysis. "
            "Please upload a blood test report containing glucose measurements."
        )
    },
    'cardiac': {
        'keywords': {
            'troponin', 'ck-mb', 'ckmb', 'bnp', 'nt-probnp',
            'cardiac markers', 'cardiac enzymes', 'cpk',
            'creatine kinase', 'myoglobin', 'ldh', 'homocysteine'
        },
        'display_name': 'Cardiac Markers',
        'message': (
            "This appears to be a Cardiac Markers test report. "
            "This app specializes in glucose analysis. "
            "Please upload a glucose-related report like Fasting Blood Sugar or HbA1c."
        )
    }
}

# Specific glucose test type keywords for detection
GLUCOSE_TEST_TYPES = {
    'fasting': {
        'keywords': {'fasting', 'fbg', 'fbs', 'f.b.s', 'f.b.g', 'fasting glucose',
                     'fasting blood sugar', 'fasting blood glucose'},
        'display_name': 'Fasting Blood Sugar (FBS)'
    },
    'hba1c': {
        'keywords': {'hba1c', 'hb a1c', 'a1c', 'glycated hemoglobin',
                     'glycated haemoglobin', 'glycohemoglobin', 'hgba1c',
                     'hemoglobin a1c', 'haemoglobin a1c', 'glycosylated'},
        'display_name': 'HbA1c (Glycated Hemoglobin)'
    },
    'ppbs': {
        'keywords': {'ppbs', 'post prandial', 'postprandial', 'pp blood sugar',
                     'post meal', 'after meal', '2 hour', '2hr', '2-hour',
                     'pp glucose', 'pbs'},
        'display_name': 'Post-Prandial Blood Sugar (PPBS)'
    },
    'rbs': {
        'keywords': {'rbs', 'random blood sugar', 'random glucose', 'r.b.s',
                     'random blood glucose'},
        'display_name': 'Random Blood Sugar (RBS)'
    },
    'ogtt': {
        'keywords': {'ogtt', 'oral glucose tolerance', 'glucose tolerance', 'gtt',
                     'glucose tolerance test'},
        'display_name': 'Oral Glucose Tolerance Test (OGTT)'
    }
}


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    # Convert to lowercase
    text = text.lower()
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    return text


def _find_keywords(text: str, keyword_set: Set[str]) -> List[str]:
    """
    Find all matching keywords in text.

    Args:
        text: Normalized text to search
        keyword_set: Set of keywords to look for

    Returns:
        List of found keywords
    """
    found = []
    for keyword in keyword_set:
        # Use word boundary matching for short keywords to avoid false positives
        if len(keyword) <= 3:
            # For short keywords like 'rbc', 'wbc', use word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                found.append(keyword)
        else:
            # For longer keywords, simple containment check
            if keyword in text:
                found.append(keyword)
    return found


def validate_glucose_report(extracted_text: str) -> Dict[str, Any]:
    """
    Validate if the extracted text is from a glucose-related lab report.

    Args:
        extracted_text: Text extracted from the lab report image

    Returns:
        Dictionary containing:
        - is_valid: Boolean indicating if this is a valid glucose report
        - confidence: Confidence score (0.0-1.0)
        - keywords_found: List of glucose keywords found
        - report_type_detected: Detected report type
        - message: Validation message
    """
    if not extracted_text or not extracted_text.strip():
        return {
            'is_valid': False,
            'confidence': 0.0,
            'keywords_found': [],
            'report_type_detected': 'unknown',
            'message': (
                "No text could be extracted from the image. "
                "Please ensure the image is clear and contains readable text. "
                "Try uploading a higher quality image of your glucose lab report."
            )
        }

    # Normalize text for matching
    normalized_text = _normalize_text(extracted_text)

    # Find glucose-related keywords
    glucose_keywords_found = _find_keywords(normalized_text, GLUCOSE_KEYWORDS)

    # Find rejection keywords for each report type
    rejection_matches = {}
    for report_type, config in REJECTION_KEYWORDS.items():
        found = _find_keywords(normalized_text, config['keywords'])
        if found:
            rejection_matches[report_type] = found

    # Calculate confidence and determine validity
    glucose_count = len(glucose_keywords_found)

    # Check for special case: "hemoglobin" alone (without "a1c" or "glycated")
    # should not count as glucose-related
    hemoglobin_alone = (
        'hemoglobin' in normalized_text and
        'a1c' not in normalized_text and
        'glycated' not in normalized_text and
        'glycosylated' not in normalized_text and
        'hba1c' not in normalized_text
    )

    if hemoglobin_alone and 'hemoglobin' in glucose_keywords_found:
        # This is likely a CBC report, not glucose
        glucose_keywords_found = [k for k in glucose_keywords_found if k != 'hemoglobin']
        glucose_count = len(glucose_keywords_found)

    # Determine if valid glucose report
    if glucose_count >= 2:
        # Strong glucose indicators
        confidence = min(0.95, 0.6 + (glucose_count * 0.1))
        return {
            'is_valid': True,
            'confidence': round(confidence, 2),
            'keywords_found': glucose_keywords_found,
            'report_type_detected': 'glucose',
            'message': "Valid glucose report detected. Proceeding with analysis."
        }

    elif glucose_count == 1:
        # Single glucose indicator - check if other report types are stronger
        total_rejection_keywords = sum(len(v) for v in rejection_matches.values())

        if total_rejection_keywords > 3:
            # Other report type is stronger
            detected_type = max(rejection_matches.keys(),
                               key=lambda k: len(rejection_matches[k]))
            return {
                'is_valid': False,
                'confidence': 0.3,
                'keywords_found': glucose_keywords_found,
                'report_type_detected': detected_type,
                'message': get_rejection_message(detected_type)
            }
        else:
            # Weak but possible glucose report
            return {
                'is_valid': True,
                'confidence': 0.5,
                'keywords_found': glucose_keywords_found,
                'report_type_detected': 'glucose',
                'message': (
                    "This may be a glucose report, but confidence is low. "
                    "Results may be limited. For best results, upload a report "
                    "that clearly shows glucose test results."
                )
            }

    else:
        # No glucose keywords found
        if rejection_matches:
            # Detected another report type
            detected_type = max(rejection_matches.keys(),
                               key=lambda k: len(rejection_matches[k]))
            confidence = min(0.9, 0.5 + (len(rejection_matches[detected_type]) * 0.1))
            return {
                'is_valid': False,
                'confidence': round(confidence, 2),
                'keywords_found': [],
                'report_type_detected': detected_type,
                'message': get_rejection_message(detected_type)
            }
        else:
            # Unknown report type
            return {
                'is_valid': False,
                'confidence': 0.0,
                'keywords_found': [],
                'report_type_detected': 'unknown',
                'message': (
                    "Unable to identify this as a glucose report. "
                    "Please upload a lab report containing glucose test results such as "
                    "Fasting Blood Sugar (FBS), HbA1c, Post-Prandial Blood Sugar (PPBS), "
                    "or Oral Glucose Tolerance Test (OGTT)."
                )
            }


def detect_report_type(extracted_text: str) -> Dict[str, Any]:
    """
    Detect the specific type of glucose test in the report.

    Args:
        extracted_text: Text extracted from the lab report

    Returns:
        Dictionary containing:
        - test_type: Detected test type code ('fasting', 'hba1c', etc.)
        - display_name: Human-readable test name
        - is_multiple: Whether multiple test types were detected
        - all_types: List of all detected test types
    """
    if not extracted_text or not extracted_text.strip():
        return {
            'test_type': 'unknown',
            'display_name': 'Unknown',
            'is_multiple': False,
            'all_types': []
        }

    normalized_text = _normalize_text(extracted_text)
    detected_types = []

    for test_type, config in GLUCOSE_TEST_TYPES.items():
        found = _find_keywords(normalized_text, config['keywords'])
        if found:
            detected_types.append({
                'type': test_type,
                'display_name': config['display_name'],
                'keywords_found': found,
                'match_count': len(found)
            })

    if not detected_types:
        # Check for generic glucose mention
        if 'glucose' in normalized_text or 'blood sugar' in normalized_text:
            return {
                'test_type': 'unknown',
                'display_name': 'Glucose Test (Type Unknown)',
                'is_multiple': False,
                'all_types': []
            }
        return {
            'test_type': 'unknown',
            'display_name': 'Unknown',
            'is_multiple': False,
            'all_types': []
        }

    if len(detected_types) == 1:
        return {
            'test_type': detected_types[0]['type'],
            'display_name': detected_types[0]['display_name'],
            'is_multiple': False,
            'all_types': [detected_types[0]['type']]
        }

    # Multiple test types detected
    # Sort by match count to get primary type
    detected_types.sort(key=lambda x: x['match_count'], reverse=True)

    return {
        'test_type': 'multiple',
        'display_name': 'Multiple Glucose Tests',
        'is_multiple': True,
        'all_types': [t['type'] for t in detected_types],
        'primary_type': detected_types[0]['type'],
        'details': detected_types
    }


def get_rejection_message(detected_type: str) -> str:
    """
    Get a user-friendly rejection message for a non-glucose report type.

    Args:
        detected_type: The detected report type code

    Returns:
        User-friendly rejection message
    """
    if detected_type in REJECTION_KEYWORDS:
        return REJECTION_KEYWORDS[detected_type]['message']

    # Default message for unknown types
    return (
        "This does not appear to be a glucose-related lab report. "
        "This app is designed to analyze blood glucose test results. "
        "Please upload a report containing Fasting Blood Sugar, HbA1c, "
        "Post-Prandial Blood Sugar, Random Blood Sugar, or OGTT results."
    )


def get_supported_report_types() -> Dict[str, Any]:
    """
    Get information about supported glucose test types.

    Returns:
        Dictionary with supported test types and their descriptions
    """
    supported = {}
    for test_type, config in GLUCOSE_TEST_TYPES.items():
        supported[test_type] = {
            'display_name': config['display_name'],
            'keywords': list(config['keywords'])[:5]  # Sample keywords
        }

    return {
        'supported_types': supported,
        'description': (
            "This app analyzes glucose-related lab reports including "
            "Fasting Blood Sugar (FBS), HbA1c, Post-Prandial Blood Sugar (PPBS), "
            "Random Blood Sugar (RBS), and Oral Glucose Tolerance Test (OGTT)."
        )
    }


def validate_image_text_quality(extracted_text: str) -> Dict[str, Any]:
    """
    Check if the extracted text quality is sufficient for analysis.

    Args:
        extracted_text: Text extracted from the image

    Returns:
        Dictionary with quality assessment
    """
    if not extracted_text:
        return {
            'is_sufficient': False,
            'word_count': 0,
            'has_numbers': False,
            'message': "No text was extracted from the image."
        }

    # Count words
    words = extracted_text.split()
    word_count = len(words)

    # Check for numbers (important for lab values)
    has_numbers = bool(re.search(r'\d+\.?\d*', extracted_text))

    # Check for decimal numbers (common in lab reports)
    has_decimal_numbers = bool(re.search(r'\d+\.\d+', extracted_text))

    # Assess quality
    if word_count < 5:
        return {
            'is_sufficient': False,
            'word_count': word_count,
            'has_numbers': has_numbers,
            'message': (
                "Very little text was extracted from the image. "
                "Please ensure the image is clear and well-lit. "
                "Try uploading a higher resolution image."
            )
        }

    if not has_numbers:
        return {
            'is_sufficient': False,
            'word_count': word_count,
            'has_numbers': False,
            'message': (
                "No numeric values were detected in the extracted text. "
                "Lab reports typically contain test values. "
                "Please ensure the image clearly shows the test results section."
            )
        }

    if word_count < 15:
        return {
            'is_sufficient': True,
            'word_count': word_count,
            'has_numbers': has_numbers,
            'quality': 'low',
            'message': (
                "Limited text was extracted. Results may be incomplete. "
                "For best results, ensure the entire report is visible in the image."
            )
        }

    return {
        'is_sufficient': True,
        'word_count': word_count,
        'has_numbers': has_numbers,
        'has_decimal_numbers': has_decimal_numbers,
        'quality': 'good' if word_count >= 30 else 'moderate',
        'message': "Text extraction quality is sufficient for analysis."
    }


def comprehensive_validation(extracted_text: str) -> Dict[str, Any]:
    """
    Perform comprehensive validation of extracted report text.

    Combines text quality check, report validation, and type detection.

    Args:
        extracted_text: Text extracted from the lab report image

    Returns:
        Comprehensive validation result
    """
    # Check text quality first
    quality_check = validate_image_text_quality(extracted_text)

    if not quality_check['is_sufficient']:
        return {
            'is_valid': False,
            'validation_stage': 'quality_check',
            'quality': quality_check,
            'report_validation': None,
            'report_type': None,
            'message': quality_check['message']
        }

    # Validate as glucose report
    report_validation = validate_glucose_report(extracted_text)

    if not report_validation['is_valid']:
        return {
            'is_valid': False,
            'validation_stage': 'report_validation',
            'quality': quality_check,
            'report_validation': report_validation,
            'report_type': None,
            'message': report_validation['message']
        }

    # Detect specific test type
    report_type = detect_report_type(extracted_text)

    return {
        'is_valid': True,
        'validation_stage': 'complete',
        'quality': quality_check,
        'report_validation': report_validation,
        'report_type': report_type,
        'message': (
            f"Valid glucose report detected: {report_type['display_name']}. "
            "Ready for analysis."
        )
    }

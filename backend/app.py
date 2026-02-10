"""
Blood Glucose Analyzer API

Flask backend that provides:
- Image upload and OCR extraction
- Report validation
- Glucose classification based on ADA guidelines
- Diabetes risk prediction using ML model
"""

import os
import uuid
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import configuration
from config import Config

# Import services
from services.ocr_service import get_ocr_service, extract_glucose_values
from services.classification_service import (
    classify_glucose,
    classify_multiple,
    get_all_thresholds,
    get_recommendation
)
from services.validation_service import (
    validate_glucose_report,
    detect_report_type,
    comprehensive_validation,
    get_supported_report_types
)
from services.ml_predictor import (
    predict_diabetes_risk,
    predict_diabetes_risk_with_explanation,
    get_prediction_thresholds,
    get_input_requirements,
    check_model_status,
    get_feature_importance
)
from services.database_service import get_database_service
from services.pdf_service import get_pdf_service


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent overwrites."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
    unique_name = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    return unique_name


def cleanup_file(filepath):
    """Remove a file if it exists."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        app.logger.warning(f"Failed to cleanup file {filepath}: {e}")


# ============================================
# Health Check Endpoints
# ============================================

@app.route('/')
def index():
    """Basic health check endpoint."""
    return jsonify({
        "status": "running",
        "message": "Blood Glucose Analyzer API",
        "version": "1.0.0"
    })


@app.route('/api/health')
def health_check():
    """Detailed system health check."""
    try:
        # Check OCR service
        ocr_service = get_ocr_service()
        ocr_status = {
            "initialized": ocr_service.initialized,
            "error": ocr_service.init_error if not ocr_service.initialized else None
        }

        # Check ML model
        ml_status = check_model_status()

        # Check uploads folder
        uploads_folder = app.config['UPLOAD_FOLDER']
        uploads_status = {
            "exists": os.path.exists(uploads_folder),
            "writable": os.access(uploads_folder, os.W_OK) if os.path.exists(uploads_folder) else False
        }

        # Determine overall status
        all_healthy = (
            ocr_status['initialized'] and
            ml_status.get('initialized', False) and
            uploads_status['exists'] and
            uploads_status['writable']
        )

        return jsonify({
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "ocr": ocr_status,
                "ml_model": {
                    "initialized": ml_status.get('initialized', False),
                    "model_info": ml_status.get('model_info'),
                    "error": ml_status.get('error')
                },
                "uploads": uploads_status
            }
        })

    except Exception as e:
        app.logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================
# File Upload Endpoint
# ============================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle image file upload."""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file part in request"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            }), 400

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        filename = generate_unique_filename(original_filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save file
        file.save(filepath)

        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "filename": filename,
            "original_filename": original_filename,
            "filepath": filepath
        })

    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# Analyze Endpoint (OCR + Validation + Classification)
# ============================================

@app.route('/api/analyze', methods=['POST'])
def analyze_report():
    """
    Analyze uploaded lab report image.

    Pipeline:
    1. Save uploaded image
    2. Extract text using OCR
    3. Validate as glucose report
    4. Extract and classify glucose values
    5. Return comprehensive analysis
    """
    filepath = None

    try:
        # Check for file in request
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file part in request"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            }), 400

        # Save file temporarily
        original_filename = secure_filename(file.filename)
        filename = generate_unique_filename(original_filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Step 1: Extract text and glucose values using OCR
        ocr_result = extract_glucose_values(filepath)

        if not ocr_result.get('extraction_success', False):
            cleanup_file(filepath)
            return jsonify({
                "success": False,
                "error": ocr_result.get('error', 'OCR extraction failed'),
                "message": "Failed to extract text from the image. Please ensure the image is clear and readable."
            }), 400

        extracted_text = ocr_result.get('raw_text', '')

        # Step 2: Validate as glucose report
        validation_result = comprehensive_validation(extracted_text)

        if not validation_result['is_valid']:
            cleanup_file(filepath)
            return jsonify({
                "success": False,
                "is_valid_report": False,
                "validation": validation_result,
                "extracted_text": extracted_text,
                "message": validation_result.get('message', 'This does not appear to be a glucose report.')
            })

        # Step 3: Get detected glucose values from OCR
        detected_values = ocr_result.get('detected_values', [])

        if not detected_values:
            cleanup_file(filepath)
            return jsonify({
                "success": True,
                "is_valid_report": True,
                "validation": validation_result,
                "extracted_text": extracted_text,
                "detected_values": [],
                "classifications": [],
                "message": "Report validated as glucose report, but no specific glucose values could be extracted. "
                          "The image may need to be clearer, or you can enter values manually."
            })

        # Step 4: Classify each detected glucose value
        classifications = []
        for value_info in detected_values:
            classification = classify_glucose(
                test_type=value_info['test_type'],
                value=value_info['value'],
                unit=value_info['unit']
            )

            if classification.get('success'):
                classifications.append({
                    "detected": value_info,
                    "classification": classification
                })

        # Step 5: Generate summary
        if classifications:
            # Check for concerning results
            severity_levels = [c['classification'].get('severity', 'low') for c in classifications]

            if 'high' in severity_levels:
                summary = "Analysis complete. Some values are in the diabetes range. Please consult a healthcare provider."
            elif 'moderate' in severity_levels:
                summary = "Analysis complete. Some values indicate prediabetes or need monitoring. Consider consulting a healthcare provider."
            else:
                summary = "Analysis complete. Values appear to be within normal range."
        else:
            summary = "Analysis complete. No classifiable glucose values found."

        # Cleanup temporary file
        cleanup_file(filepath)

        return jsonify({
            "success": True,
            "is_valid_report": True,
            "validation": validation_result,
            "extracted_text": extracted_text,
            "detected_values": detected_values,
            "classifications": classifications,
            "summary": summary,
            "analysis_timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        app.logger.error(f"Analysis error: {e}")
        cleanup_file(filepath)
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "An error occurred during analysis. Please try again."
        }), 500


# ============================================
# Manual Input Endpoint
# ============================================

@app.route('/api/manual-input', methods=['POST'])
def manual_input():
    """
    Handle manual glucose value input for classification.

    Expected JSON:
    {
        "test_type": "fasting",
        "value": 105,
        "unit": "mg/dL"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        # Validate required fields
        required_fields = ['test_type', 'value']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Get values with defaults
        test_type = data['test_type']
        value = data['value']
        unit = data.get('unit', 'mg/dL')

        # Validate value is a number
        try:
            value = float(value)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "Value must be a valid number"
            }), 400

        # Run classification
        result = classify_glucose(test_type, value, unit)

        if not result.get('success'):
            return jsonify({
                "success": False,
                "error": result.get('error', 'Classification failed')
            }), 400

        return jsonify({
            "success": True,
            "input": {
                "test_type": test_type,
                "value": value,
                "unit": unit
            },
            "classification": result
        })

    except Exception as e:
        app.logger.error(f"Manual input error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/manual-input/batch', methods=['POST'])
def manual_input_batch():
    """
    Handle multiple manual glucose value inputs.

    Expected JSON:
    {
        "readings": [
            {"test_type": "fasting", "value": 105, "unit": "mg/dL"},
            {"test_type": "hba1c", "value": 6.2, "unit": "%"}
        ]
    }
    """
    try:
        data = request.get_json()

        if not data or 'readings' not in data:
            return jsonify({
                "success": False,
                "error": "No readings provided. Expected: {\"readings\": [...]}"
            }), 400

        readings = data['readings']

        if not isinstance(readings, list) or len(readings) == 0:
            return jsonify({
                "success": False,
                "error": "Readings must be a non-empty array"
            }), 400

        # Classify all readings
        result = classify_multiple(readings)

        return jsonify({
            "success": True,
            "input_count": len(readings),
            **result
        })

    except Exception as e:
        app.logger.error(f"Batch input error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# Risk Prediction Endpoint
# ============================================

@app.route('/api/predict-risk', methods=['POST'])
def predict_risk():
    """
    Predict diabetes risk using ML model.

    Expected JSON:
    {
        "glucose": 105,
        "bmi": 25.5,
        "age": 45,
        "blood_pressure": 80,
        "insulin": 100,          // optional
        "skin_thickness": 20,    // optional
        "pregnancies": 2,        // optional
        "diabetes_pedigree": 0.5 // optional
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        # Run prediction (validation handled by service)
        result = predict_diabetes_risk(data)

        if not result.get('success'):
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict-risk/requirements', methods=['GET'])
def prediction_requirements():
    """Get input requirements for risk prediction."""
    try:
        return jsonify({
            "success": True,
            **get_input_requirements()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict-risk/thresholds', methods=['GET'])
def prediction_thresholds():
    """Get risk category thresholds."""
    try:
        return jsonify({
            "success": True,
            **get_prediction_thresholds()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict-risk/feature-importance', methods=['GET'])
def feature_importance():
    """Get feature importance from the ML model."""
    try:
        result = get_feature_importance()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict-risk/explain', methods=['POST'])
def predict_risk_with_explanation():
    """
    Predict diabetes risk with SHAP-based explanation and confidence interval.

    Same input as /api/predict-risk, but response includes:
    - explanation: SHAP feature contributions with plain English summaries
    - confidence_interval: prediction uncertainty range from RF tree variance
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        result = predict_diabetes_risk_with_explanation(data)

        if not result.get('success'):
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Explanation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# Reference Data Endpoints
# ============================================

@app.route('/api/thresholds', methods=['GET'])
def thresholds():
    """Get all glucose classification thresholds."""
    try:
        result = get_all_thresholds()
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/supported-tests', methods=['GET'])
def supported_tests():
    """Get list of supported glucose test types."""
    try:
        result = get_supported_report_types()
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# History & Persistence Endpoints
# ============================================

@app.route('/api/save-analysis', methods=['POST'])
def save_analysis():
    """Save an analysis result to history."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        analysis_type = data.get('analysis_type')
        if analysis_type not in ('ocr', 'manual', 'risk'):
            return jsonify({
                "success": False,
                "error": "analysis_type must be 'ocr', 'manual', or 'risk'"
            }), 400

        db = get_database_service()
        result = db.save_analysis(
            analysis_type=analysis_type,
            input_data=data.get('input_data'),
            result_data=data.get('result_data'),
            test_type=data.get('test_type'),
            glucose_value=data.get('glucose_value'),
            classification=data.get('classification'),
            risk_category=data.get('risk_category'),
            risk_percentage=data.get('risk_percentage'),
            label=data.get('label'),
        )

        if not result.get('success'):
            return jsonify(result), 500

        return jsonify(result), 201

    except Exception as e:
        app.logger.error(f"Save analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get analysis history with pagination."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        analysis_type = request.args.get('type', None)

        db = get_database_service()
        result = db.get_history(limit=limit, offset=offset, analysis_type=analysis_type)
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Get history error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/history/<analysis_id>', methods=['GET'])
def get_analysis_detail(analysis_id):
    """Get a single analysis by ID."""
    try:
        db = get_database_service()
        result = db.get_analysis(analysis_id)

        if not result.get('success'):
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Get analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/history/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """Delete an analysis from history."""
    try:
        db = get_database_service()
        result = db.delete_analysis(analysis_id)

        if not result.get('success'):
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Delete analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/trends', methods=['GET'])
def get_trends():
    """Get trend data for glucose value charts."""
    try:
        days = request.args.get('days', 30, type=int)
        test_type = request.args.get('test_type', None)

        db = get_database_service()
        result = db.get_trend_data(test_type=test_type, days=days)
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Get trends error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# PDF Report Endpoint
# ============================================

@app.route('/api/report/pdf/<analysis_id>', methods=['GET'])
def download_pdf_report(analysis_id):
    """Generate and download a PDF report for a saved analysis."""
    try:
        db = get_database_service()
        result = db.get_analysis(analysis_id)

        if not result.get('success'):
            return jsonify(result), 404

        pdf_service = get_pdf_service()
        pdf_bytes = pdf_service.generate_report(result['analysis'])

        from flask import Response
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=glucose-report-{analysis_id[:8]}.pdf'
            }
        )

    except Exception as e:
        app.logger.error(f"PDF generation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": "Bad request",
        "message": str(error)
    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "File too large",
        "message": f"Maximum file size is {Config.MAX_CONTENT_LENGTH // (1024 * 1024)}MB"
    }), 413


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================
# Application Entry Point
# ============================================

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Log startup info
    print("=" * 50)
    print("Blood Glucose Analyzer API")
    print("=" * 50)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Max file size: {Config.MAX_CONTENT_LENGTH // (1024 * 1024)}MB")
    print(f"Allowed extensions: {', '.join(Config.ALLOWED_EXTENSIONS)}")
    print("=" * 50)

    # Check services on startup
    ocr = get_ocr_service()
    print(f"OCR Service: {'Ready' if ocr.initialized else 'Not initialized - ' + str(ocr.init_error)}")

    ml_status = check_model_status()
    print(f"ML Model: {'Ready' if ml_status.get('initialized') else 'Not initialized - ' + str(ml_status.get('error'))}")
    print("=" * 50)

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)

# Blood Glucose Analyzer

An intelligent web application for analyzing blood glucose reports and predicting diabetes risk, designed specifically to improve healthcare accessibility in Nepal.

## Project Overview

This is an undergraduate Computer Science thesis project that addresses a critical gap in Nepal's healthcare landscape. Patients in Nepal often receive laboratory reports but lack access to professional interpretation due to healthcare accessibility challenges. This application provides educational interpretation of glucose-related blood tests and diabetes risk assessment.

**Important:** This application is an educational tool, NOT a medical diagnostic system. All results include appropriate disclaimers directing users to consult healthcare professionals.

## Problem Statement

In Nepal and similar developing regions:
- Patients receive lab reports but often cannot access doctors for interpretation
- Healthcare facilities are concentrated in urban areas
- There's limited awareness about prediabetes and early intervention
- Language and literacy barriers exist in understanding medical reports

This application bridges this gap by providing accessible, educational health information.

## System Architecture

The application operates as a **two-phase system**:

### Phase 1: Rule-Based Classification (Current Glucose Status)
- Analyzes uploaded glucose reports using OCR (Optical Character Recognition)
- Classifies glucose levels based on ADA (American Diabetes Association) guidelines
- Tells users: "Where am I NOW?" regarding glucose levels
- Supports: FBS, HbA1c, PPBS, RBS, OGTT reports

### Phase 2: Machine Learning Risk Prediction (Future Diabetes Risk)
- Predicts likelihood of developing diabetes using trained ML model
- Uses PIMA Indians Diabetes Dataset for model training
- Tells users: "What is my RISK of developing diabetes?"
- Considers: glucose, BMI, age, blood pressure, family history

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT                                    │
│         (Upload Report OR Manual Entry)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                              │
│         Is this a glucose-related report?                        │
│         ├── YES → Proceed to analysis                            │
│         └── NO  → Reject with helpful message                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 1: CLASSIFICATION                             │
│         Rule-based analysis using ADA guidelines                 │
│         Output: Normal / Prediabetes / Diabetes                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: RISK PREDICTION                            │
│         ML model trained on PIMA dataset                         │
│         Output: Risk percentage + category                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESULTS DISPLAY                               │
│         - Visual gauge charts                                    │
│         - Classification result                                  │
│         - Risk assessment                                        │
│         - Health recommendations                                 │
│         - Educational disclaimers                                │
└─────────────────────────────────────────────────────────────────┘
```

## Supported Report Types

| Report Type | Full Name | What It Measures | Unit |
|-------------|-----------|------------------|------|
| FBS | Fasting Blood Sugar | Glucose after 8-12 hour fast | mg/dL |
| HbA1c | Glycated Hemoglobin | Average glucose over 2-3 months | % |
| PPBS | Post-Prandial Blood Sugar | Glucose 2 hours after meal | mg/dL |
| RBS | Random Blood Sugar | Glucose at any random time | mg/dL |
| OGTT | Oral Glucose Tolerance Test | Glucose processing over time | mg/dL |

## Classification Thresholds (ADA Guidelines)

### Fasting Blood Sugar (mg/dL)
| Classification | Range |
|----------------|-------|
| Normal | < 100 |
| Prediabetes | 100 - 125 |
| Diabetes | ≥ 126 |

### HbA1c (%)
| Classification | Range |
|----------------|-------|
| Normal | < 5.7 |
| Prediabetes | 5.7 - 6.4 |
| Diabetes | ≥ 6.5 |

### Post-Prandial Blood Sugar (mg/dL)
| Classification | Range |
|----------------|-------|
| Normal | < 140 |
| Prediabetes | 140 - 199 |
| Diabetes | ≥ 200 |

### Random Blood Sugar (mg/dL)
| Classification | Range |
|----------------|-------|
| Normal | < 140 |
| Needs Monitoring | 140 - 199 |
| Diabetes | ≥ 200 |

## Tech Stack

### Backend
- **Framework:** Flask (Python)
- **OCR Engine:** PaddleOCR
- **Image Processing:** Pillow (PIL)
- **ML Libraries:** scikit-learn, pandas, numpy
- **Model Serialization:** joblib

> **Why PaddleOCR?** PaddleOCR was chosen over Tesseract for its superior handling of tabular document layouts common in laboratory reports (95%+ accuracy vs 85-90%), and its ability to return text with positional data for structured extraction. This is critical for parsing lab reports with columns like "Test Name | Value | Reference Range".

### Frontend
- **Framework:** React with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **Icons:** Lucide React
- **HTTP Client:** Axios

### Machine Learning
- **Dataset:** PIMA Indians Diabetes Dataset (768 samples, 8 features)
- **Algorithms:** Logistic Regression, Random Forest, SVM (comparison study)
- **Evaluation Metrics:** Accuracy, Precision, Recall, F1-Score, ROC-AUC

## Project Structure

```
blood-glucose-analyzer/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── requirements.txt       # Python dependencies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py     # Text extraction from images
│   │   ├── classification_service.py  # ADA-based classification
│   │   ├── ml_predictor.py    # Diabetes risk prediction
│   │   └── validation_service.py      # Report type validation
│   ├── models/
│   │   ├── diabetes_model.pkl # Trained ML model
│   │   └── scaler.pkl         # Feature scaler
│   └── uploads/               # Temporary upload storage
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ManualInputForm.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   ├── GaugeChart.tsx
│   │   │   ├── RiskAssessment.tsx
│   │   │   └── Disclaimer.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Analyze.tsx
│   │   │   └── About.tsx
│   │   ├── services/
│   │   │   └── api.ts         # API client functions
│   │   ├── types/
│   │   │   └── index.ts       # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tailwind.config.js
│
├── ml_training/
│   ├── train_model.py         # Model training script
│   ├── pima_diabetes.csv      # Training dataset
│   └── training_results.txt   # Metrics documentation
│
└── README.md
```

## API Endpoints

### Health Check
```
GET /
Response: {"status": "running"}
```

### Upload Report Image
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (image)
Response: {"message": "File received", "filename": "..."}
```

### Analyze Report (OCR + Classification)
```
POST /api/analyze
Content-Type: multipart/form-data
Body: file (image)
Response: {
    "validation": {"is_valid": true, "keywords_found": [...]},
    "extracted_values": [...],
    "classification": {
        "test_type": "fasting",
        "value": 105,
        "classification": "Prediabetes",
        "recommendation": "..."
    }
}
```

### Manual Input Classification
```
POST /api/manual-input
Content-Type: application/json
Body: {
    "test_type": "fasting",
    "value": 105,
    "unit": "mg/dL"
}
Response: {
    "classification": "Prediabetes",
    "severity": "moderate",
    "range": {"min": 100, "max": 125},
    "recommendation": "..."
}
```

### Diabetes Risk Prediction
```
POST /api/predict-risk
Content-Type: application/json
Body: {
    "glucose": 120,
    "bmi": 25.5,
    "age": 35,
    "blood_pressure": 80,
    "insulin": 0,           // optional
    "skin_thickness": 0,    // optional
    "pregnancies": 0,       // optional
    "diabetes_pedigree": 0.5 // optional, family history factor
}
Response: {
    "risk_probability": 0.67,
    "risk_percentage": 67,
    "risk_category": "High",
    "factors_used": [...],
    "disclaimer": "..."
}
```

### System Health
```
GET /api/health
Response: {
    "ocr_service": "operational",
    "ml_model": "loaded",
    "status": "healthy"
}
```

## PIMA Dataset Features

The ML model is trained on these 8 features:

| Feature | Description | Range |
|---------|-------------|-------|
| Pregnancies | Number of pregnancies | 0-17 |
| Glucose | Plasma glucose concentration (2hr OGTT) | 0-199 mg/dL |
| BloodPressure | Diastolic blood pressure | 0-122 mm Hg |
| SkinThickness | Triceps skin fold thickness | 0-99 mm |
| Insulin | 2-Hour serum insulin | 0-846 mu U/ml |
| BMI | Body mass index | 0-67.1 kg/m² |
| DiabetesPedigreeFunction | Diabetes pedigree (family history) | 0.078-2.42 |
| Age | Age in years | 21-81 |

**Output:** Binary classification (0 = No diabetes, 1 = Diabetes)

## Development Guidelines

### Code Style
- Python: Follow PEP 8 conventions
- TypeScript: Use strict typing, avoid `any`
- Components: Functional components with hooks
- Naming: Descriptive, self-documenting names

### Error Handling
- All API endpoints must have try-catch error handling
- Return meaningful error messages to frontend
- Log errors on backend for debugging

### Security Considerations
- No user data is stored permanently
- Uploaded images are processed and deleted
- No authentication required (educational tool)
- All processing happens locally (privacy-preserving)

### Accessibility
- Healthcare-appropriate color scheme (blues, greens, whites)
- Clear, readable fonts
- Mobile-responsive design
- Color-blind friendly indicators (not just red/green)

## Ethical Considerations

This project adheres to strict ethical guidelines:

1. **Educational Purpose Only:** Clear disclaimers that this is not medical advice
2. **Privacy:** No user data stored, local processing only
3. **Transparency:** Open about limitations and accuracy
4. **No Diagnosis:** Classification, not diagnosis - always recommend professional consultation
5. **Accessibility Focus:** Designed to help underserved populations access health information

## Limitations

1. **OCR Accuracy:** Depends on image quality and report format
2. **ML Model:** ~65-75% accuracy (acceptable for health prediction, not diagnosis)
3. **Report Types:** Only glucose-related reports supported
4. **Language:** Currently English only
5. **Guidelines:** Based on ADA standards, may differ from local guidelines

## Expected ML Model Performance

Based on PIMA dataset benchmarks:
- **Accuracy:** 65-75% (good)
- **Accuracy > 85%:** Likely overfitting, investigate
- **Accuracy < 60%:** Underfitting, needs improvement

Note: 100% accuracy is NOT the goal and would indicate a problem. Medical prediction inherently involves uncertainty.

## Future Enhancements (Out of Current Scope)

- Nepali language support
- Multi-parameter unified risk scoring
- Longitudinal trend analysis
- Explainable AI (SHAP values)
- PDF report generation
- Mobile application

## References

- American Diabetes Association (ADA) Standards of Medical Care
- PIMA Indians Diabetes Dataset (UCI Machine Learning Repository)
- WHO Guidelines on Diabetes Diagnosis

## Disclaimer

This application is developed as an educational tool for a Computer Science undergraduate thesis. It is NOT intended to replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers for medical decisions.

---

**Author:** Ishan  
**Project Type:** Undergraduate CS Thesis  
**Focus Area:** Healthcare Accessibility in Nepal  
**Deadline:** January 5, 2026
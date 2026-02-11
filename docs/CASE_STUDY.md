# Technical Case Study: Blood Glucose Analyzer

An AI-powered web application for glucose report analysis and diabetes risk prediction, built as an undergraduate thesis addressing healthcare accessibility in Nepal.

---

## 1. Problem Statement

### The Healthcare Gap in Nepal

Nepal's healthcare system faces structural challenges that disproportionately affect patients in rural and semi-urban areas:

- **Limited access to specialists:** Over 60% of healthcare facilities are concentrated in urban centers, leaving rural populations without convenient access to doctors who can interpret laboratory results.
- **Lab report literacy:** Patients routinely receive printed lab reports from pathology labs but lack the medical knowledge to understand what the numbers mean — particularly for chronic conditions like diabetes where early detection is critical.
- **Prediabetes awareness:** The prediabetes stage (where intervention is most effective) often goes unrecognized because patients never consult a doctor about borderline results.
- **Language and education barriers:** Medical terminology on lab reports is in English, while many patients are more comfortable with Nepali.

### What This Project Addresses

This application serves as an **educational tool** that helps patients understand their glucose-related lab results and assess their diabetes risk. It does not replace medical advice — every result screen includes disclaimers directing users to consult a healthcare professional.

The goal is to bridge the gap between *receiving* a lab report and *understanding* it, especially for the five most common glucose tests in Nepal: FBS, HbA1c, PPBS, RBS, and OGTT.

---

## 2. Architecture Overview

The system is designed as a two-phase pipeline with a React frontend and Flask backend:

```
┌──────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  Upload Report │ Manual Input │ Risk Assessment      │
└────────┬───────────────┬───────────────┬─────────────┘
         │               │               │
         ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  OCR Pipeline│ │ Classificati-│ │  ML Prediction   │
│  PaddleOCR   │ │ on ADA Rules │ │  Random Forest   │
│  + Validation│ │              │ │  + SHAP          │
└──────┬───────┘ └──────┬───────┘ └──────┬───────────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌──────────────────┐
              │   Persistence    │
              │  SQLite + PDF    │
              └──────────────────┘
```

### Service Layer

The backend is organized into focused services, each responsible for a single concern:

| Service | Responsibility |
|---------|---------------|
| `ocr_service.py` | Text extraction from lab report images using PaddleOCR |
| `validation_service.py` | Verifying that extracted text is from a glucose report |
| `classification_service.py` | ADA guideline-based glucose classification |
| `ml_predictor.py` | Random Forest diabetes risk prediction |
| `explainability_service.py` | SHAP value computation and plain-English summaries |
| `database_service.py` | SQLite storage for history and trends |
| `pdf_service.py` | PDF report generation with ReportLab |

All services are lazily initialized singletons — they load only when first accessed, keeping startup fast and memory usage predictable.

---

## 3. Technical Decisions

### Why PaddleOCR over Tesseract

Nepali laboratory reports typically use a tabular format with columns like "Test Name | Value | Unit | Reference Range". This layout is critical to parse correctly.

| Criterion | Tesseract | PaddleOCR |
|-----------|-----------|-----------|
| Tabular layout accuracy | ~85-90% | ~95%+ |
| Positional data (bounding boxes) | Basic | Detailed per-word |
| Pre-trained on diverse scripts | Good | Better for mixed English/Devanagari |
| Setup complexity | Simple | Moderate (PaddlePaddle dependency) |

PaddleOCR's ability to return text with spatial coordinates was the deciding factor — it allows structured extraction of values from specific columns rather than treating the page as a flat text block.

**Trade-off:** PaddleOCR pulls in PaddlePaddle (~500MB), making the Docker image significantly larger. For deployment on free-tier hosting, the OCR feature can be disabled while manual input and risk prediction remain functional.

### Why Random Forest for Risk Prediction

The model needs to be:
1. **Interpretable** — patients and healthcare workers should understand *why* a certain risk level was predicted
2. **Compatible with SHAP** — SHAP's TreeExplainer is highly optimized for tree-based models
3. **Robust to small datasets** — PIMA has only 768 samples; ensembles generalize better than single models

Random Forest met all three criteria. Logistic Regression was also evaluated (simpler, equally interpretable) but showed lower recall on the minority class. SVM performed similarly to RF on accuracy but lacks native probability calibration and SHAP compatibility.

### Why SHAP for Explainability

In a healthcare context, a risk percentage alone is insufficient. Patients need to know which factors contributed to their risk score. SHAP (SHapley Additive exPlanations) provides:

- **Per-feature contribution scores** — "Your glucose level increased your risk by 15%"
- **Direction** — whether a feature pushed risk up or down
- **Consistency** — SHAP values are mathematically grounded in game theory (Shapley values)

The explainability service translates raw SHAP values into plain-English summaries like "Your BMI of 32.1 (obese range) significantly increased your predicted risk."

### Why SQLite for Persistence

This is a single-user educational tool, not a multi-tenant SaaS application. SQLite provides:
- Zero configuration — no separate database server needed
- Single-file storage — easy to backup, move, or reset
- Sufficient performance for the expected access patterns
- Built into Python's standard library

For a production multi-user deployment, this would be swapped for PostgreSQL, but that is out of scope for the thesis.

---

## 4. ML Pipeline

### Dataset

**PIMA Indians Diabetes Dataset** (UCI Machine Learning Repository)
- **Samples:** 768 (500 non-diabetic, 268 diabetic)
- **Features:** 8 numeric attributes
- **Class imbalance:** ~65/35 split

| Feature | Description | Range |
|---------|-------------|-------|
| Pregnancies | Number of pregnancies | 0–17 |
| Glucose | Plasma glucose (2hr OGTT) | 0–199 mg/dL |
| BloodPressure | Diastolic blood pressure | 0–122 mm Hg |
| SkinThickness | Triceps skin fold | 0–99 mm |
| Insulin | 2-hour serum insulin | 0–846 mu U/ml |
| BMI | Body mass index | 0–67.1 kg/m² |
| DiabetesPedigreeFunction | Family history factor | 0.078–2.42 |
| Age | Age in years | 21–81 |

### Preprocessing

1. **Zero-value imputation:** Columns like Glucose, BloodPressure, and BMI have 0 values that represent missing data — these are replaced with median values.
2. **Feature scaling:** StandardScaler is applied to normalize ranges across features.
3. **Train/test split:** 80/20 stratified split to maintain class distribution.

### Training & Evaluation

Three models were compared:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|-----|---------|
| Logistic Regression | ~72% | ~68% | ~58% | ~63% | ~78% |
| **Random Forest** | **~74%** | **~70%** | **~62%** | **~66%** | **~80%** |
| SVM (RBF) | ~73% | ~69% | ~60% | ~64% | ~79% |

Random Forest was selected for its balanced performance and SHAP compatibility. The trained model and scaler are serialized with joblib as `.pkl` files.

### Confidence Intervals

The Random Forest's ensemble structure (100 trees) provides a natural mechanism for uncertainty estimation. The variance across individual tree predictions is used to compute a confidence interval for each risk score.

---

## 5. Challenges & Solutions

### OCR Noise Filtering

**Challenge:** Raw OCR output from lab reports contains headers, patient information, reference ranges, and non-glucose test results mixed in with glucose values.

**Solution:** A multi-stage pipeline:
1. Extract all text with bounding boxes
2. Apply regex patterns to identify numeric values with associated test keywords (e.g., "fasting", "HbA1c")
3. Validate extracted values against physiologically plausible ranges
4. Cross-reference with a keyword dictionary of glucose-related terms

### Model Calibration

**Challenge:** The PIMA dataset's class imbalance means the model tends to be overconfident on the majority class (non-diabetic).

**Solution:** Rather than presenting raw probabilities, the system maps predictions into three risk categories (Low < 30%, Moderate 30–60%, High > 60%) with clear descriptions. The confidence interval provides additional context about prediction uncertainty.

### Report Validation

**Challenge:** Users might upload non-glucose reports (e.g., CBC, thyroid panels) or non-medical images entirely.

**Solution:** A comprehensive validation service checks for:
- Medical report structure keywords ("laboratory", "report", "patient")
- Glucose-specific terminology ("glucose", "fasting", "HbA1c", "sugar")
- Numeric values in plausible ranges
- A confidence score that must exceed a threshold before classification proceeds

---

## 6. Results

### Classification Coverage

The system correctly classifies glucose values for all five supported test types, following ADA guidelines:

| Test Type | Classifications |
|-----------|----------------|
| Fasting Blood Sugar | Normal / Prediabetes / Diabetes |
| HbA1c | Normal / Prediabetes / Diabetes |
| Post-Prandial (PPBS) | Normal / Prediabetes / Diabetes |
| Random Blood Sugar | Normal / Needs Monitoring / Diabetes |
| OGTT | Normal / Prediabetes / Diabetes |

### ML Model Performance

- **Accuracy:** ~74% on held-out test set
- **ROC-AUC:** ~80%
- **Note:** Performance in the 65–75% range is expected and appropriate for this dataset. Accuracy above 85% would indicate overfitting.

### System Features Delivered

- OCR-based lab report analysis with structured value extraction
- Manual glucose value classification for all five ADA test types
- ML diabetes risk prediction with confidence intervals
- SHAP-based explainability with plain-English summaries
- Analysis history with trend visualization (line charts)
- PDF report generation for saved analyses
- Interactive Swagger API documentation

---

## 7. Key Takeaways

### What Worked Well

- **Service-oriented architecture** made it easy to develop, test, and iterate on each component independently. The OCR service could be improved without touching classification logic.
- **SHAP integration** added significant value — even with a relatively simple model, the per-feature explanations make results more trustworthy and educational.
- **Progressive disclosure** in the UI (gauge charts first, then details, then raw data) made complex medical information approachable.

### What Would Change With More Time

- **Nepali language support** — both for OCR extraction and UI localization. This is the single highest-impact improvement for the target audience.
- **PostgreSQL + user authentication** — to support multi-user scenarios and longitudinal tracking across devices.
- **Model retraining pipeline** — the current model is static. A feedback loop where validated results could improve the model over time would be valuable.
- **More test types** — expanding beyond glucose to cover lipid panels, thyroid function, and complete blood counts would make the tool more generally useful.

### Lessons Learned

1. OCR accuracy on real-world lab reports is highly variable — the validation layer is just as important as the extraction layer.
2. In healthcare applications, *explaining* a result matters as much as *computing* it.
3. Keeping the ML model modest (Random Forest, 768 samples) and transparent is more valuable than chasing accuracy with black-box deep learning when the goal is education.

---

*This case study was written as part of an undergraduate Computer Science thesis at the intersection of AI and healthcare accessibility.*

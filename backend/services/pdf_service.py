"""
PDF Report Service - Generate downloadable analysis reports.

Uses ReportLab to create professional PDF reports containing
analysis results, classifications, risk assessments, and SHAP explanations.
"""

import io
import json
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


# Color palette
BLUE = colors.HexColor('#4F46E5')
GREEN = colors.HexColor('#10B981')
AMBER = colors.HexColor('#F59E0B')
RED = colors.HexColor('#EF4444')
DARK = colors.HexColor('#1E293B')
MUTED = colors.HexColor('#64748B')
LIGHT_BG = colors.HexColor('#F8FAFC')
WHITE = colors.white

CLASSIFICATION_COLORS = {
    'Normal': GREEN,
    'Low': AMBER,
    'Prediabetes': AMBER,
    'Needs Monitoring': AMBER,
    'Diabetes': RED,
}

RISK_COLORS = {
    'Low': GREEN,
    'Moderate': AMBER,
    'High': RED,
}


def _get_styles():
    """Create custom paragraph styles."""
    base = getSampleStyleSheet()
    styles = {
        'title': ParagraphStyle(
            'CustomTitle',
            parent=base['Title'],
            fontSize=20,
            textColor=DARK,
            spaceAfter=4 * mm,
        ),
        'subtitle': ParagraphStyle(
            'CustomSubtitle',
            parent=base['Normal'],
            fontSize=10,
            textColor=MUTED,
            spaceAfter=8 * mm,
        ),
        'heading': ParagraphStyle(
            'CustomHeading',
            parent=base['Heading2'],
            fontSize=13,
            textColor=BLUE,
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
        ),
        'body': ParagraphStyle(
            'CustomBody',
            parent=base['Normal'],
            fontSize=10,
            textColor=DARK,
            leading=14,
            spaceAfter=2 * mm,
        ),
        'small': ParagraphStyle(
            'CustomSmall',
            parent=base['Normal'],
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
        'disclaimer': ParagraphStyle(
            'Disclaimer',
            parent=base['Normal'],
            fontSize=8,
            textColor=MUTED,
            leading=11,
            spaceBefore=4 * mm,
        ),
    }
    return styles


class PDFReportService:
    """Generate PDF reports from stored analyses."""

    def generate_report(self, analysis: Dict[str, Any]) -> bytes:
        """
        Generate a PDF report from an analysis record.

        Args:
            analysis: Full analysis record from database (with parsed JSON)

        Returns:
            PDF file contents as bytes
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = _get_styles()
        story = []

        # Header
        story.append(Paragraph('Blood Glucose Analysis Report', styles['title']))
        meta_parts = [f"Report ID: {analysis.get('id', 'N/A')}"]
        created = analysis.get('created_at', '')
        if created:
            try:
                dt = datetime.fromisoformat(created)
                meta_parts.append(f"Date: {dt.strftime('%B %d, %Y at %I:%M %p')}")
            except ValueError:
                meta_parts.append(f"Date: {created}")
        meta_parts.append(f"Type: {(analysis.get('analysis_type') or '').upper()}")
        story.append(Paragraph(' &nbsp;|&nbsp; '.join(meta_parts), styles['subtitle']))

        story.append(HRFlowable(width='100%', color=colors.HexColor('#E2E8F0'), thickness=0.5))
        story.append(Spacer(1, 4 * mm))

        result_data = analysis.get('result_data') or {}
        analysis_type = analysis.get('analysis_type', '')

        # Route to the right section builder
        if analysis_type == 'manual':
            self._build_manual_section(story, styles, analysis, result_data)
        elif analysis_type == 'risk':
            self._build_risk_section(story, styles, analysis, result_data)
        elif analysis_type == 'ocr':
            self._build_ocr_section(story, styles, analysis, result_data)

        # Disclaimer
        story.append(Spacer(1, 6 * mm))
        story.append(HRFlowable(width='100%', color=colors.HexColor('#E2E8F0'), thickness=0.5))
        disclaimer = result_data.get(
            'disclaimer',
            'This report is for educational purposes only and should not be considered '
            'a medical diagnosis. Please consult a healthcare professional for proper '
            'evaluation and diagnosis.',
        )
        story.append(Paragraph(f'<b>Disclaimer:</b> {disclaimer}', styles['disclaimer']))

        # Footer
        story.append(Spacer(1, 4 * mm))
        story.append(
            Paragraph(
                f'Generated by GlucoAnalyzer &nbsp;|&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                styles['small'],
            )
        )

        doc.build(story)
        return buf.getvalue()

    def _build_manual_section(self, story, styles, analysis, result_data):
        """Build sections for manual input results."""
        classification = result_data.get('classification', {})
        if not classification:
            story.append(Paragraph('No classification data available.', styles['body']))
            return

        story.append(Paragraph('Classification Result', styles['heading']))

        table_data = [
            ['Test Type', classification.get('display_name', 'N/A')],
            ['Value', f"{classification.get('value', 'N/A')} {classification.get('unit', '')}"],
            [
                'Normal Range',
                f"{classification.get('normal_range', {}).get('min', '')} - "
                f"{classification.get('normal_range', {}).get('max', '')} "
                f"{classification.get('unit', '')}",
            ],
            ['Classification', classification.get('classification', 'N/A')],
            ['Severity', (classification.get('severity') or '').capitalize()],
        ]
        story.append(self._make_table(table_data))

        rec = classification.get('recommendation')
        if rec:
            story.append(Paragraph('Recommendation', styles['heading']))
            story.append(Paragraph(rec, styles['body']))

    def _build_risk_section(self, story, styles, analysis, result_data):
        """Build sections for risk prediction results."""
        story.append(Paragraph('Risk Assessment', styles['heading']))

        risk_pct = result_data.get('risk_percentage', 0)
        category = result_data.get('risk_category', 'N/A')

        table_data = [
            ['Risk Score', f"{risk_pct:.1f}%"],
            ['Risk Category', category],
            ['Confidence', (result_data.get('confidence_level') or '').capitalize()],
            ['Factors Analyzed', str(len(result_data.get('factors_provided', [])))],
        ]
        story.append(self._make_table(table_data))

        desc = result_data.get('risk_description')
        if desc:
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(desc, styles['body']))

        # Input values
        input_vals = result_data.get('input_values', {})
        if input_vals:
            story.append(Paragraph('Health Metrics Used', styles['heading']))
            metrics = [
                ['Metric', 'Value'],
                ['Glucose', f"{input_vals.get('glucose', 'N/A')} mg/dL"],
                ['BMI', f"{input_vals.get('bmi', 'N/A')} kg/m\u00b2"],
                ['Age', f"{input_vals.get('age', 'N/A')} years"],
                ['Blood Pressure', f"{input_vals.get('blood_pressure', 'N/A')} mmHg"],
            ]
            if input_vals.get('insulin'):
                metrics.append(['Insulin', f"{input_vals['insulin']} \u03bcU/mL"])
            if input_vals.get('pregnancies'):
                metrics.append(['Pregnancies', str(input_vals['pregnancies'])])
            story.append(self._make_table(metrics, has_header=True))

        # SHAP explanation
        explanation = result_data.get('explanation', {})
        if explanation and not explanation.get('error'):
            story.append(Paragraph('AI Explanation (SHAP Analysis)', styles['heading']))
            summary = explanation.get('plain_english_summary', '')
            if summary:
                story.append(Paragraph(summary, styles['body']))

            contributions = explanation.get('feature_contributions', [])
            if contributions:
                story.append(Spacer(1, 2 * mm))
                contrib_data = [['Factor', 'Impact', 'Direction']]
                for fc in contributions:
                    direction = '\u2191 Risk' if fc['direction'] == 'risk' else '\u2193 Protective'
                    contrib_data.append([
                        fc['display_name'],
                        f"{fc['contribution_pct']:.1f}%",
                        direction,
                    ])
                story.append(self._make_table(contrib_data, has_header=True))

        # Confidence interval
        ci = result_data.get('confidence_interval', {})
        if ci and not ci.get('error'):
            story.append(Paragraph('Prediction Confidence', styles['heading']))
            story.append(
                Paragraph(
                    f"The model estimates your risk between "
                    f"<b>{ci.get('ci_lower_pct', 0):.1f}%</b> and "
                    f"<b>{ci.get('ci_upper_pct', 0):.1f}%</b> "
                    f"(95% confidence interval based on {ci.get('tree_count', 100)} decision trees).",
                    styles['body'],
                )
            )

    def _build_ocr_section(self, story, styles, analysis, result_data):
        """Build sections for OCR analysis results."""
        story.append(Paragraph('OCR Analysis Results', styles['heading']))

        summary = result_data.get('summary')
        if summary:
            story.append(Paragraph(summary, styles['body']))

        classifications = result_data.get('classifications', [])
        if classifications:
            story.append(Paragraph('Detected Values', styles['heading']))
            table_data = [['Test Type', 'Value', 'Classification', 'Severity']]
            for item in classifications:
                c = item.get('classification', {})
                table_data.append([
                    c.get('display_name', 'N/A'),
                    f"{c.get('value', 'N/A')} {c.get('unit', '')}",
                    c.get('classification', 'N/A'),
                    (c.get('severity') or '').capitalize(),
                ])
            story.append(self._make_table(table_data, has_header=True))

            # Recommendations for each
            for item in classifications:
                c = item.get('classification', {})
                rec = c.get('recommendation')
                if rec:
                    story.append(Spacer(1, 2 * mm))
                    story.append(
                        Paragraph(
                            f"<b>{c.get('display_name', '')}:</b> {rec}",
                            styles['body'],
                        )
                    )

    def _make_table(self, data, has_header=False):
        """Create a styled table."""
        col_count = len(data[0]) if data else 1
        col_width = (A4[0] - 40 * mm) / col_count

        t = Table(data, colWidths=[col_width] * col_count)

        style_commands = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), DARK),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1 if has_header else 0), (-1, -1), [WHITE, LIGHT_BG]),
        ]

        if has_header:
            style_commands.extend([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), BLUE),
            ])
        else:
            # Key-value style: bold first column
            style_commands.append(('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'))

        t.setStyle(TableStyle(style_commands))
        return t


# Singleton
_pdf_instance: Optional[PDFReportService] = None


def get_pdf_service() -> PDFReportService:
    global _pdf_instance
    if _pdf_instance is None:
        _pdf_instance = PDFReportService()
    return _pdf_instance

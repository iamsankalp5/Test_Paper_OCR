"""
Report generator for creating PDF and JSON reports.
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from app.config.logging_config import get_logger
from app.core.utils import ensure_directory_exists


logger = get_logger(__name__)


class ReportGenerator:
    """Generates comprehensive test reports in PDF and JSON formats."""
    
    def __init__(self):
        """Initialize report generator."""
        logger.info("ReportGenerator initialized")
    
    def _clean_markdown_text(self, text: str) -> str:
        """
        Convert markdown formatting to HTML for PDF rendering.
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            HTML-formatted text for reportlab
        """
        if not text:
            return ""
        
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        
        # Convert *italic* to <i>italic</i>
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        
        # Preserve line breaks
        text = text.replace('\n', '<br/>')
        
        return text
    
    def _wrap_text(self, text: str, max_length: int = 500) -> str:
        """
        Wrap long text for better PDF rendering.
        
        Args:
            text: Text to wrap
            max_length: Maximum length before wrapping
            
        Returns:
            Wrapped text
        """
        if not text or len(text) <= max_length:
            return text or "N/A"
        
        # Return full text (no truncation)
        return text
    
    def generate_pdf_report(
        self,
        job_data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate PDF report.
        
        Args:
            job_data: Complete job data dictionary
            output_path: Path to save PDF report
            
        Returns:
            Path to generated PDF file
            
        Raises:
            Exception: If PDF generation fails
        """
        try:
            logger.info(f"Generating PDF report: {output_path}")
            
            # Ensure directory exists
            ensure_directory_exists(os.path.dirname(output_path))
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=letter,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5490'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2e7d32'),
                spaceAfter=12,
                spaceBefore=16,
                fontName='Helvetica-Bold'
            )
            
            subheading_style = ParagraphStyle(
                'CustomSubheading',
                parent=styles['Heading3'],
                fontSize=11,
                textColor=colors.HexColor('#1976d2'),
                spaceAfter=8,
                spaceBefore=10,
                fontName='Helvetica-Bold'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=10,
                leading=14,
                alignment=TA_JUSTIFY,
                spaceAfter=6
            )
            
            # Title
            story.append(Paragraph("TEST ASSESSMENT REPORT", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Student Information
            story.append(Paragraph("Student Information", heading_style))
            student_data = [
                ['Student Name:', job_data.get('student_name', 'N/A')],
                ['Student ID:', job_data.get('student_id', 'N/A')],
                ['Exam:', job_data.get('exam_name', 'N/A')],
                ['Subject:', job_data.get('subject', 'N/A')],
                ['Date:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            student_table = Table(student_data, colWidths=[2*inch, 4.5*inch])
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(student_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Overall Performance
            story.append(Paragraph("Overall Performance", heading_style))
            
            feedback = job_data.get('feedback', {})
            grade = feedback.get('grade', 'N/A')
            if grade == 'N/A':
                percentage = job_data.get('percentage', 0)
                if percentage >= 90:
                    grade = 'S'
                elif percentage >= 80:
                    grade = 'A'
                elif percentage >= 70:
                    grade = 'B'
                elif percentage >= 60:
                    grade = 'C'
                elif percentage >= 50:
                    grade = 'D'
                else:
                    grade = 'F'
            
            performance_data = [
                ['Total Marks:', str(job_data.get('total_marks', 0))],
                ['Marks Obtained:', str(round(job_data.get('total_marks_obtained', 0), 2))],
                ['Percentage:', f"{job_data.get('percentage', 0):.2f}%"],
                ['Grade:', grade]
            ]
            
            performance_table = Table(performance_data, colWidths=[2*inch, 4.5*inch])
            performance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(performance_table)
            story.append(Spacer(1, 0.3*inch))
            
            # AI Insights / Feedback Section
            story.append(Paragraph("AI Insights", heading_style))
            
            # Overall Feedback
            overall_feedback = feedback.get('overall_feedback', 'No feedback available.')
            cleaned_feedback = self._clean_markdown_text(overall_feedback)
            story.append(Paragraph(cleaned_feedback, body_style))
            story.append(Spacer(1, 0.15*inch))
            
            # Strengths
            strengths = feedback.get('strengths', [])
            if strengths and len(strengths) > 0:
                story.append(Paragraph("<b>Strengths:</b>", subheading_style))
                for strength in strengths:
                    if strength:
                        cleaned_strength = self._clean_markdown_text(strength)
                        story.append(Paragraph(f"• {cleaned_strength}", body_style))
                story.append(Spacer(1, 0.1*inch))
            
            # Areas for Improvement
            areas_for_improvement = feedback.get('areas_for_improvement', [])
            if areas_for_improvement and len(areas_for_improvement) > 0:
                story.append(Paragraph("<b>Areas for Improvement:</b>", subheading_style))
                for area in areas_for_improvement:
                    if area:
                        cleaned_area = self._clean_markdown_text(area)
                        story.append(Paragraph(f"• {cleaned_area}", body_style))
                story.append(Spacer(1, 0.1*inch))
            
            # Recommendations
            recommendations = feedback.get('recommendations', [])
            if recommendations and len(recommendations) > 0:
                story.append(Paragraph("<b>Recommendations:</b>", subheading_style))
                for rec in recommendations:
                    if rec:
                        cleaned_rec = self._clean_markdown_text(rec)
                        story.append(Paragraph(f"• {cleaned_rec}", body_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Detailed Question-wise Assessment
            if job_data.get('assessed_answers'):
                story.append(PageBreak())
                story.append(Paragraph("Detailed Question-wise Assessment", heading_style))
                story.append(Spacer(1, 0.2*inch))
                
                for answer in job_data['assessed_answers']:
                    q_num = answer.get('question_number', 'N/A')
                    question_text = self._wrap_text(answer.get('question_text', 'N/A'))
                    
                    story.append(Paragraph(
                        f"<b>Question {q_num}:</b>", 
                        subheading_style
                    ))
                    story.append(Paragraph(question_text, body_style))
                    story.append(Spacer(1, 0.08*inch))
                    
                    # Full answer text (no truncation)
                    answer_text = self._wrap_text(str(answer.get('answer_text', 'N/A')))
                    story.append(Paragraph(f"<b>Your Answer:</b>", body_style))
                    story.append(Paragraph(answer_text, body_style))
                    story.append(Spacer(1, 0.08*inch))
                    
                    marks_text = f"{answer.get('marks_obtained', 0)}/{answer.get('max_marks', 0)}"
                    story.append(Paragraph(f"<b>Marks:</b> {marks_text}", body_style))
                    story.append(Spacer(1, 0.08*inch))
                    
                    explanation = self._wrap_text(answer.get('explanation', 'N/A'))
                    cleaned_explanation = self._clean_markdown_text(explanation)
                    story.append(Paragraph(f"<b>Assessment:</b>", body_style))
                    story.append(Paragraph(cleaned_explanation, body_style))
                    story.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(story)
            logger.info(f"PDF report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF report generation failed: {str(e)}", exc_info=True)
            raise Exception(f"PDF report generation failed: {str(e)}")
    
    def generate_json_report(
        self,
        job_data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate JSON report.
        
        Args:
            job_data: Complete job data dictionary
            output_path: Path to save JSON report
            
        Returns:
            Path to generated JSON file
            
        Raises:
            Exception: If JSON generation fails
        """
        try:
            logger.info(f"Generating JSON report: {output_path}")
            
            # Ensure directory exists
            ensure_directory_exists(os.path.dirname(output_path))
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"JSON report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"JSON report generation failed: {str(e)}", exc_info=True)
            raise Exception(f"JSON report generation failed: {str(e)}")

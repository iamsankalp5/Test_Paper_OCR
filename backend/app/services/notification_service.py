"""
Notification service for email and other delivery methods.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
from app.config.logging_config import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


class NotificationService:
    """Service for sending notifications via email."""
    
    def __init__(self):
        """Initialize notification service."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        logger.info("NotificationService initialized")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            attachments: Optional list of file paths to attach
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email")
                return False
            
            logger.info(f"Sending email to: {to_email}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            attachment = MIMEApplication(f.read())
                            attachment.add_header('Content-Disposition', 'attachment',
                                                filename=file_path.split('/')[-1])
                            msg.attach(attachment)
                    except Exception as e:
                        logger.error(f"Failed to attach file {file_path}: {str(e)}")
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}", exc_info=True)
            return False
    
    async def send_report_email(
        self,
        student_name: str,
        student_email: str,
        report_path: str,
        grade: str,
        percentage: float
    ) -> bool:
        """
        Send test report via email to student.
        
        Args:
            student_name: Name of the student
            student_email: Email address of student
            report_path: Path to PDF report
            grade: Final grade
            percentage: Percentage score
            
        Returns:
            True if sent successfully
        """
        subject = f"Your Test Assessment Report - Grade: {grade}"
        
        body = f"""
        <html>
        <body>
            <h2>Dear {student_name},</h2>
            <p>Your test has been assessed. Here are your results:</p>
            <ul>
                <li><strong>Grade:</strong> {grade}</li>
                <li><strong>Score:</strong> {percentage:.2f}%</li>
            </ul>
            <p>Please find your detailed assessment report attached.</p>
            <p>Keep up the good work!</p>
            <br>
            <p>Best regards,<br>Agentic AI Assessment System</p>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=student_email,
            subject=subject,
            body=body,
            attachments=[report_path]
        )
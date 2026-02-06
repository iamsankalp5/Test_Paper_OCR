"""
Workflow Manager - Orchestrates complete autonomous workflows.
Multi-agent collaboration coordinator.
"""
import os
from typing import Dict, Any, Optional
from fastapi import UploadFile
from app.config.logging_config import get_logger
from app.core.agent_controller import AgentController, AgentType
from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.services.reference_service import ReferenceService
from app.services.multipage_processor import MultiPageProcessor
from app.core.utils import generate_job_id
from app.models.enums import WorkflowState
from app.core.utils import get_grade_from_percentage
from datetime import datetime, timezone


logger = get_logger(__name__)


class WorkflowManager:
    """
    Central workflow orchestrator implementing multi-agent collaboration.
    Coordinates autonomous end-to-end test paper processing.
    """
    
    def __init__(self):
        """Initialize workflow manager with agent controller."""
        self.agent_controller = AgentController()
        self.db = None
        self.storage = None
        logger.info("WorkflowManager initialized")
    
    async def execute_autonomous_pipeline(
        self,
        file: UploadFile,
        student_name: str,
        student_id: str,
        reference_id: Optional[str] = None,
        exam_name: Optional[str] = None,
        subject: Optional[str] = None,
        total_marks: int = 100
    ) -> Dict[str, Any]:
        """
        Execute complete autonomous workflow with multi-agent collaboration.
        
        This is the main agentic AI pipeline where specialized agents work together
        to process a test paper from upload to final report generation.
        
        Args:
            file: Uploaded test paper file
            student_name: Student's name
            student_id: Student's ID
            reference_id: Optional reference answer key ID
            exam_name: Exam name
            subject: Subject name
            total_marks: Total marks for the test
            
        Returns:
            Complete workflow result with all agent outputs
        """
        logger.info(f"Starting autonomous workflow for {student_name}")
        
        # Initialize services
        self.db = DatabaseService()
        await self.db.connect()
        self.storage = StorageService()
        
        # Generate job ID
        job_id = generate_job_id()
        
        workflow_result = {
            "job_id": job_id,
            "student_name": student_name,
            "stages": {}
        }
        
        try:
            # ============================================================
            # STAGE 1: UPLOAD & PREPROCESSING
            # ============================================================
            logger.info("Stage 1: Upload & Preprocessing")
            
            # Save uploaded file
            original_path, file_size = await self.storage.save_uploaded_file(
                file, job_id, "original"
            )
            
            # Create job in database
            job_data = {
                "job_id": job_id,
                "student_name": student_name,
                "student_id": student_id,
                "exam_name": exam_name or "Unknown Exam",
                "subject": subject or "Unknown Subject",
                "total_marks": total_marks,
                "reference_id": reference_id,
                "original_image_path": original_path,
                "processed_image_path": self.storage.get_file_path(job_id, "processed", ".jpg"),
                "state": WorkflowState.UPLOADED.value,
                "current_step": "uploaded",
                "progress_percentage": 10,
                "metadata": {
                    "original_filename": file.filename,
                    "file_size": file_size
                }
            }
            
            await self.db.create_job(job_data)
            
            # Handle PDF multi-page processing
            is_pdf = original_path.lower().endswith('.pdf')
            if is_pdf:
                logger.info("Detected multi-page PDF")
                # Try with Tesseract first (faster)
                processor = MultiPageProcessor(use_trocr=False)
                pages_dir = os.path.join('uploads', f'{job_id}_pages')
                page_paths = processor.split_pdf_to_pages(original_path, pages_dir)
                
                # Preprocess all pages
                processed_pages = []
                for page_path in page_paths:
                    processed_path = page_path.replace('.jpg', '_processed.jpg')
                    from app.core.image_preprocessor import ImagePreprocessor
                    preprocessor = ImagePreprocessor()
                    preprocessor.preprocess(page_path, processed_path)
                    processed_pages.append(processed_path)
                
                workflow_result['stages']['preprocessing'] = {
                    "status": "success",
                    "total_pages": len(page_paths),
                    "processed_pages": processed_pages
                }
                
                image_path_for_ocr = processed_pages  # List of pages
            else:
                # Single image preprocessing
                from app.core.image_preprocessor import ImagePreprocessor
                preprocessor = ImagePreprocessor()
                preprocessor.preprocess(original_path, job_data['processed_image_path'])
                
                workflow_result['stages']['preprocessing'] = {
                    "status": "success",
                    "total_pages": 1
                }
                
                image_path_for_ocr = job_data['processed_image_path']
            
            # Update progress
            await self.db.update_job(job_id, {
                "state": WorkflowState.PREPROCESSING.value,
                "current_step": "preprocessing",
                "progress_percentage": 20
            })
            
            # ============================================================
            # STAGE 2: VISION AGENT - OCR EXTRACTION
            # ============================================================
            logger.info("Stage 2: Vision Agent - OCR Extraction")
            
            await self.db.update_job(job_id, {
                "state": WorkflowState.OCR_EXTRACTING.value, 
                "current_step": "ocr_extracting",
                "progress_percentage": 30
            })
            
            if isinstance(image_path_for_ocr, list):
                # Multi-page OCR
                from app.core.ocr_engine import OCREngine
                ocr_engine = OCREngine()
                all_text = []
                total_confidence = 0
                
                for i, page_path in enumerate(image_path_for_ocr, 1):
                    text, confidence, _ = ocr_engine.extract_text(page_path, use_easyocr=False, use_trocr=False)
                    all_text.append(text)
                    total_confidence += confidence
                
                extracted_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
                avg_confidence = total_confidence / len(image_path_for_ocr)

                # If confidence is low, retry with TrOCR for handwritten text
                if avg_confidence < 80:
                    logger.warning(f"Low OCR confidence ({avg_confidence:.1f}%), retrying with TrOCR for handwriting...")
                    
                    try:
                        from app.core.trocr_engine import TrOCREngine
                        trocr_engine = TrOCREngine()
                        
                        all_text = []
                        total_confidence = 0
                        
                        for i, page_path in enumerate(image_path_for_ocr, 1):
                            logger.info(f"TrOCR processing page {i}/{len(image_path_for_ocr)}...")
                            text, confidence, _ = trocr_engine.extract_text(page_path)
                            all_text.append(text)
                            total_confidence += confidence
                            logger.debug(f"Page {i}: {confidence:.1f}% confidence")
                        
                        extracted_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
                        avg_confidence = total_confidence / len(image_path_for_ocr)
                        
                        logger.info(f"TrOCR completed with improved confidence: {avg_confidence:.1f}%")
                        
                    except Exception as e:
                        logger.error(f"TrOCR retry failed: {str(e)}")
                        logger.info("Continuing with original Tesseract results...")
                        # Keep the original Tesseract results

            else:
                logger.info("Processing single page...")
                from app.core.ocr_engine import OCREngine
                ocr_engine = OCREngine()
                
                # Try Tesseract first
                extracted_text, avg_confidence, _ = ocr_engine.extract_text(
                    image_path_for_ocr, 
                    use_easyocr=False, 
                    use_trocr=False
                )
                
                logger.info(f"Initial OCR completed with confidence: {avg_confidence:.1f}%")
                
                # Retry with TrOCR if confidence is low
                if avg_confidence < 80:
                    logger.warning(f"Low OCR confidence ({avg_confidence:.1f}%), retrying with TrOCR...")
                    try:
                        from app.core.trocr_engine import TrOCREngine
                        trocr_engine = TrOCREngine()
                        
                        extracted_text, avg_confidence, _ = trocr_engine.extract_text(image_path_for_ocr)
                        logger.info(f"TrOCR completed with improved confidence: {avg_confidence:.1f}%")
                        
                    except Exception as e:
                        logger.error(f"TrOCR retry failed: {str(e)}")
                        logger.info("Continuing with original Tesseract results...")
            
            workflow_result['stages']['ocr'] = {
                "status": "success",
                "confidence": avg_confidence,
                "text_length": len(extracted_text),
                "engine": "TrOCR" if avg_confidence < 80 else "Tesseract"
            }
            
            # ============================================================
            # STAGE 3: PARSER AGENT - STRUCTURE ANSWERS
            # ============================================================
            logger.info("Stage 3: Parser Agent - Answer Structuring")
            
            await self.db.update_job(job_id, {
                "state": WorkflowState.PARSING.value,
                "current_step": "parsing",
                "progress_percentage": 50
            })
            
            parse_result = await self.agent_controller.execute_agent(
                AgentType.PARSER,
                {
                    "extracted_text": extracted_text,
                    "total_marks": total_marks
                }
            )
            
            parsed_answers = parse_result['parsed_answers']
            
            workflow_result['stages']['parsing'] = {
                "status": "success",
                "total_questions": len(parsed_answers)
            }
            
            # ============================================================
            # STAGE 4: ASSESSMENT AGENT - AI GRADING (GEMINI)
            # ============================================================
            logger.info("Stage 4: Assessment Agent - AI Grading with Gemini")
            
            await self.db.update_job(job_id, {
                "state": WorkflowState.ASSESSING.value,
                "current_step": "assessing",
                "progress_percentage": 65
            })
            
            # Get reference answers if available
            answer_key = None
            if reference_id:
                ref_service = ReferenceService(self.db)
                reference = await ref_service.get_reference(reference_id)
                if reference and reference.get('parsed_answers'):
                    answer_key = {
                        ans['question_number']: ans['answer_text']
                        for ans in reference['parsed_answers']
                    }
                    logger.info(f"Using reference answers from: {reference_id}")
            
            assessment_result = await self.agent_controller.execute_agent(
                AgentType.ASSESSMENT,
                {
                    "parsed_answers": parsed_answers,
                    "answer_key": answer_key
                }
            )
            
            assessed_answers = assessment_result['assessed_answers']
            percentage = assessment_result['percentage']
            
            workflow_result['stages']['assessment'] = {
                "status": "success",
                "total_marks_obtained": assessment_result['total_marks_obtained'],
                "total_marks": assessment_result['total_marks'],
                "percentage": percentage
            }
            
            # Update to ASSESSED state
            await self.db.update_job(job_id, {
                "state": WorkflowState.ASSESSED.value,
                "current_step": "assessed",
                "progress_percentage": 75
            })
            
            # ============================================================
            # STAGE 5: FEEDBACK AGENT - PERSONALIZED FEEDBACK (GEMINI)
            # ============================================================
            logger.info("Stage 5: Feedback Agent - Generating Personalized Feedback")
            
            await self.db.update_job(job_id, {
                "state": WorkflowState.GENERATING_FEEDBACK.value,
                "current_step": "generating_feedback",
                "progress_percentage": 80
            })
            
            try:
                feedback_result = await self.agent_controller.execute_agent(
                    AgentType.FEEDBACK,
                    {
                        "student_name": student_name,
                        "assessed_answers": assessed_answers,
                        "percentage": percentage,
                        "subject": subject
                    }
                )
                
                workflow_result['stages']['feedback'] = {
                    "status": "success",
                    "grade": feedback_result['feedback']['grade']
                }
            except Exception as e:
                logger.error(f"Feedback generation failed: {str(e)}")
                
                # Create fallback feedback
                grade = "B" if percentage >= 80 else "C" if percentage >= 70 else "D"
                feedback_result = {
                    "feedback": {
                        "grade": grade,
                        "overall_feedback": f"Score: {percentage}%. Good work!",
                        "strengths": ["Completed assessment"],
                        "areas_for_improvement": ["Review incorrect answers"],
                        "suggestions": ["Keep practicing"]
                    }
                }
                
                workflow_result['stages']['feedback'] = {
                    "status": "fallback",
                    "grade": grade,
                    "error": str(e)
                }
            
            # Calculate grade
            grade = get_grade_from_percentage(percentage)
            
            # **CRITICAL: Update to FEEDBACK_GENERATED state**
            await self.db.update_job(job_id, {
                "state": WorkflowState.FEEDBACK_GENERATED.value,
                "current_step": "feedback_generated",
                "progress_percentage": 90,
                "extracted_text": extracted_text,
                "parsed_answers": parsed_answers,
                "assessed_answers": assessed_answers,
                "feedback": feedback_result['feedback'],
                "total_marks_obtained": assessment_result['total_marks_obtained'],
                "percentage": percentage,
                "grade": grade,
                "ocr_confidence": avg_confidence
            })
            
            # ============================================================
            # STAGE 6: REPORT AGENT - PDF GENERATION
            # ============================================================
            logger.info("Stage 6: Report Agent - Generating PDF Report")
            
            await self.db.update_job(job_id, {
                "state": WorkflowState.REPORT_GENERATING.value,
                "current_step": "report_generating",
                "progress_percentage": 95
            })
            
            # Get updated job data
            job_data_full = await self.db.get_job(job_id)
            
            report_path = self.storage.get_file_path(job_id, "report", ".pdf")
            
            report_result = await self.agent_controller.execute_agent(
                AgentType.REPORT,
                {
                    "job_data": job_data_full,
                    "output_path": report_path,
                    "format": "pdf"
                }
            )
            
            workflow_result['stages']['report'] = {
                "status": "success",
                "report_path": report_path
            }
            
            # **CRITICAL: Update to COMPLETED with report_path**
            await self.db.update_job(job_id, {
                "state": WorkflowState.COMPLETED.value,
                "current_step": "completed",
                "progress_percentage": 100,
                "report_path": report_path
            })
            
            # ============================================================
            # WORKFLOW COMPLETE
            # ============================================================
            
            # Get execution summary from agent controller
            execution_summary = self.agent_controller.get_execution_summary()
            
            workflow_result['execution_summary'] = execution_summary
            workflow_result['status'] = 'success'
            workflow_result['final_score'] = f"{percentage}%"
            workflow_result['grade'] = feedback_result['feedback']['grade']
            workflow_result['report_download_url'] = f"/api/v1/report/download/{job_id}"
            
            logger.info(f"Autonomous workflow completed successfully: {job_id}")
            logger.info(f"Final Score: {percentage}% | Grade: {feedback_result['feedback']['grade']}")
            logger.info(f"Total execution time: {execution_summary['total_execution_time']}s")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Autonomous workflow failed: {str(e)}", exc_info=True)
            
            # Update job status to FAILED
            if self.db:
                await self.db.update_job(job_id, {
                    "state": WorkflowState.FAILED.value,
                    "current_step": "failed",
                    "error_message": str(e)
                })
            
            raise Exception(f"Workflow execution failed: {str(e)}")
        
        finally:
            if self.db:
                await self.db.disconnect()

    async def reprocess_existing_file(
        self,
        original_job_id: str,
        file_path: str,
        student_name: str,
        student_id: str,
        exam_name: str,
        subject: str,
        total_marks: int = 100,
        reference_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reprocess an existing uploaded file without re-uploading.
        
        Args:
            original_job_id: Original job ID (for reference)
            file_path: Path to existing file on server
            student_name: Student name
            student_id: Student ID
            exam_name: Exam name
            subject: Subject
            total_marks: Total marks
            reference_id: Optional reference answer key
            
        Returns:
            New job data
        """
        import uuid
        from datetime import datetime
        
        logger.info(f"Reprocessing file from job: {original_job_id}")
        
        # Initialize services
        self.db = DatabaseService()
        await self.db.connect()
        self.storage = StorageService()
        
        # Generate new job ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_job_id = f"job_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        workflow_result = {
            "job_id": new_job_id,
            "student_name": student_name,
            "stages": {}
        }
        
        try:
            # ============================================================
            # Create new job pointing to existing file
            # ============================================================
            job_data = {
                "job_id": new_job_id,
                "original_job_id": original_job_id,
                "student_name": student_name,
                "student_id": student_id,
                "exam_name": exam_name,
                "subject": subject,
                "total_marks": total_marks,
                "reference_id": reference_id,
                "original_image_path": file_path,  # Reuse existing file
                "processed_image_path": self.storage.get_file_path(new_job_id, "processed", ".jpg"),
                "state": WorkflowState.UPLOADED.value,
                "current_step": "uploaded",
                "progress_percentage": 10,
                "is_reprocess": True,
                "metadata": {
                    "original_job_id": original_job_id,
                    "reprocessed_at": datetime.utcnow().isoformat()
                },
                "created_at": datetime.now(timezone.utc), 
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.create_job(job_data)
            logger.info(f"Created reprocess job: {new_job_id}")
            
            # ============================================================
            # STAGE 1: PREPROCESSING (reuse existing file)
            # ============================================================
            logger.info("Stage 1: Preprocessing existing file")
            
            # Handle PDF multi-page processing
            is_pdf = file_path.lower().endswith('.pdf')
            if is_pdf:
                logger.info("Detected multi-page PDF")
                processor = MultiPageProcessor()
                pages_dir = os.path.join('uploads', f'{new_job_id}_pages')
                page_paths = processor.split_pdf_to_pages(file_path, pages_dir)
                
                # Preprocess all pages
                processed_pages = []
                for page_path in page_paths:
                    processed_path = page_path.replace('.jpg', '_processed.jpg')
                    from app.core.image_preprocessor import ImagePreprocessor
                    preprocessor = ImagePreprocessor()
                    preprocessor.preprocess(page_path, processed_path)
                    processed_pages.append(processed_path)
                
                workflow_result['stages']['preprocessing'] = {
                    "status": "success",
                    "total_pages": len(page_paths),
                    "processed_pages": processed_pages
                }
                
                image_path_for_ocr = processed_pages
            else:
                # Single image preprocessing
                from app.core.image_preprocessor import ImagePreprocessor
                preprocessor = ImagePreprocessor()
                preprocessor.preprocess(file_path, job_data['processed_image_path'])
                
                workflow_result['stages']['preprocessing'] = {
                    "status": "success",
                    "total_pages": 1
                }
                
                image_path_for_ocr = job_data['processed_image_path']
            
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.PREPROCESSING.value,
                "current_step": "preprocessing",
                "progress_percentage": 20
            })
            
            # ============================================================
            # STAGE 2-6: Continue with rest of pipeline
            # (Copy from execute_autonomous_pipeline, starting from OCR)
            # ============================================================
            
            # STAGE 2: OCR
            logger.info("Stage 2: Vision Agent - OCR Extraction")
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.OCR_EXTRACTING.value,
                "current_step": "ocr_extracting",
                "progress_percentage": 30
            })
            
            if isinstance(image_path_for_ocr, list):
                from app.core.ocr_engine import OCREngine
                ocr_engine = OCREngine()
                all_text = []
                total_confidence = 0
                
                for page_path in image_path_for_ocr:
                    text, confidence, _ = ocr_engine.extract_text(page_path)
                    all_text.append(text)
                    total_confidence += confidence
                
                extracted_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
                avg_confidence = total_confidence / len(image_path_for_ocr)
            else:
                ocr_result = await self.agent_controller.execute_agent(
                    AgentType.VISION,
                    {"image_path": image_path_for_ocr}
                )
                extracted_text = ocr_result['extracted_text']
                avg_confidence = ocr_result['confidence']
            
            workflow_result['stages']['ocr'] = {
                "status": "success",
                "confidence": avg_confidence,
                "text_length": len(extracted_text)
            }
            
            # STAGE 3: PARSING
            logger.info("Stage 3: Parser Agent")
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.PARSING.value,
                "current_step": "parsing",
                "progress_percentage": 50
            })
            
            parse_result = await self.agent_controller.execute_agent(
                AgentType.PARSER,
                {
                    "extracted_text": extracted_text,
                    "total_marks": total_marks
                }
            )
            
            parsed_answers = parse_result['parsed_answers']
            workflow_result['stages']['parsing'] = {
                "status": "success",
                "total_questions": len(parsed_answers)
            }
            
            # STAGE 4: ASSESSMENT
            logger.info("Stage 4: Assessment Agent")
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.ASSESSING.value,
                "current_step": "assessing",
                "progress_percentage": 65
            })
            
            # Get reference answers if available
            answer_key = None
            if reference_id:
                ref_service = ReferenceService(self.db)
                reference = await ref_service.get_reference(reference_id)
                if reference and reference.get('reference_answers'):
                    answer_key = {
                        ans['question_number']: ans['answer_text']
                        for ans in reference['reference_answers']
                    }
            
            assessment_result = await self.agent_controller.execute_agent(
                AgentType.ASSESSMENT,
                {
                    "parsed_answers": parsed_answers,
                    "answer_key": answer_key
                }
            )
            
            assessed_answers = assessment_result['assessed_answers']
            percentage = assessment_result['percentage']
            
            workflow_result['stages']['assessment'] = {
                "status": "success",
                "total_marks_obtained": assessment_result['total_marks_obtained'],
                "total_marks": assessment_result['total_marks'],
                "percentage": percentage
            }
            
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.ASSESSED.value,
                "current_step": "assessed",
                "progress_percentage": 75
            })
            
            # STAGE 5: FEEDBACK
            logger.info("Stage 5: Feedback Agent")
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.GENERATING_FEEDBACK.value,
                "current_step": "generating_feedback",
                "progress_percentage": 80
            })
            
            try:
                feedback_result = await self.agent_controller.execute_agent(
                    AgentType.FEEDBACK,
                    {
                        "student_name": student_name,
                        "assessed_answers": assessed_answers,
                        "percentage": percentage,
                        "subject": subject
                    }
                )
            except Exception as e:
                logger.error(f"Feedback generation failed: {str(e)}")
                grade = "B" if percentage >= 80 else "C" if percentage >= 70 else "D"
                feedback_result = {
                    "feedback": {
                        "grade": grade,
                        "overall_feedback": f"Score: {percentage}%. Good work!",
                        "strengths": ["Completed assessment"],
                        "areas_for_improvement": ["Review incorrect answers"],
                        "suggestions": ["Keep practicing"]
                    }
                }
            
            grade = get_grade_from_percentage(percentage)
            
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.FEEDBACK_GENERATED.value,
                "current_step": "feedback_generated",
                "progress_percentage": 90,
                "extracted_text": extracted_text,
                "parsed_answers": parsed_answers,
                "assessed_answers": assessed_answers,
                "feedback": feedback_result['feedback'],
                "total_marks_obtained": assessment_result['total_marks_obtained'],
                "percentage": percentage,
                "grade": grade,
                "ocr_confidence": avg_confidence
            })
            
            # STAGE 6: REPORT
            logger.info("Stage 6: Report Generation")
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.REPORT_GENERATING.value,
                "current_step": "report_generating",
                "progress_percentage": 95
            })
            
            job_data_full = await self.db.get_job(new_job_id)
            report_path = self.storage.get_file_path(new_job_id, "report", ".pdf")
            
            report_result = await self.agent_controller.execute_agent(
                AgentType.REPORT,
                {
                    "job_data": job_data_full,
                    "output_path": report_path,
                    "format": "pdf"
                }
            )
            
            workflow_result['stages']['report'] = {
                "status": "success",
                "report_path": report_path
            }
            
            await self.db.update_job(new_job_id, {
                "state": WorkflowState.COMPLETED.value,
                "current_step": "completed",
                "progress_percentage": 100,
                "report_path": report_path
            })
            
            workflow_result['status'] = 'success'
            workflow_result['final_score'] = f"{percentage}%"
            workflow_result['grade'] = grade
            
            logger.info(f"Reprocessing completed successfully: {new_job_id}")
            
            return {"job_id": new_job_id, **workflow_result}
            
        except Exception as e:
            logger.error(f"Reprocessing failed: {str(e)}", exc_info=True)
            
            if self.db:
                await self.db.update_job(new_job_id, {
                    "state": WorkflowState.FAILED.value,
                    "current_step": "failed",
                    "error_message": str(e)
                })
            
            raise Exception(f"Reprocessing failed: {str(e)}")
        
        finally:
            if self.db:
                await self.db.disconnect()

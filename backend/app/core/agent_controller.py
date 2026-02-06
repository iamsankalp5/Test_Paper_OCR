"""
Agent Controller - Orchestrates multiple specialized AI agents.
"""
from typing import Dict, Any, Optional
from enum import Enum
from app.config.logging_config import get_logger
from app.core.image_preprocessor import ImagePreprocessor
from app.core.ocr_engine import OCREngine
from app.core.answer_parser import AnswerParser
from app.core.assessment_engine import AssessmentEngine
from app.core.feedback_generator import FeedbackGenerator
from app.core.report_generator import ReportGenerator

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Types of specialized agents in the system."""
    VISION = "vision_agent"
    PARSER = "parser_agent"
    ASSESSMENT = "assessment_agent"
    FEEDBACK = "feedback_agent"
    REPORT = "report_agent"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Agent:
    """Base agent class with common functionality."""
    
    def __init__(self, agent_type: AgentType, name: str):
        self.agent_type = agent_type
        self.name = name
        self.status = AgentStatus.IDLE
        self.result = None
        self.error = None
        self.execution_time = 0


class AgentController:
    """
    Central controller that orchestrates multiple AI agents.
    """
    
    def __init__(self):
        """Initialize agent controller with all specialized agents."""
        self.agents: Dict[AgentType, Agent] = {}
        self.execution_log = []
        logger.info("AgentController initialized")
        
        # Initialize all agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Create and register all specialized agents."""
        agent_configs = [
            (AgentType.VISION, "Vision Agent (OCR)"),
            (AgentType.PARSER, "Parser Agent (NLP)"),
            (AgentType.ASSESSMENT, "Assessment Agent (Gemini AI)"),
            (AgentType.FEEDBACK, "Feedback Agent (Gemini AI)"),
            (AgentType.REPORT, "Report Generator Agent"),
        ]
        
        for agent_type, name in agent_configs:
            agent = Agent(agent_type, name)
            self.agents[agent_type] = agent
    
    async def execute_agent(
        self,
        agent_type: AgentType,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific agent with given task data.
        """
        import time
        import inspect
        
        agent = self.agents[agent_type]
        agent.status = AgentStatus.RUNNING
        start_time = time.time()
        
        logger.info(f"Executing: {agent.name}")
        
        try:
            # Get the executor method based on agent type
            executor_map = {
                AgentType.VISION: self._execute_vision_agent,
                AgentType.PARSER: self._execute_parser_agent,
                AgentType.ASSESSMENT: self._execute_assessment_agent,
                AgentType.FEEDBACK: self._execute_feedback_agent,
                AgentType.REPORT: self._execute_report_agent
            }
            
            executor = executor_map.get(agent_type)
            
            if executor is None:
                raise ValueError(f"No executor found for agent type: {agent_type}")
            
            # Verify it's callable
            if not callable(executor):
                raise TypeError(f"Executor is not callable: {type(executor)}")
            
            # Execute with automatic async detection
            if inspect.iscoroutinefunction(executor):
                result = await executor(task_data)
            else:
                result = executor(task_data)
            
            agent.status = AgentStatus.SUCCESS
            agent.result = result
            agent.execution_time = time.time() - start_time
            
            logger.info(f"{agent.name} completed in {agent.execution_time:.2f}s")
            
            # Log execution
            self.execution_log.append({
                "agent": agent.name,
                "status": "success",
                "execution_time": agent.execution_time,
                "result_summary": self._summarize_result(result)
            })
            
            return result
            
        except Exception as e:
            agent.status = AgentStatus.FAILED
            agent.error = str(e)
            agent.execution_time = time.time() - start_time
            
            logger.error(f"{agent.name} failed: {str(e)}", exc_info=True)
            
            # Log failure
            self.execution_log.append({
                "agent": agent.name,
                "status": "failed",
                "execution_time": agent.execution_time,
                "error": str(e)
            })
            
            raise
    
    def _execute_vision_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OCR extraction agent."""
        image_path = task_data.get('image_path')
        use_easyocr = task_data.get('use_easyocr', False)
        use_trocr = task_data.get('use_trocr', False) # NEW: TrOCR option
        
        if not image_path:
            raise ValueError("No image_path provided for vision agent")
        
        ocr_engine = OCREngine()
        text, confidence, details = ocr_engine.extract_text(image_path, use_easyocr, use_trocr=use_trocr)
        
        # NEW: Auto-retry with TrOCR if confidence is low
        if confidence < 80 and not use_trocr:
            logger.info("Low confidence detected, retrying with TrOCR for handwriting...")
            text, confidence, details = ocr_engine.extract_text(
                image_path,
                use_trocr=True
            )
            logger.info(f"TrOCR retry completed with confidence: {confidence}%")
            
        return {
            "extracted_text": text,
            "confidence": confidence,
            "details": details,
            "agent": str(AgentType.VISION)
        }
    
    def _execute_parser_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute answer parsing agent."""
        text = task_data.get('extracted_text')
        total_marks = task_data.get('total_marks', 100)
        
        if not text:
            raise ValueError("No extracted_text provided for parser agent")
        
        parser = AnswerParser()
        answers = parser.parse(text, total_marks)
        
        return {
            "parsed_answers": answers,
            "total_questions": len(answers),
            "agent": str(AgentType.PARSER)
        }
    
    async def _execute_assessment_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI assessment agent."""
        answers = task_data.get('parsed_answers')
        answer_key = task_data.get('answer_key')
        
        if not answers:
            raise ValueError("No parsed_answers provided for assessment agent")
        
        assessment_engine = AssessmentEngine()
        assessed_answers = await assessment_engine.assess_answers(answers, answer_key)
        
        # Calculate totals
        total_marks_obtained = sum(a['marks_obtained'] for a in assessed_answers)
        total_marks = sum(a['max_marks'] for a in assessed_answers)
        percentage = (total_marks_obtained / total_marks * 100) if total_marks > 0 else 0
        
        return {
            "assessed_answers": assessed_answers,
            "total_marks_obtained": total_marks_obtained,
            "total_marks": total_marks,
            "percentage": round(percentage, 2),
            "agent": str(AgentType.ASSESSMENT)
        }
    
    async def _execute_feedback_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute feedback generation agent."""
        student_name = task_data.get('student_name')
        assessed_answers = task_data.get('assessed_answers')
        percentage = task_data.get('percentage')
        subject = task_data.get('subject', 'General')
        
        if not assessed_answers:
            raise ValueError("No assessed_answers provided for feedback agent")
        
        feedback_gen = FeedbackGenerator()
        feedback = await feedback_gen.generate_feedback(
            student_name=student_name,
            assessed_answers=assessed_answers,
            percentage=percentage,
            subject=subject
        )
        
        return {
            "feedback": feedback,
            "agent": str(AgentType.FEEDBACK)
        }
    
    def _execute_report_agent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation agent."""
        job_data = task_data.get('job_data')
        output_path = task_data.get('output_path')
        
        if not job_data:
            raise ValueError("No job_data provided for report agent")
        
        if not output_path:
            raise ValueError("No output_path provided for report agent")
        
        report_gen = ReportGenerator()
        report_path = report_gen.generate_pdf_report(  # CORRECT METHOD NAME
            job_data=job_data,
            output_path=output_path
        )
        
        return {
            "report_path": report_path,
            "agent": str(AgentType.REPORT)
        }
    
    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create a brief summary of agent result."""
        if "confidence" in result:
            return f"OCR confidence: {result['confidence']}%"
        elif "total_questions" in result:
            return f"Parsed {result['total_questions']} questions"
        elif "percentage" in result:
            return f"Score: {result['percentage']}%"
        elif "feedback" in result:
            return "Generated feedback"
        elif "report_path" in result:
            return "Report generated"
        return "Completed"
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all agent executions."""
        total_time = sum(log['execution_time'] for log in self.execution_log)
        successful = sum(1 for log in self.execution_log if log['status'] == 'success')
        failed = sum(1 for log in self.execution_log if log['status'] == 'failed')
        
        return {
            "total_agents": len(self.execution_log),
            "successful": successful,
            "failed": failed,
            "total_execution_time": round(total_time, 2),
            "execution_log": self.execution_log
        }